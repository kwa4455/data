import streamlit as st
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import streamlit_authenticator as stauth

from constants import SPREADSHEET_ID, USERS_SHEET, REG_REQUESTS_SHEET, LOG_SHEET

# Google Sheets Setup
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

def ensure_users_sheet(spreadsheet):
    try:
        return spreadsheet.worksheet(USERS_SHEET)
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(USERS_SHEET, rows="100", cols="5")
        sheet.append_row(["Username", "Name", "Email", "Password", "Role"])
        return sheet

def ensure_reg_requests_sheet(spreadsheet):
    try:
        # Try to fetch the existing sheet
        return spreadsheet.worksheet(REG_REQUESTS_SHEET)
    except gspread.exceptions.WorksheetNotFound:
        # If the sheet doesn't exist, create it
        sheet = spreadsheet.add_worksheet(title=REG_REQUESTS_SHEET, rows=100, cols=6)  # 6 columns for the headers
        sheet.append_row(["username", "name", "email", "password_hash", "role", "timestamp"])  # Adding headers
        return sheet
    except Exception as e:
        # Catch any other exceptions (e.g., permission errors, API issues)
        raise Exception(f"Error while ensuring the registration requests sheet: {str(e)}")

def ensure_reg_requests_sheet(spreadsheet):
    try:
        return spreadsheet.worksheet(REG_REQUESTS_SHEET)
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(REG_REQUESTS_SHEET, rows="100", cols="5")
        sheet.append_row(["username", "name", "email", "password_hash", "timestamp"])
        return sheet

def approve_user(user_data):
    users_sheet = ensure_users_sheet(spreadsheet)
    success, message = register_user_to_sheet(
        username=user_data["username"],
        name=user_data["name"],
        email=user_data["email"],
        password=user_data["password_hash"],
        role=user_data["role"],
        sheet=users_sheet,
        is_hashed=True
    )
    return message

def register_user_to_sheet(username, name, email, password, role, sheet, is_hashed=False):
    users = sheet.get_all_records()
    for user in users:
        if user["Username"] == username:
            return False, "Username already exists."
        if user["Email"] == email:
            return False, "Email already registered."

    final_pw = password if is_hashed else stauth.Hasher([password]).generate()[0]
    sheet.append_row([username, name, email, final_pw, role])
    return True, "Registration successful."

def load_users_from_sheet(sheet):
    users = sheet.get_all_records()
    credentials = {"usernames": {}}
    for user in users:
        credentials["usernames"][user["Username"]] = {
            "name": user["Name"],
            "email": user["Email"],
            "password": user["Password"]
        }
    return credentials

def get_user_role(username, sheet):
    users = sheet.get_all_records()
    for user in users:
        if user["Username"] == username:
            return user["Role"]
    return "viewer"

def delete_registration_request(username):
    sheet = spreadsheet.worksheet(REG_REQUESTS_SHEET)
    data = sheet.get_all_values()
    for i, row in enumerate(data):
        if i == 0:
            continue
        if row[0] == username:
            sheet.delete_rows(i + 1)
            return True
    return False

def log_registration_event(username, action, admin_username):
    try:
        log_sheet = spreadsheet.worksheet(LOG_SHEET)
    except gspread.exceptions.WorksheetNotFound:
        log_sheet = spreadsheet.add_worksheet(LOG_SHEET, rows="100", cols="5")
        log_sheet.append_row(["Username", "Action", "By", "Timestamp"])

    log_sheet.append_row([username, action, admin_username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
