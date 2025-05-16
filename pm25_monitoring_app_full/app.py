import sys
sys.path.append("modules")

import streamlit as st
# === Page Setup ===
st.set_page_config(page_title="PM₂.₅ Monitoring App", layout="wide")


import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from modules.authentication import login, logout_button
from modules.user_utils import ensure_users_sheet
from pages import main, data_entry, edit_records, pm_calculation, admin  # Assuming these are your app sections


# === Google Sheets Auth ===
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

SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
spreadsheet = client.open_by_key(SPREADSHEET_ID)
users_sheet = ensure_users_sheet(spreadsheet)

# === Login ===
logged_in, authenticator = login(users_sheet)
if not logged_in:
    st.stop()

# === Sidebar and Page Navigation ===
st.sidebar.title(f"👋 Welcome {st.session_state['name']}")

page = st.sidebar.radio("Go to", ["Main", "Data Entry", "Edit Records", "PM Calculation", "Admin"])
logout_button(authenticator)

# === Page Dispatcher ===
if page == "Main":
    main.show()
elif page == "Data Entry":
    data_entry.show()
elif page == "Edit Records":
    edit_records.show()
elif page == "PM Calculation":
    pm_calculation.show()
elif page == "Admin":
    admin.show()
