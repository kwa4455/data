import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit_authenticator as stauth
from datetime import datetime

# === Constants ===
SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
REG_REQUESTS_SHEET = "Registration Requests"
USERS_SHEET = "Users"
LOG_SHEET = "Registration Log"

# === GSpread Client ===
def get_gspread_client():
    creds_dict = st.secrets["GOOGLE_CREDENTIALS"]
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

# === Ensure Users Sheet Exists ===
def ensure_users_sheet(spreadsheet):
    try:
        return spreadsheet.worksheet(USERS_SHEET)
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(USERS_SHEET, rows="100", cols="5")
        sheet.append_row(["Username", "Name", "Email", "Password", "Role"])
        return sheet

# === Register Approved User ===
def approve_user(user_data):
    client = get_gspread_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
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
    if not success:
        return f"⚠️ Failed to approve user: {message}"
    return f"✅ User {user_data['username']} approved successfully with role '{user_data['role']}'."

# === Register Function ===
def register_user_to_sheet(username, name, email, password, role, sheet, is_hashed=False):
    users = sheet.get_all_records()

    for user in users:
        if user["Username"] == username:
            return False, "⚠️ Username already exists."
        if user["Email"] == email:
            return False, "⚠️ Email already registered."

    final_pw = password if is_hashed else stauth.Hasher([password]).generate()[0]
    sheet.append_row([username, name, email, final_pw, role])
    return True, "✅ Registration successful."

# === Load Users ===
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

# === Get Role ===
def get_user_role(username, sheet):
    users = sheet.get_all_records()
    for user in users:
        if user["Username"] == username:
            return user["Role"]
    return "viewer"

# === Delete Registration Request ===
def delete_registration_request(username):
    client = get_gspread_client()
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(REG_REQUESTS_SHEET)
    data = sheet.get_all_values()
    for i, row in enumerate(data):
        if i == 0:
            continue
        if row[0] == username:
            sheet.delete_rows(i + 1)
            return True
    return False

# === Log Registration Event ===
def log_registration_event(username, action, admin_username):
    client = get_gspread_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    try:
        log_sheet = spreadsheet.worksheet(LOG_SHEET)
    except gspread.exceptions.WorksheetNotFound:
        log_sheet = spreadsheet.add_worksheet(LOG_SHEET, rows="100", cols="5")
        log_sheet.append_row(["Username", "Action", "By", "Timestamp"])

    log_sheet.append_row([username, action, admin_username, datetime.now().isoformat()])
