import streamlit as st
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import streamlit_authenticator as stauth
import time
from gspread.exceptions import APIError
from gspread.exceptions import WorksheetNotFound 

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

def hash_password(password):
    return stauth.Hasher([password]).generate()[0]


for _ in range(20):
    do_some_sheet_read()
    time.sleep(1.5)  # add delay between calls

@st.cache_data(ttl=600)
def ensure_users_sheet(spreadsheet):
    try:
        return spreadsheet.worksheet(USERS_SHEET)
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(USERS_SHEET, rows="100", cols="5")
        sheet.append_row(["Username", "Full Name", "Email", "Password", "Role"])
        return sheet

@st.cache_data(ttl=600)
def ensure_reg_requests_sheet(spreadsheet):
    try:
        return spreadsheet.worksheet(REG_REQUESTS_SHEET)
    except WorksheetNotFound:
        # Create the worksheet if it doesn't exist
        sheet = spreadsheet.add_worksheet(title=REG_REQUESTS_SHEET, rows=100, cols=6)
        sheet.append_row(["Timestamp", "Username", "Full Name", "Email","Password", "Role", "Status"])  # header
        return sheet

@st.cache_data(ttl=600)
def ensure_log_sheet(spreadsheet):
    try:
        return spreadsheet.worksheet(LOG_SHEET)
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(LOG_SHEET, rows="100", cols="5")
        sheet.append_row(["Username", "Action", "By", "Timestamp"])
        return sheet



@st.cache_data(ttl=600)
def register_user_request(username, name, email, password, role, spreadsheet):
    sheet = ensure_reg_requests_sheet(spreadsheet)
    requests = sheet.get_all_records()

    for user in requests:
        if user["Username"].lower() == username.lower():
            return False, "Username already requested."
        if user["Email"].lower() == email.lower():
            return False, "Email already requested."

    # Hash the password before saving it to the sheet
    password_hash = hash_password(password)
    
    # Print the password hash to the console for debugging
    print("Generated Password Hash:", password_hash)

    # Append the registration request with hashed password
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, username, name, email, password_hash, role, "pending"])

    return True, "✅ Registration request submitted."

@st.cache_data(ttl=600)
def register_user_to_sheet(username, name, email, password, role, sheet, is_hashed=False):
    users = sheet.get_all_records()
    for user in users:
        if user["Username"] == username:
            return False, "Username already exists."
        if user["Email"] == email:
            return False, "Email already registered."

    final_pw = password if is_hashed else stauth.Hasher([password]).generate()[0]
    sheet.append_row([username, name, email, final_pw, role])
    return True, "User approved and added."

def delete_registration_request(username, spreadsheet):
    sheet = ensure_reg_requests_sheet(spreadsheet)
    data = sheet.get_all_values()

    # Find the index of the "Username" column in the header row (first row)
    header = data[0]
    try:
        username_col_index = header.index("Username")
    except ValueError:
        print("Error: 'Username' column not found in header")
        return False

    for i, row in enumerate(data[1:], start=2):  # start=2 for 1-based sheet rows skipping header
        print(f"Checking row {i}: {row}")
        # Check with case-insensitive comparison and strip whitespace
        if row[username_col_index].strip().lower() == username.strip().lower():
            print(f"Deleting row {i} for username '{username}'")
            sheet.delete_rows(i)
            return True

    print(f"Username '{username}' not found for deletion.")
    return False


@st.cache_data(ttl=600)
def log_registration_event(username, action, admin_username, spreadsheet):
    sheet = ensure_log_sheet(spreadsheet)
    sheet.append_row([username, action, admin_username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

def approve_user(user_data, admin_username, spreadsheet):
    users_sheet = ensure_users_sheet(spreadsheet)
    success, message = register_user_to_sheet(
        username=user_data["Username"],
        name=user_data["Full Name"],
        email=user_data["Email"],
        password=user_data["Password"],
        role=user_data["Role"],  # <-- admin-assigned role
        sheet=users_sheet,
        is_hashed=True
    )

    if success:
        delete_registration_request(user_data["Username"], spreadsheet)
        log_registration_event(user_data["Username"], "approved", admin_username, spreadsheet)
    return message

@st.cache_data(ttl=600)
def load_users_from_sheet(sheet):
    try:
        users = sheet.get_all_records()
    except APIError as e:
        st.error("❌ Failed to load users from sheet.")
        st.write("Error details:", e)
        raise  # Re-raise the error after logging
    credentials = {"usernames": {}}
    for user in users:
        credentials["usernames"][user["Username"]] = {
            "name": user["Full Name"],
            "email": user["Email"],
            "password": user["Password"]
        }
    return credentials


def get_user_role(username, sheet):
    users = sheet.get_all_records()
    for user in users:
        if user["Username"] == username:
            return user["Role"]
    return "collector"

