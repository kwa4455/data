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
from resource import load_data_from_sheet, sheet, spreadsheet
from constants import MERGED_SHEET, CALC_SHEET, USERS_SHEET

st.set_page_config(layout="wide")

st.markdown("""
<style>

/* Universal styles */
* {
    font-family: 'Segoe UI', sans-serif;
    transition: all 0.2s ease-in-out;
}

/* =======================
   LIGHT MODE
======================= */
@media (prefers-color-scheme: light) {
    html, body, .stApp {
        background: url('https://source.unsplash.com/1600x900/?clouds,day') no-repeat center center fixed;
        background-size: cover;
        min-height: 100vh;
        backdrop-filter: blur(15px);
    }

    section.main > div {
        background: rgba(255, 255, 255, 0.55);
        color: #111;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }

    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.3);
        border-right: 1px solid rgba(0, 0, 0, 0.1);
    }

    input, textarea, select {
        background: rgba(255, 255, 255, 0.6) !important;
        color: #111 !important;
        border-radius: 8px !important;
        padding: 6px 10px !important;
        font-size: 1rem !important;
    }

    thead, tbody, tr, th, td {
        background: rgba(255, 255, 255, 0.4) !important;
        color: #111 !important;
        font-size: 0.95rem !important;
    }

    button[data-testid="baseButton-primary"] {
        background: linear-gradient(to right, #ff5f6d, #ffc371) !important;
        color: white !important;
        border-radius: 12px;
        font-weight: bold;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transition: transform 0.3s, box-shadow 0.3s;
    }

    button[data-testid="baseButton-primary"]:hover {
        transform: scale(1.03);
        background: linear-gradient(to right, #ff3d5a, #ffb347) !important;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
    }

    div[data-testid="stAlert-info"] {
        background: rgba(0, 0, 0, 0.05);
        color: #111;
        border-radius: 10px;
    }

    a {
        color: #0056cc !important;
        text-decoration: underline;
        font-weight: 500;
    }
}

/* =======================
   DARK MODE
======================= */
@media (prefers-color-scheme: dark) {
    html, body, .stApp {
        background: url('https://i.postimg.cc/tCMmM50P/temp-Imageqld-VCj.avif');
        background-size: cover;
        min-height: 100vh;
        backdrop-filter: blur(8px);
        color: #f5f5f5 !important;
    }

    section.main > div {
        background: rgba(20, 20, 20, 0.85) !important;
        color: #f5f5f5 !important;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
    }

    section[data-testid="stSidebar"] {
        background: rgba(30, 30, 30, 0.95) !important;
        color: #ffffff !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    input, textarea, select {
        background: rgba(255, 255, 255, 0.07) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        font-weight: 500;
        padding: 6px 10px !important;
        font-size: 1rem !important;
    }

    thead, tbody, tr, th, td {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #ffffff !important;
        font-size: 0.95rem !important;
    }

    button[data-testid="baseButton-primary"] {
        background: linear-gradient(to right, #0099f7, #0652dd) !important;
        color: #fff !important;
        border-radius: 12px;
        font-weight: bold;
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.3);
        transition: transform 0.3s, box-shadow 0.3s;
    }

    button[data-testid="baseButton-primary"]:hover {
        transform: scale(1.03);
        background: linear-gradient(to right, #007be5, #0044aa) !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
    }

    div[data-testid="stAlert-info"] {
        background: rgba(255, 255, 255, 0.15);
        color: white !important;
        border-radius: 10px;
    }

    a {
        color: #66ccff !important;
        font-weight: 500;
        text-decoration: underline;
    }

    h1, h2, h3, h4, h5, h6, p, li, label, span {
        color: #f5f5f5 !important;
    }

    .element-container {
        background: rgba(0, 0, 0, 0.6) !important;
        color: #f5f5f5 !important;
    }
}

/* =======================
   SHARED STYLES
======================= */

section.main > div,
.stDataFrame, .stTable,
.element-container {
    border-radius: 16px;
    backdrop-filter: blur(12px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    padding: 1rem;
    transition: transform 0.3s, box-shadow 0.3s;
}

/* Hover effects for tables and graphs */
.stDataFrame:hover, .stTable:hover, .element-container:hover {
    transform: scale(1.02);
    box-shadow: 0 10px 36px rgba(0, 0, 0, 0.3);
}

/* Optional: lighter hover for performance */
button:hover, input:hover, select:hover, textarea:hover {
    box-shadow: 0 0 8px rgba(255, 255, 255, 0.2);
}

/* HR and spacing */
hr {
    border: none;
    border-top: 1px solid rgba(255, 255, 255, 0.2);
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)











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








# === Header ===
username = st.session_state.get("username")
role = st.session_state.get("role")

st.markdown("""
<style>
/* General alert box (st.info, st.warning, etc.) */
div[role="alert"] {
    background: rgba(255, 255, 255, 0.25) !important;
    color: #000 !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    padding: 16px !important;
    font-weight: 500;
}

/* Optional: override icon color for st.info */
div[role="alert"] svg {
    color: #0066cc !important; /* blue tone for info */
}
</style>
""", unsafe_allow_html=True)
st.info(f"👤 Logged in as: **{username}** (Role: {role})")




# === Load Data Once ===
if "df" not in st.session_state:
    with st.spinner("🔄 Loading data..."):
        st.session_state.df = load_data_from_sheet(sheet)
        st.session_state.sheet = sheet
        st.session_state.spreadsheet = spreadsheet




role_pages = {
    "admin": [
        ("🏠 Home", "Home"),
        ("✍️ Data Entry Form", "Data Entry Form"),
        ("🔖 Edit Data Entry Form", "Edit Data Entry Form"),
        ("📟 PM Calculator", "PM Calculator"),
        ("📖 Supervisor Review Section", "Supervisor Review Section"),
        ("⚙️ Admin Panel", "Admin Panel")
    ],
    "officer": [
        ("🏠 Home", "Home"),
        ("✍️ Data Entry Form", "Data Entry Form"),
        ("🔖 Edit Data Entry Form", "Edit Data Entry Form"),
        ("📟 PM Calculator", "PM Calculator"),
    ],
    
    "supervisor": [
        ("🏠 Home", "Home"),
        ("⚙️ Admin Panel", "Admin Panel"),
        ("📖 Supervisor Review Section", "Supervisor Review Section")
    ]
}
pages_with_icons = role_pages.get(role, [])
pages = [p[1] for p in pages_with_icons]



if "selected_page" not in st.session_state or st.session_state["selected_page"] not in pages:
    st.session_state["selected_page"] = pages[0] if pages else None



# 6. Styled Sidebar Navigation
# ------------------------
st.markdown("""
    <style>
    div[role="radiogroup"] > label > div > input[type="radio"] {
        display: none;
    }
    div[role="radiogroup"] > label {
        display: block;
        cursor: pointer;
        user-select: none;
        padding: 12px 15px;
        margin: 5px 0;
        font-size: 16px;
        color: #444;
        background-color: rgba(255, 255, 255, 0.15);
        border-radius: 8px;
        transition: background-color 0.3s ease, color 0.3s ease;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
    }
    div[role="radiogroup"] > label:hover {
        background-color: rgba(255, 255, 255, 0.3);
        color: #20B2AA;
    }
    div[role="radiogroup"] > label[data-baseweb="option"]:has(input[type="radio"]:checked) {
        background-color: #20B2AA;
        color: red;
        box-shadow: 0 0 8px #20B2AA;
    }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("📁 Navigation")
    selected_page = st.radio(
        "Go to",
        options=[p[0] for p in pages_with_icons],
        index=pages.index(st.session_state["selected_page"]) if st.session_state["selected_page"] else 0,
        key="nav_radio"
    )
    for label, page in pages_with_icons:
        if label == selected_page:
            st.session_state["selected_page"] = page
            break
    st.markdown("---")
    logout_button(authenticator)



# ------------------------
# 7. Page Routing
# ------------------------
choice = st.session_state.get("selected_page")


# === Page Routing ===
if choice == "Home":
    apartment.show()
elif choice == "Data Entry Form":
    data_entry_form.show()
elif choice == "Edit Data Entry Form":
    edit_data_entry_form.show()
elif choice == "PM Calculator":
    pm25_calculation.show()
elif choice == "Supervisor Review Section":
    supervisor_review_section.show()
elif choice == "Admin Panel":
    admin_panel()
    
st.markdown("""
<hr>
<div style="
    text-align: center;
    color: var(--color-text);
    font-size: 0.9em;
">
    © 2025 EPA Ghana · Developed by Clement Mensah Ackaah 🦺 · Built with 😍 using Streamlit |
    <a href="mailto:clement.ackaah@epa.gov.gh" style="color: var(--color-text); text-decoration: underline;">
        Contact Support
    </a>
</div>
""", unsafe_allow_html=True)
