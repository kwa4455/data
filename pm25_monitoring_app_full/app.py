import sys
sys.path.append("modules")

import streamlit as st
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_option_menu import option_menu

# === Internal Module Imports ===
from admin.show import show
from admin.user_management import admin_panel
from components import (
    data_entry_form,
    edit_data_entry_form,
    pm25_calculation,
    supervisor_review_section
)
from modules.authentication import login, logout_button
from modules.user_utils import ensure_users_sheet, get_gspread_client
from resource import load_data_from_sheet, sheet, spreadsheet
from constants import MERGED_SHEET, CALC_SHEET, USERS_SHEET

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

SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
spreadsheet = client.open_by_key(SPREADSHEET_ID)
users_sheet = ensure_users_sheet(spreadsheet)

# === LOGIN GATE ===
logged_in, authenticator = login(users_sheet)
if not logged_in:
    st.stop()

# === Header ===
st.title("🇬🇭 EPA Ghana | PM2.5 Field Data Platform")
username = st.session_state.get("username")
role = st.session_state.get("role")
st.info(f"👤 Logged in as: **{username}** (Role: `{role}`)")

# === Load Data Once ===
if "df" not in st.session_state:
    with st.spinner("🔄 Loading data..."):
        st.session_state.df = load_data_from_sheet(sheet)
        st.session_state.sheet = sheet
        st.session_state.spreadsheet = spreadsheet

# === Navigation ===
role_pages = {
    "admin": ["📥 Data Entry Form", "✏️ Edit Data Entry Form", "🗂️ PM25 Calculation", "⚙️ Admin Panel"],
    "collector": ["📥 Data Entry Form", "✏️ Edit Data Entry Form"],
    "editor": ["✏️ Edit Data Entry Form", "🗂️ PM25 Calculation"],
    "viewer": ["🗂️ PM25 Calculation"],
    "supervisor": ["🗂️ PM25 Calculation", "🗂️ Supervisor Review Section"]
}
pages = role_pages.get(role, [])

with st.sidebar:
    st.title("📁 Navigation")
    choice = option_menu(
        menu_title="Go to",
        options=pages,
        icons=["cloud-upload", "pencil", "folder", "gear"][:len(pages)],
        menu_icon="cast",
        default_index=0,
    )
    st.markdown("---")
    logout_button(authenticator)

# === Page Routing ===
if choice == "📥 Data Entry Form":
    data_entry_form.show()
elif choice == "✏️ Edit Data Entry Form":
    edit_data_entry_form.show()
elif choice == "🗂️ PM25 Calculation":
    pm25_calculation.show()
elif choice == "🗂️ Supervisor Review Section":
    supervisor_review_section.show()
elif choice == "⚙️ Admin Panel":
    admin_panel()
