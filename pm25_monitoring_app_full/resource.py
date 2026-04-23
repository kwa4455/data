
import streamlit as st
import pandas as pd
import gspread

from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import APIError,WorksheetNotFound 

import json
import time
from constants import SPREADSHEET_ID, MAIN_SHEET, MERGED_SHEET, CALC_SHEET

# === Google Sheets Setup ===
creds_json = st.secrets["GOOGLE_CREDENTIALS"]
creds_dict = json.loads(creds_json)

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

spreadsheet = client.open_by_key(SPREADSHEET_ID)


# === Ensure Observations worksheet exists and is initialized ===
def ensure_main_sheet_initialized(spreadsheet, sheet_name):
    expected_header = [
        "Entry Type", "ID", "Site", "Latitude", "Longitude", "Monitoring Officer", "Driver",
        "Date", "Time", "Temperature (°C)", "RH (%)", "Pressure (mbar)",
        "Weather", "Wind Speed", "Wind Direction", "Elapsed Time (min)", "Flow Rate (L/min)", "Observation",
        "Submitted By","Submitted At"
    ]
    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")

    all_values = sheet.get_all_values()

    if not all_values:
        sheet.append_row(expected_header)
    else:
        current_header = all_values[0]
        if current_header != expected_header:
            sheet.delete_rows(1)  # Remove existing header
            sheet.insert_row(expected_header, index=1)  # Insert correct header

    return sheet
sheet = ensure_main_sheet_initialized(spreadsheet, MAIN_SHEET)


# === Data Utilities ===

def convert_timestamps_to_string(df):
    for col in df.select_dtypes(include=['datetime64[ns]']).columns:
        df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
    return df


import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
from gspread.exceptions import APIError


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
        st.text(f"Details: {e.response.text}")
        return pd.DataFrame()

    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
        return pd.DataFrame()


def add_data(row, username):
    row.append(username)
    row.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    sheet.append_row(row)


def filter_by_site_and_date(df, site_col="Site", date_col="Submitted At", context_label=""):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    st.markdown(f"### 🔍 Filter Records {context_label}")
    sites = ["All"] + sorted(df[site_col].dropna().unique())

    selected_site = st.selectbox(
        f"Filter by Site {context_label}:",
        sites,
        key=f"{context_label}_site"
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
        key=f"{context_label}_date"
    )

    filtered_df = df.copy()
    if selected_site != "All":
        filtered_df = filtered_df[filtered_df[site_col] == selected_site]

    filtered_df = filtered_df[filtered_df[date_col].dt.date == selected_date]
    return filtered_df


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


def backup_deleted_row(row_data, original_sheet_name, row_number, deleted_by):
    try:
        backup_sheet = spreadsheet.worksheet("Deleted Records")
    except Exception:
        num_columns = len(row_data) + 3
        backup_sheet = spreadsheet.add_worksheet(
            title="Deleted Records",
            rows="1000",
            cols=str(num_columns)
        )

        header = [
            "Entry Type", "ID", "Site", "Latitude", "Longitude", "Monitoring Officer", "Driver", "Date", "Time",
            "Temperature (°C)", "RH (%)", "Pressure (mbar)", "Weather", "Wind Speed",
            "Wind Direction", "Elapsed Time (min)", "Flow Rate (L/min)", "Observation",
            "Submitted by", "Submitted At", "Deleted At", "Source", "Deleted By"
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
    worksheet = sheet.spreadsheet.worksheet(MERGED_SHEET)
    row_data = worksheet.row_values(index_to_delete + 2)  # Skip header
    backup_deleted_row(row_data, "Merged Sheet", index_to_delete + 2, deleted_by)
    worksheet.delete_rows(index_to_delete + 2)


def restore_specific_deleted_record(selected_index: int):
    try:
        backup_sheet = spreadsheet.worksheet("Deleted Records")
        deleted_rows = backup_sheet.get_all_values()

        if len(deleted_rows) <= 1:
            return "❌ No deleted records to restore."

        headers = deleted_rows[0]
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


def merge_start_stop(df):
    df = df.copy()
    df.columns = df.columns.str.strip()

    merge_keys = ["ID", "Site", "Latitude", "Longitude"]

    if "Entry Type" not in df.columns:
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
        merged["Elapsed Time (min)_Start"] = pd.to_numeric(merged["Elapsed Time (min)_Start"], errors="coerce")
        merged["Elapsed Time (min)_Stop"] = pd.to_numeric(merged["Elapsed Time (min)_Stop"], errors="coerce")

        # Keep units in minutes to match the column name
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

    merged = merged.drop(columns=["seq"])

    desired_order = [
        "ID", "Site", "Latitude", "Longitude",
        "Entry Type_Start", "Monitoring Officer_Start", "Driver_Start", "Date_Start", "Time_Start",
        "Temperature (°C)_Start", "RH (%)_Start", "Pressure (mbar)_Start", "Weather_Start",
        "Wind Speed_Start", "Wind Direction_Start", "Elapsed Time (min)_Start", "Flow Rate (L/min)_Start",
        "Observation_Start", "Submitted At_Start",
        "Entry Type_Stop", "Monitoring Officer_Stop", "Driver_Stop", "Date_Stop", "Time_Stop",
        "Temperature (°C)_Stop", "RH (%)_Stop", "Pressure (mbar)_Stop", "Weather_Stop",
        "Wind Speed_Stop", "Wind Direction_Stop", "Elapsed Time (min)_Stop", "Flow Rate (L/min)_Stop",
        "Observation_Stop", "Submitted At_Stop",
        "Elapsed Time Diff (min)", "Average Flow Rate (L/min)"
    ]

    existing_cols = [col for col in desired_order if col in merged.columns]
    return merged[existing_cols]


def sanitize_for_google_sheets(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Convert datetime-like columns
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Replace infinities
    df = df.replace([np.inf, -np.inf], np.nan)

    # Convert everything to object before cell-wise cleaning
    df = df.astype(object)

    def clean_cell(x):
        if pd.isna(x):
            return ""
        if isinstance(x, pd.Timestamp):
            return x.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(x, (list, dict, tuple, set)):
            return str(x)
        return x

    # If your pandas version warns on applymap, replace with:
    # df = df.apply(lambda col: col.map(clean_cell))
    df = df.applymap(clean_cell)

    # Make all headers strings
    df.columns = [str(c) for c in df.columns]

    return df


def save_merged_data_to_sheet(df, spreadsheet, sheet_name):
    if df.empty:
        return

    df = convert_timestamps_to_string(df)
    df = sanitize_for_google_sheets(df)

    try:
        try:
            ws = spreadsheet.worksheet(sheet_name)
            spreadsheet.del_worksheet(ws)
        except Exception:
            pass

        rows = max(len(df) + 10, 1000)
        cols = max(len(df.columns) + 5, 50)

        new_sheet = spreadsheet.add_worksheet(
            title=sheet_name,
            rows=str(rows),
            cols=str(cols)
        )

        values = [df.columns.tolist()] + df.values.tolist()

        new_sheet.update(
            range_name="A1",
            values=values
        )

    except Exception as e:
        st.error(f"❌ Failed to save merged data to Google Sheets: {e}")
        st.write("Preview of data being written:")
        st.dataframe(df.head())


def filter_dataframe(df, site_filter=None, date_range=None):
    if df.empty:
        return df

    df = df.copy()

    if "Submitted At" in df.columns:
        df["Submitted At"] = pd.to_datetime(df["Submitted At"], errors="coerce")

    if site_filter and site_filter != "All":
        df = df[df["Site"] == site_filter]

    if date_range and len(date_range) == 2:
        start, end = date_range
        df = df[
            (df["Submitted At"].dt.date >= start) &
            (df["Submitted At"].dt.date <= end)
        ]

    return df


def display_and_merge_data(df, spreadsheet, merged_sheet_name):
    if df.empty:
        st.info("No data submitted yet.")
        return

    with st.expander("🔍 Filter Records"):
        site_filter = st.selectbox(
            "Filter by Site",
            ["All"] + sorted(df["Site"].dropna().unique())
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



