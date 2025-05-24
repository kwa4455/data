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


svg_icons = {
    "Home": '''
        <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
        <path d="M3 9.75L12 3l9 6.75v10.5A1.75 1.75 0 0 1 19.25 22H4.75A1.75 1.75 0 0 1 3 20.25V9.75z" />
        </svg>
    ''',
    "Notes": '''
        <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
        <path d="M19 3H5a2 2 0 0 0-2 2v14l4-4h12a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2z" />
        </svg>
    ''',
    "Write": '''
        <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
        <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" />
        </svg>
    ''',
    "Calc": '''
        <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
        <path d="M5 2h14a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm0 18h14V4H5v16zm4-4h2v2H9v-2zm4 0h2v2h-2v-2zM9 10h2v2H9v-2zm4 0h2v2h-2v-2z" />
        </svg>
    ''',
    "Settings": '''
        <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
        <path d="M19.43 12.98c.04-.32.07-.65.07-.98s-.03-.66-.07-.98l2.11-1.65a.5.5 0 0 0 .12-.63l-2-3.46a.5.5 0 0 0-.6-.22l-2.49 1a7.02 7.02 0 0 0-1.69-.98l-.38-2.65A.5.5 0 0 0 14 2h-4a.5.5 0 0 0-.5.42l-.38 2.65a7.02 7.02 0 0 0-1.69.98l-2.49-1a.5.5 0 0 0-.6.22l-2 3.46a.5.5 0 0 0 .12.63L4.57 11c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65a.5.5 0 0 0-.12.63l2 3.46c.14.25.45.35.7.22l2.49-1a7.02 7.02 0 0 0 1.69.98l.38 2.65a.5.5 0 0 0 .5.42h4a.5.5 0 0 0 .5-.42l.38-2.65a7.02 7.02 0 0 0 1.69-.98l2.49 1a.5.5 0 0 0 .6-.22l2-3.46a.5.5 0 0 0-.12-.63l-2.11-1.65zM12 15.5A3.5 3.5 0 1 1 12 8.5a3.5 3.5 0 0 1 0 7z"/>
        </svg>
    '''
}

query_params = st.experimental_get_query_params()
active_page = query_params.get("page", [pages[0] if pages else ""])[0]

# Render sidebar
with st.sidebar:
    st.markdown("## 📁 Navigation")

    if pages:
        sidebar_html = '<div class="svg-sidebar">'
        for page in pages:
            active_class = "active" if page == active_page else ""
            icon_svg = svg_icons.get(page, "📄")
            sidebar_html += f"""
                <a href="?page={page}" class="nav-link {active_class}">
                    <span class="svg-icon">{icon_svg}</span>
                    <span class="link-text">{page}</span>
                </a>
            """
        sidebar_html += "</div>"
        st.markdown(sidebar_html, unsafe_allow_html=True)
        st.markdown("---")
    else:
        st.warning("No pages available for your role.")

# CSS styling for navigation
st.markdown("""
<style>
.svg-sidebar {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}
.nav-link {
    display: flex;
    align-items: center;
    padding: 0.6rem 1rem;
    border-radius: 8px;
    background-color: rgba(255,255,255,0.05);
    text-decoration: none;
    color: #ddd;
    transition: all 0.2s ease;
}
.nav-link:hover {
    background-color: rgba(255,255,255,0.1);
    transform: translateX(5px);
}
.nav-link.active {
    background-color: #52b788;
    color: #fff;
    box-shadow: 0 0 10px #74c69d;
}
.svg-icon {
    margin-right: 0.7rem;
    display: flex;
    align-items: center;
}
.link-text {
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)







# Call theming setup
apply_custom_theme()



# Content with animation
st.markdown('<div class="slide-in">', unsafe_allow_html=True)
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
