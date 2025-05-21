import sys
sys.path.append("modules")

import streamlit as st
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials


from admin.show import show
from admin.user_management import admin_panel
from components import (
    data_entry_form,
    edit_data_entry_form,
    pm25_calculation,
    supervisor_review_section
)

from modules.authentication import login, logout_button,require_role,require_login
from modules.user_utils import ensure_users_sheet, get_gspread_client
from resource import load_data_from_sheet, add_data, merge_start_stop,save_merged_data_to_sheet,sheet,spreadsheet

from constants import MERGED_SHEET,MERGED_SHEET,CALC_SHEET,USERS_SHEET

creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
spreadsheet = client.open_by_key(SPREADSHEET_ID)
users_sheet = ensure_users_sheet(spreadsheet)
# === LOGIN ===
logged_in, authenticator = login(users_sheet)
if not logged_in:
    st.stop()



# Header and Styling
def inject_global_css():
    st.markdown(
        """
        <style>
        .css-18e3th9 {padding-top: 1rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )

# Role and user info
username = st.session_state.get("username")
role = st.session_state.get("role")

# App header
st.title("🇬🇭 EPA Ghana | PM2.5 Field Data Platform")
st.info(f"👤 Logged in as: **{username}** (Role: `{role}`)")

# Load data once into session state
if "df" not in st.session_state:
    with st.spinner("🔄 Loading data..."):
        st.session_state.df = load_data_from_sheet(sheet)
        st.session_state.sheet = sheet
        st.session_state.spreadsheet = spreadsheet

# Sidebar navigation
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

# Page Routing
if choice == "📥 Data Entry Form":
    require_role(["admin", "collector", "editor"])  # Check role
    data_entry_form.show()
elif choice == "✏️ Edit Data Entry Form":
    require_role(["admin", "editor", "collector"])  # Check role
    edit_data_entry_form.show()
elif choice == "🗂️ PM25 Calculation":
    require_role(["admin", "editor", "supervisor", "viewer"])  # Check role
    pm25_calculation.show()
elif choice == "🗂️ Supervisor Review Section":
    require_role(["supervisor"])  # Only supervisor can access
    supervisor_review_section.show()
elif choice == "⚙️ Admin Panel":
    require_role(["admin"])  # Only admin can access
    admin_panel()
