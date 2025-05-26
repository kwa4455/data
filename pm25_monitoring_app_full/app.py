import sys
sys.path.append("modules")

import streamlit as st
import json
import gspread
import os

from oauth2client.service_account import ServiceAccountCredentials
from streamlit_option_menu import option_menu

# === Internal Module Imports ===
from admin.show import show
from admin.user_management import admin_panel
from components import (
    data_entry_form,
    edit_data_entry_form,
    pm25_calculation,
    supervisor_review_section,
    apartment
)
from modules.authentication import login, logout_button
from modules.user_utils import get_user_role, spreadsheet,ensure_users_sheet
from modules.ui_forms import add_glass_style
from resource import load_data_from_sheet_cached, sheet, spreadsheet
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
    st.markdown('</div>', unsafe_allow_html=True)





def main():
    add_glass_style()


# === Header ===
username = st.session_state.get("username")
role = st.session_state.get("role")
st.info(f"👤 Logged in as: **{username}** (Role: {role})")




# === Load Data Once ===
if "df" not in st.session_state:
    with st.spinner("🔄 Loading data..."):
        st.session_state.df = load_data_from_sheet_cached(sheet)
        st.session_state.sheet = sheet
        st.session_state.spreadsheet = spreadsheet

# === Navigation ===
role_pages = {
    "admin": ["Home","Data Entry Form", "Edit Data Entry Form", "PM25 Calculation", "Supervisor Review Section", "Admin Panel"],
    "collector": ["Home","Data Entry Form", "Edit Data Entry Form"],
    "editor": ["Home","Data Entry Form", "Edit Data Entry Form", "PM25 Calculation"],
    "supervisor": ["Home","Admin Panel", "Supervisor Review Section"]
}
pages = role_pages.get(role, [])



with st.sidebar:
    st.title("📁 Navigation")
    if pages:
        choice = option_menu(
            menu_title="Go to",
            options=pages,
            icons=["house", "pencil", "pen", "calculator","chat-dots", "gear"][:len(pages)],
            menu_icon="cast",
            default_index=0,
        )
    else:
        st.warning("No pages available for your role.")
        choice = None

    st.markdown("---")
    logout_button(authenticator)
    st.markdown('</div>', unsafe_allow_html=True)
















# === Page Routing ===
if choice == "Home":
    apartment.show()
elif choice == "Data Entry Form":
    data_entry_form.show()
elif choice == "Edit Data Entry Form":
    edit_data_entry_form.show()
elif choice == "PM25 Calculation":
    pm25_calculation.show()
elif choice == "Supervisor Review Section":
    supervisor_review_section.show()
elif choice == "Admin Panel":
    admin_panel()
    
 # --- Footer ---
    st.markdown("""
        <hr style="margin-top: 40px; margin-bottom:10px">
        <div style='text-align: center; color: grey; font-size: 0.9em;'>
            © 2025 EPA Ghana · Developed by Clement Mensah Ackaah 🦺 · Built with 😍 using Streamlit | 
            <a href="mailto:clement.ackaah@epa.gov.gh">Contact Support</a>
        </div>
    """, unsafe_allow_html=True)
