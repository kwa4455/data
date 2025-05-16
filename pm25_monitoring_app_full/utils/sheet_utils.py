import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from constants import SPREADSHEET_ID, MAIN_SHEET, MERGED_SHEET, CALC_SHEET

def get_gspread_client():
    creds_json = st.secrets["GOOGLE_CREDENTIALS"]
    creds_dict = json.loads(creds_json)
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

# === Ensure Observations worksheet exists and is initialized ===
def ensure_main_sheet_initialized(spreadsheet, sheet_name):
    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")

    if not sheet.get_all_values():
        sheet.append_row([
            "Entry Type", "ID", "Site", "Monitoring Officer", "Driver",
            "Date", "Time", "Temperature (°C)", "RH (%)", "Pressure (mbar)",
            "Weather", "Wind Speed", "Wind Direction", "Elapsed Time (min)", "Flow Rate (L/min)", "Observation",
            "Submitted At"
        ])
    return sheet

sheet = ensure_main_sheet_initialized(spreadsheet, MAIN_SHEET)

def load_data_from_sheet(sheet):
    try:
        all_values = sheet.get_all_values()
        if not all_values:
            return pd.DataFrame()
        headers = all_values[0]
        rows = all_values[1:]
        if not rows:
            return pd.DataFrame(columns=headers)
        df = pd.DataFrame(rows, columns=headers)
        return convert_timestamps_to_string(df)
    except Exception as e:
        st.error(f"❌ Failed to load data from sheet: {e}")
        return pd.DataFrame()

def save_merged_data_to_sheet(df, spreadsheet, sheet_name):
    df = convert_timestamps_to_string(df)
    if sheet_name in [ws.title for ws in spreadsheet.worksheets()]:
        spreadsheet.del_worksheet(spreadsheet.worksheet(sheet_name))
    new_sheet = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="50")
    new_sheet.update([df.columns.tolist()] + df.values.tolist())

def add_data(row):
    row.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    sheet.append_row(row)

def delete_row(sheet, row_number):
    row_data = sheet.row_values(row_number)
    backup_deleted_row(row_data, "Main Sheet", row_number)
    sheet.delete_rows(row_number)

def delete_merged_record_by_index(index_to_delete):
    worksheet = sheet.spreadsheet.worksheet(MERGED_SHEET)
    row_data = worksheet.row_values(index_to_delete + 2)  # Skip header
    backup_deleted_row(row_data, "Merged Sheet", index_to_delete + 2)
    worksheet.delete_rows(index_to_delete + 2)

def undo_last_delete(sheet):
    st.warning("⚠️ Undo not supported. Check backup sheet manually.")

def display_and_merge_data(df, spreadsheet, merged_sheet_name):
    if df.empty:
        st.info("No data submitted yet.")
        return

    with st.expander("🔍 Filter Records"):
        site_filter = st.selectbox("Filter by Site", ["All"] + sorted(df["Site"].dropna().unique()))
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