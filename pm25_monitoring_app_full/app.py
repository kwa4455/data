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

# Inject styles (define CSS globally)
def inject_global_css():
    st.markdown(
        """
        <style>
        .css-18e3th9 {padding-top: 1rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_global_css()


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

    choice = option_menu(
        menu_title="Go to",
        options=pages,
        icons=["cloud-upload", "pencil", "folder", "gear"][:len(pages)],
        menu_icon="cast",
        default_index=0,
    )

    st.markdown("---")
    logout_user()

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

# === LOGIN ===
logged_in, authenticator = login(users_sheet)
if not logged_in:
    st.stop()

# === AFTER LOGIN ===
st.sidebar.title(f"👋 Welcome {st.session_state['name']}")
logout_button(authenticator)

st.session_state["authenticated"] = True
st.session_state["name"] = name
st.session_state["username"] = username
st.session_state["role"] = role

st.markdown("Use the sidebar to navigate through available tools.")
