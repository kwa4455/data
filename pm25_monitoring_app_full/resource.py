import json
import math
import time
from datetime import datetime

import gspread
import numpy as np
import pandas as pd
import streamlit as st
from gspread.exceptions import APIError, WorksheetNotFound
from oauth2client.service_account import ServiceAccountCredentials

from constants import SPREADSHEET_ID, MAIN_SHEET, MERGED_SHEET, CALC_SHEET


# =========================================================
# GOOGLE SHEETS SETUP
# =========================================================
creds_json = st.secrets["GOOGLE_CREDENTIALS"]
creds_dict = json.loads(creds_json)

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SPREADSHEET_ID)


# =========================================================
# SHEET INITIALIZATION
# =========================================================
def ensure_main_sheet_initialized(spreadsheet, sheet_name):
    expected_header = [
        "Entry Type",
        "ID",
        "Site",
        "Latitude",
        "Longitude",
        "Monitoring Officer",
        "Driver",
        "Date",
        "Time",
        "Temperature (°C)",
        "RH (%)",
        "Pressure (mbar)",
        "Weather",
        "Wind Speed",
        "Wind Direction",
        "Elapsed Time (min)",
        "Flow Rate (L/min)",
        "Observation",
        "Submitted By",
        "Submitted At",
    ]

    try:
        ws = spreadsheet.worksheet(sheet_name)
    except WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")

    all_values = ws.get_all_values()

    if not all_values:
        ws.append_row(expected_header)
    else:
        current_header = all_values[0]
        if current_header != expected_header:
            ws.clear()
            ws.append_row(expected_header)

    return ws


sheet = ensure_main_sheet_initialized(spreadsheet, MAIN_SHEET)


# =========================================================
# GENERAL UTILITIES
# =========================================================
def convert_timestamps_to_string(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns:
        df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df


def make_unique_headers(headers):
    seen = {}
    unique_headers = []

    for h in headers:
        if h == "":
            h = "Unnamed"

        if h in seen:
            seen[h] += 1
            unique_headers.append(f"{h}.{seen[h]}")
        else:
            seen[h] = 0
            unique_headers.append(h)

    return unique_headers


def load_data_from_sheet(sheet):
    try:
        all_values = sheet.get_all_values()
        if not all_values:
            return pd.DataFrame()

        headers = make_unique_headers(all_values[0])
        rows = all_values[1:]

        if not rows:
            return pd.DataFrame(columns=headers)

        df = pd.DataFrame(rows, columns=headers)
        return convert_timestamps_to_string(df)

    except APIError as e:
        st.error(f"❌ APIError: {e.response.status_code} - {e.response.reason}")
        try:
            st.text(f"Details: {e.response.text}")
        except Exception:
            pass
        return pd.DataFrame()

    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
        return pd.DataFrame()


def add_data(row, username):
    row.append(username)
    row.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    sheet.append_row(row)


# =========================================================
# FILTERING / VALIDATION
# =========================================================
def filter_by_site_and_date(df, site_col="Site", date_col="Submitted At", context_label=""):
    df = df.copy()

    if site_col not in df.columns or date_col not in df.columns:
        st.warning("Required filter columns are missing.")
        return df

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    st.markdown(f"### 🔍 Filter Records {context_label}")
    sites = ["All"] + sorted(df[site_col].dropna().astype(str).unique().tolist())

    selected_site = st.selectbox(
        f"Filter by Site {context_label}:",
        sites,
        key=f"{context_label}_site",
    )

    valid_dates = df[date_col].dropna()
    if valid_dates.empty:
        st.warning("No valid dates found for filtering.")
        return df.iloc[0:0]

    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()

    selected_date = st.date_input(
        f"Filter by Date {context_label}:",
        value=min_date,
        min_value=min_date,
        max_value=max_date,
        key=f"{context_label}_date",
    )

    filtered_df = df.copy()

    if selected_site != "All":
        filtered_df = filtered_df[filtered_df[site_col].astype(str) == selected_site]

    filtered_df = filtered_df[filtered_df[date_col].dt.date == selected_date]
    return filtered_df


def filter_dataframe(df, site_filter=None, date_range=None):
    if df.empty:
        return df

    df = df.copy()

    if "Submitted At" in df.columns:
        df["Submitted At"] = pd.to_datetime(df["Submitted At"], errors="coerce")

    if site_filter and site_filter != "All" and "Site" in df.columns:
        df = df[df["Site"] == site_filter]

    if date_range and len(date_range) == 2 and "Submitted At" in df.columns:
        start, end = date_range
        df = df[
            (df["Submitted At"].dt.date >= start) &
            (df["Submitted At"].dt.date <= end)
        ]

    return df


def validate_inputs(temp, rh, pressure, wind_speed):
    try:
        temp = float(temp)
        rh = float(rh)
        pressure = float(pressure)
        wind_speed = float(wind_speed)
    except (TypeError, ValueError):
        st.error("❗ Temperature, RH, Pressure, and Wind Speed must all be numeric.")
        return False

    if not (-40 <= temp <= 60):
        st.error("❗ Temperature must be between -40°C and 60°C")
        return False

    if not (0 <= rh <= 100):
        st.error("❗ Relative Humidity must be between 0% and 100%")
        return False

    if not (800 <= pressure <= 1100):
        st.error("❗ Pressure must be between 800 mbar and 1100 mbar")
        return False

    if wind_speed <= 0:
        st.error("❗ Wind Speed must be a positive number")
        return False

    return True


# =========================================================
# DELETE / RESTORE UTILITIES
# =========================================================
def backup_deleted_row(row_data, original_sheet_name, row_number, deleted_by):
    try:
        backup_sheet = spreadsheet.worksheet("Deleted Records")
    except Exception:
        num_columns = len(row_data) + 3
        backup_sheet = spreadsheet.add_worksheet(
            title="Deleted Records",
            rows="1000",
            cols=str(num_columns),
        )

        header = [
            "Entry Type",
            "ID",
            "Site",
            "Latitude",
            "Longitude",
            "Monitoring Officer",
            "Driver",
            "Date",
            "Time",
            "Temperature (°C)",
            "RH (%)",
            "Pressure (mbar)",
            "Weather",
            "Wind Speed",
            "Wind Direction",
            "Elapsed Time (min)",
            "Flow Rate (L/min)",
            "Observation",
            "Submitted By",
            "Submitted At",
            "Deleted At",
            "Source",
            "Deleted By",
        ]
        backup_sheet.append_row(header)

    deleted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source = f"{original_sheet_name} - Row {row_number}"
    backup_sheet.append_row(row_data + [deleted_at, source, deleted_by])


def delete_row(sheet, row_number, deleted_by):
    row_data = sheet.row_values(row_number)
    backup_deleted_row(row_data, "Main Sheet", row_number, deleted_by)
    sheet.delete_rows(row_number)


def delete_merged_record_by_index(index_to_delete, deleted_by):
    worksheet = spreadsheet.worksheet(MERGED_SHEET)
    row_data = worksheet.row_values(index_to_delete + 2)  # skip header row
    backup_deleted_row(row_data, "Merged Sheet", index_to_delete + 2, deleted_by)
    worksheet.delete_rows(index_to_delete + 2)


def restore_specific_deleted_record(selected_index: int):
    try:
        backup_sheet = spreadsheet.worksheet("Deleted Records")
        deleted_rows = backup_sheet.get_all_values()

        if len(deleted_rows) <= 1:
            return "❌ No deleted records to restore."

        record_rows = deleted_rows[1:]

        if not (0 <= selected_index < len(record_rows)):
            return "❌ Invalid selection."

        selected_row = record_rows[selected_index]

        # Remove Deleted At, Source, Deleted By
        restored_data = selected_row[:-3]

        sheet.append_row(restored_data)
        backup_sheet.delete_rows(selected_index + 2)

        return "✅ Selected deleted record has been restored."

    except Exception as e:
        return f"❌ Restore failed: {e}"


# =========================================================
# MERGE LOGIC
# =========================================================
def merge_start_stop(df):
    df = df.copy()
    df.columns = df.columns.str.strip()

    merge_keys = ["ID", "Site", "Latitude", "Longitude"]

    required_cols = merge_keys + ["Entry Type"]
    if any(col not in df.columns for col in required_cols):
        return pd.DataFrame()

    start_df = df[df["Entry Type"].astype(str).str.upper() == "START"].copy()
    stop_df = df[df["Entry Type"].astype(str).str.upper() == "STOP"].copy()

    if start_df.empty or stop_df.empty:
        return pd.DataFrame()

    start_df = start_df.reset_index(drop=True)
    stop_df = stop_df.reset_index(drop=True)

    start_df["seq"] = start_df.groupby(merge_keys).cumcount() + 1
    stop_df["seq"] = stop_df.groupby(merge_keys).cumcount() + 1

    start_df = start_df.rename(
        columns=lambda x: f"{x}_Start" if x not in merge_keys + ["seq"] else x
    )
    stop_df = stop_df.rename(
        columns=lambda x: f"{x}_Stop" if x not in merge_keys + ["seq"] else x
    )

    merged = pd.merge(start_df, stop_df, on=merge_keys + ["seq"], how="inner")

    if "Elapsed Time (min)_Start" in merged.columns and "Elapsed Time (min)_Stop" in merged.columns:
        merged["Elapsed Time (min)_Start"] = pd.to_numeric(
            merged["Elapsed Time (min)_Start"], errors="coerce"
        )
        merged["Elapsed Time (min)_Stop"] = pd.to_numeric(
            merged["Elapsed Time (min)_Stop"], errors="coerce"
        )
        merged["Elapsed Time Diff (min)"] = (
            merged["Elapsed Time (min)_Stop"] - merged["Elapsed Time (min)_Start"]
        )

    flow_start_col = "Flow Rate (L/min)_Start"
    flow_stop_col = "Flow Rate (L/min)_Stop"

    if flow_start_col in merged.columns and flow_stop_col in merged.columns:
        merged[flow_start_col] = pd.to_numeric(merged[flow_start_col], errors="coerce")
        merged[flow_stop_col] = pd.to_numeric(merged[flow_stop_col], errors="coerce")
        merged["Average Flow Rate (L/min)"] = (
            merged[flow_start_col] + merged[flow_stop_col]
        ) / 2

    if "seq" in merged.columns:
        merged = merged.drop(columns=["seq"])

    desired_order = [
        "ID",
        "Site",
        "Latitude",
        "Longitude",
        "Entry Type_Start",
        "Monitoring Officer_Start",
        "Driver_Start",
        "Date_Start",
        "Time_Start",
        "Temperature (°C)_Start",
        "RH (%)_Start",
        "Pressure (mbar)_Start",
        "Weather_Start",
        "Wind Speed_Start",
        "Wind Direction_Start",
        "Elapsed Time (min)_Start",
        "Flow Rate (L/min)_Start",
        "Observation_Start",
        "Submitted At_Start",
        "Entry Type_Stop",
        "Monitoring Officer_Stop",
        "Driver_Stop",
        "Date_Stop",
        "Time_Stop",
        "Temperature (°C)_Stop",
        "RH (%)_Stop",
        "Pressure (mbar)_Stop",
        "Weather_Stop",
        "Wind Speed_Stop",
        "Wind Direction_Stop",
        "Elapsed Time (min)_Stop",
        "Flow Rate (L/min)_Stop",
        "Observation_Stop",
        "Submitted At_Stop",
        "Elapsed Time Diff (min)",
        "Average Flow Rate (L/min)",
    ]

    existing_cols = [col for col in desired_order if col in merged.columns]
    return merged[existing_cols]


# =========================================================
# GOOGLE SHEETS JSON-SAFE SANITIZING
# =========================================================
def sanitize_for_google_sheets(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

    df = df.astype(object)

    def clean_cell(x):
        if x is None:
            return ""

        if isinstance(x, np.generic):
            x = x.item()

        try:
            if pd.isna(x):
                return ""
        except Exception:
            pass

        if isinstance(x, pd.Timestamp):
            return "" if pd.isna(x) else x.strftime("%Y-%m-%d %H:%M:%S")

        if isinstance(x, float):
            if math.isnan(x) or math.isinf(x):
                return ""
            return x

        if isinstance(x, (str, int, bool)):
            return x

        return str(x)

    df = df.apply(lambda col: col.map(clean_cell))
    df.columns = [str(c) for c in df.columns]
    return df


def validate_json_payload(values):
    json.dumps({"values": values}, allow_nan=False)


# =========================================================
# SAVE MERGED DATA
# =========================================================
def save_merged_data_to_sheet(df, spreadsheet, sheet_name):
    if df.empty:
        st.warning("No merged data to save.")
        return

    clean_df = sanitize_for_google_sheets(df)
    values = [clean_df.columns.tolist()] + clean_df.values.tolist()

    try:
        validate_json_payload(values)

        try:
            ws = spreadsheet.worksheet(sheet_name)
            ws.clear()
        except WorksheetNotFound:
            rows = max(len(values) + 10, 1000)
            cols = max(len(clean_df.columns) + 5, 50)
            ws = spreadsheet.add_worksheet(
                title=sheet_name,
                rows=str(rows),
                cols=str(cols),
            )

        ws.update(range_name="A1", values=values)

    except Exception as e:
        st.error(f"❌ Failed to save merged data to Google Sheets: {e}")

        # pinpoint the exact bad value if any remain
        try:
            for r, row in enumerate(values):
                for c, val in enumerate(row):
                    try:
                        json.dumps(val, allow_nan=False)
                    except Exception:
                        st.write(
                            f"Bad value at row {r + 1}, col {c + 1}: {repr(val)} | type={type(val)}"
                        )
                        return
        except Exception:
            pass

        st.write("Preview of cleaned data:")
        st.dataframe(clean_df.head(), use_container_width=True)


# =========================================================
# DISPLAY / MERGE PIPELINE
# =========================================================
def display_and_merge_data(df, spreadsheet, merged_sheet_name):
    if df.empty:
        st.info("No data submitted yet.")
        return

    if "Site" not in df.columns:
        st.warning("Column 'Site' is missing from the dataset.")
        st.dataframe(df, use_container_width=True)
        return

    with st.expander("🔍 Filter Records"):
        site_filter = st.selectbox(
            "Filter by Site",
            ["All"] + sorted(df["Site"].dropna().astype(str).unique().tolist()),
        )
        date_range = st.date_input("Filter by Date Range", [])

    filtered_df = filter_dataframe(df, site_filter, date_range)
    st.dataframe(filtered_df, use_container_width=True)

    merged_df = merge_start_stop(filtered_df)

    if not merged_df.empty:
        save_merged_data_to_sheet(merged_df, spreadsheet, merged_sheet_name)
        st.success("✅ Merged records saved to Google Sheets.")
        st.dataframe(merged_df, use_container_width=True)
    else:
        st.warning("⚠️ No matching START and STOP records found to merge.")
