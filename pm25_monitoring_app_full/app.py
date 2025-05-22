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

# Set defaults
if "theme" not in st.session_state:
    st.session_state.theme = "Light"
if "font_size" not in st.session_state:
    st.session_state.font_size = "Medium"

# Sidebar - Appearance Controls
st.sidebar.header("🎨 Appearance Settings")

# Theme selection
theme_choice = st.sidebar.selectbox(
    "Choose Theme",
    ["Light", "Dark", "Blue", "Green", "Purple"],
    index=["Light", "Dark", "Blue", "Green", "Purple"].index(st.session_state.theme)
)
st.session_state.theme = theme_choice

# Font size selection
font_choice = st.sidebar.radio("Font Size", ["Small", "Medium", "Large"],
                               index=["Small", "Medium", "Large"].index(st.session_state.font_size))
st.session_state.font_size = font_choice

# Reset to default
if st.sidebar.button("🔄 Reset to Defaults"):
    st.session_state.theme = "Light"
    st.session_state.font_size = "Medium"
    st.success("Reset to Light theme and Medium font!")
    st.rerun()

# Theme settings dictionary
themes = {
    "Light": {
        "background": "linear-gradient(135deg, #e0f7fa, #ffffff)",
        "text": "#004d40",
        "button": "#00796b",
        "hover": "#004d40",
        "input_bg": "#ffffff"
    },
    "Dark": {
        "background": "linear-gradient(135deg, #263238, #37474f)",
        "text": "#e0f2f1",
        "button": "#26a69a",
        "hover": "#00897b",
        "input_bg": "#37474f"
    },
    "Blue": {
        "background": "linear-gradient(135deg, #e3f2fd, #90caf9)",
        "text": "#0d47a1",
        "button": "#1e88e5",
        "hover": "#1565c0",
        "input_bg": "#ffffff"
    },
    "Green": {
        "background": "linear-gradient(135deg, #dcedc8, #aed581)",
        "text": "#33691e",
        "button": "#689f38",
        "hover": "#558b2f",
        "input_bg": "#ffffff"
    },
    "Purple": {
        "background": "linear-gradient(135deg, #f3e5f5, #ce93d8)",
        "text": "#4a148c",
        "button": "#8e24aa",
        "hover": "#6a1b9a",
        "input_bg": "#ffffff"
    },
}

# Font size mapping
font_map = {"Small": "14px", "Medium": "16px", "Large": "18px"}

# Apply theme and inject CSS
theme = themes[st.session_state.theme]
font_size = font_map[st.session_state.font_size]

def generate_css(theme: dict, font_size: str) -> str:
    return f"""
    <style>
    html, body, .stApp, [class^="css"], button, input, label, textarea, select {{
        font-size: {font_size} !important;
        color: {theme["text"]} !important;
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }}
    .stApp {{
        background: {theme["background"]};
        background-attachment: fixed;
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        font-size: {font_size};
        color: {theme["text"]};
    }}
    html, body, [class^="css"] {{
        background-color: transparent !important;
        color: {theme["text"]} !important;
    }}
    h1, h2, h3 {{
        font-weight: bold;
        color: {theme["text"]};
    }}
    .stTextInput > div > input,
    .stSelectbox > div > div,
    .stRadio > div,
    textarea {{
        background-color: {theme["input_bg"]} !important;
        color: {theme["text"]} !important;
        border: 1px solid {theme["button"]};
    }}
    div.stButton > button {{
        background-color: {theme["button"]};
        color: white;
        padding: 0.5em 1.5em;
        border-radius: 8px;
        transition: background-color 0.3s ease;
    }}
    div.stButton > button:hover {{
        background-color: {theme["hover"]};
    }}
    .aqi-card, .instruction-card {{
        background: {theme["background"]};
        color: {theme["text"]};
        border: 2px solid {theme["button"]};
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s, box-shadow 0.3s;
    }}
    
    .footer {{
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: {theme["background"]};
        color: {theme["text"]};
        text-align: center;
        padding: 12px 0;
        font-size: 14px;
        font-weight: bold;
        box-shadow: 0px -2px 10px rgba(0,0,0,0.1);
    }}
    </style>
    """

st.markdown(generate_css(theme, font_size), unsafe_allow_html=True)


with st.sidebar:
    try:
        st.image("epa-logo.png", width=150)
    except:
        pass

    st.markdown("### 🧑‍💻 Developer Information")
    st.markdown("""
    - **Developed by:** Clement Mensah Ackaah  
    - **Email:** clement.ackaah@epa.gov.gh / clementackaah70@gmail.com  
    - **GitHub:** [Visit GitHub](https://github.com/kwa4455)  
    - **LinkedIn:** [Visit LinkedIn](https://www.linkedin.com/in/clementmensahackaah)  
    - **Project Repo:** [Air Quality Dashboard](https://github.com/kwa4455/air-quality-analysis-dashboard)
    """)

components.html(
    f"""
    <div style="background: {theme["button"]}; 
                padding: 30px; 
                border-radius: 12px; 
                color: white; 
                text-align: center; 
                font-size: 42px; 
                font-weight: bold;
                animation: fadeIn 1.5s ease-out;">
        👋 Welcome to the Air Quality Dashboard!
    </div>
    <style>
    @keyframes fadeIn {{
        0% {{opacity: 0; transform: translateY(-20px);}}
        100% {{opacity: 1; transform: translateY(0);}}
    }}
    </style>
    """,
    height=120
)





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
