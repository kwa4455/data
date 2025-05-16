import sys
sys.path.append("modules")

import streamlit as st
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from modules.authentication import login, logout_button
from modules.user_utils import ensure_users_sheet

# === Google Sheets Auth ===
creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

spreadsheet = client.open_by_key(st.secrets["SPREADSHEET_ID"])
users_sheet = ensure_users_sheet(spreadsheet)

# === LOGIN ===
logged_in, authenticator = login(users_sheet)
if not logged_in:
    st.stop()

# === AFTER LOGIN ===
st.sidebar.title(f"👋 Welcome {st.session_state['name']}")
logout_button(authenticator)

st.title("Welcome to the PM₂.₅ Monitoring App")
st.markdown("Use the sidebar to navigate through available tools.")
