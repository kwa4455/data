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
from modules.ui_forms import apply_custom_theme
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
st.title("🇬🇭 EPA Ghana | Air Quality Monitoring | Field Data Entry Platform")
username = st.session_state.get("username")
role = st.session_state.get("role")
st.info(f"👤 Logged in as: **{username}** (Role: {role})")




# === Load Data Once ===
if "df" not in st.session_state:
    with st.spinner("🔄 Loading data..."):
        st.session_state.df = load_data_from_sheet(sheet)
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

# Insert your CSS here
st.markdown("""
    <style>
    /* --- your CSS --- */
    body, .stApp {
        font-family: 'Poppins', sans-serif;
        transition: all 0.5s ease;
    }
    
    /* Light Mode */
    body.light-mode, .stApp.light-mode {
        background: linear-gradient(135deg, #f8fdfc, #d8f3dc);
        color: #1b4332;
    }
    
    /* Dark Mode */
    body.dark-mode, .stApp.dark-mode {
        background: linear-gradient(135deg, #0e1117, #161b22);
        color: #e6edf3;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(12px);
        border-right: 2px solid #74c69d;
        transition: all 0.5s ease;
    }

    /* Buttons */
    .stButton>button, .stDownloadButton>button {
        background: linear-gradient(135deg, #f4f2f4, #a9a9a9);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.7em 1.5em;
        font-weight: bold;
        font-size: 1rem;
        box-shadow: 0 0 15px #f7f7f7;
        transition: 0.3s ease;
    }
    
    .stButton>button:hover, .stDownloadButton>button:hover {
        background: linear-gradient(135deg, #f4f2f4, #a9a9a9);
        box-shadow: 0 0 25px #74c69d, 0 0 35px #dadada;
        transform: scale(1.05);
    }

    /* Custom Scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-thumb {
        background: #74c69d;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #52b788;
    }

    /* Glowing Title */
    .glow-text {
        text-align: center;
        font-size: 3em;
        color: #52b788;
        text-shadow: 0 0 5px #52b788, 0 0 10px #52b788, 0 0 20px #52b788;
        margin-bottom: 20px;
    }

    /* Smooth theme transition */
    html, body, .stApp {
        transition: background 0.5s ease, color 0.5s ease;
    }

    /* Download Button Specific */
    .stDownloadButton>button {
        background: linear-gradient(135deg, #f4f2f4, #a9a9a9);
        box-shadow: 0 0 10px #1b4332;
    }

    /* Button Press Animation */
    .stButton>button:active, .stDownloadButton>button:active {
        transform: scale(0.97);
    }

    /* Tables */
    .stDataFrame, .stTable {
        background: rgba(255, 255, 255, 0.6);
        border-radius: 12px;
        backdrop-filter: blur(10px);
        padding: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        overflow: hidden;
        font-size: 15px;
    }

    /* Table Headers */
    thead tr th {
        background: linear-gradient(135deg, #52b788, #74c69d);
        color: white;
        font-weight: bold;
        text-align: center;
        padding: 0.5em;
    }

    /* Table Rows */
    tbody tr:nth-child(even) {
        background-color: #e9f7ef;
    }
    tbody tr:nth-child(odd) {
        background-color: #ffffff;
    }
    tbody tr:hover {
        background-color: #b7e4c7;
        transition: background-color 0.3s ease;
    }

    /* Graph iframe Glass Effect */
    .element-container iframe {
        background: rgba(255, 255, 255, 0.5) !important;
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 10px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
    }

    /* Dark Mode Table */
    body.dark-mode .stDataFrame, body.dark-mode .stTable {
        background: #161b22cc;
        border-radius: 5px;
        backdrop-filter: blur(8px);
        font-size: 15px;
        overflow: hidden;
    }
    body.dark-mode thead tr th {
        background: linear-gradient(135deg, #238636, #2ea043);
        color: #ffffff;
        font-weight: bold;
        text-align: center;
    }
    body.dark-mode tbody tr:nth-child(even) {
        background: linear-gradient(90deg, #21262d, #30363d);
        color: #e6edf3;
        transition: all 0.3s ease;
    }
    body.dark-mode tbody tr:nth-child(odd) {
        background: linear-gradient(90deg, #161b22, #21262d);
        color: #e6edf3;
        transition: all 0.3s ease;
    }
    body.dark-mode tbody tr:hover {
        background: linear-gradient(90deg, #21262d, #30363d);
        box-shadow: 0 0 15px #58a6ff;
        transform: scale(1.01);
    }

    /* Dark Mode Graph Glow */
    body.dark-mode .element-container iframe {
        background: rgba(22, 27, 34, 0.5) !important;
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 10px;
        border: 2px solid #58a6ff;
        box-shadow: 0 0 15px #58a6ff, 0 0 30px #79c0ff;
        animation: pulse-glow-dark 3s infinite ease-in-out;
    }

    /* Glow Animations */
    @keyframes pulse-glow {
      0% { box-shadow: 0 0 15px #74c69d, 0 0 30px #52b788; }
      50% { box-shadow: 0 0 25px #40916c, 0 0 45px #2d6a4f; }
      100% { box-shadow: 0 0 15px #74c69d, 0 0 30px #52b788; }
    }
    @keyframes pulse-glow-dark {
      0% { box-shadow: 0 0 15px #58a6ff, 0 0 30px #79c0ff; }
      50% { box-shadow: 0 0 25px #3b82f6, 0 0 45px #2563eb; }
      100% { box-shadow: 0 0 15px #58a6ff, 0 0 30px #79c0ff; }
    }
    </style>
""", unsafe_allow_html=True)














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
