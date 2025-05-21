import sys
sys.path.append("modules")

import streamlit as st
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials


from admin.show import show
from admin.user_management import admin_panel




from modules.authentication import login, logout_button,require_role,require_login
from modules.user_utils import ensure_users_sheet
from resoure import load_data_from_sheet, add_data, merge_start_stop,save_merged_data_to_sheet,sheet,spreadsheet

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
name = st.session_state.get("name")
username = st.session_state.get("username")
role = st.session_state.get("role")

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

st.title("🇬🇭 EPA Ghana | PM2.5 Field Data Platform")
st.info(f"👤 Logged in as: **{username}** (Role: `{role}`)")

# Sidebar
with st.sidebar:
    st.title("📁 Navigation")

    pages = []
    if role == "admin":
        pages = ["📥 Data Entry Form", "✏️ Edit Data Entry Form", "🗂️ PM25 Calculation", "⚙️ Admin Panel"]
    elif role == "collector":
        pages = ["📥 Data Entry Form", "✏️ Edit Data Entry Form"]
    elif role == "editor":
        pages = ["✏️ Edit Data Entry Form", "🗂️ PM25 Calculation"]
    elif role == "viewer":
        pages = ["🗂️ PM25 Calculation"]

    choice = st.selectbox("Go to", pages)
    logout_button(authenticator)

# Load data
if "df" not in st.session_state:
    with st.spinner("🔄 Loading data..."):
        sheet = spreadsheet.worksheet("Observations")  # Adjust as needed
        st.session_state.df = load_data_from_sheet(sheet)
        st.session_state.sheet = sheet
        st.session_state.spreadsheet = spreadsheet

# Page Routing
if choice == "📥 Data Entry Form":
    data_entry_form.show()
elif choice == "✏️ Edit Data Entry Form":
    edit_data_entry_form.show()
elif choice == "🗂️ PM25 Calculation":
    pm25_calculation.show()
elif choice == "⚙️ Admin Panel":
    admin_panel()

st.markdown("Use the sidebar to navigate through available tools.")
