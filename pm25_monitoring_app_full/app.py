import sys
sys.path.append("modules")

import streamlit as st
import json
import gspread
import os
import base64
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
from modules.user_utils import get_user_role, spreadsheet,ensure_users_sheet
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



# === CSS as a Python multiline string ===
CSS = """
/* === Global Layout === */
html, body, #root {
    height: 100%;
    margin: 0;
    padding: 0;
    font-family: 'Poppins', sans-serif;
    color: #fff;
    display: flex;
    justify-content: center;
    align-items: center;
    background-repeat: no-repeat;
    background-size: cover;
    background-position: center;
}

/* === Login Card Styling === */
.login_card {
    background: rgba(255, 255, 255, 0.15);
    border-radius: 24px;
    padding: 40px;
    max-width: 400px;
    width: 90%;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    text-align: center;
}

/* === Headers === */
.login_card h3 {
    margin-bottom: 24px;
    font-size: 28px;
    color: #fff;
}

/* === Inputs === */
input[type="text"], input[type="password"] {
    width: 100%;
    padding: 12px 20px;
    margin: 10px 0 20px;
    border-radius: 32px;
    border: 1px solid rgba(255, 255, 255, 0.3);
    background: rgba(255, 255, 255, 0.1);
    color: #fff;
    outline: none;
    font-size: 14px;
    box-sizing: border-box;
}

input[type="text"]::placeholder, input[type="password"]::placeholder {
    color: #ddd;
}

/* === Button Styling === */
button {
    width: 100%;
    padding: 12px;
    border: none;
    border-radius: 32px;
    background-color: rgba(255, 255, 255, 0.4);
    color: #5F2CA7;
    font-weight: 600;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.3s ease-in-out;
}

button:hover {
    background-color: #5F2CA7;
    color: #fff;
}

/* === Responsive === */
@media (max-width: 500px) {
    .login_card {
        padding: 20px;
    }

    h3 {
        font-size: 24px;
    }

    button {
        font-size: 14px;
    }
}
"""










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
    "admin": ["📥 Data Entry Form", "✏️ Edit Data Entry Form", "🗂️ PM25 Calculation", "🗂️ Supervisor Review Section", "⚙️ Admin Panel"],
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
