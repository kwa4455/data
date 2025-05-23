import streamlit as st



import sys
import os
from streamlit_option_menu import option_menu
from auth.login import login_user
from auth.logout import logout_user
from components import (
    data_entry_form,
    edit_data_entry_form,
    pm25_calculation,
    supervisor_review_section,
    apartment
)
from admin.show import show
from admin.user_management import admin_panel, require_admin

from resource import load_data_from_sheet, sheet, spreadsheet


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

# Login check
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Show login form if not logged in
if not st.session_state.logged_in:
    login_user()
    st.stop()

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

role_pages = {
    "admin": [ "🏛️ Home","📥 Data Entry Form", "✏️ Edit Data Entry Form", "🗂️ PM25 Calculation", "⚙️ Admin Panel"],
    "collector": ["🏛️ Home","📥 Data Entry Form", "✏️ Edit Data Entry Form"],
    "editor": ["🏛️ Home","✏️ Edit Data Entry Form", "🗂️ PM25 Calculation"],
    "supervisor": ["🏛️ Home","🗂️ PM25 Calculation", "🗂️ Supervisor Review Section"]
}

# Assign pages based on the user's role
pages = role_pages.get(role, [])

# Sidebar navigation
with st.sidebar:
    st.title("📁 Navigation")

    choice = option_menu(
        menu_title="Go to",
        options=pages,
        icons=["cloud-upload", "pencil", "folder", "gear", "clipboard"][:len(pages)],  # Add icons here as needed
        menu_icon="cast",
        default_index=0,
    )

    st.markdown("---")
    logout_user()

# Show corresponding page based on the selection
if choice == "🏛️ Home":
    apartment.show()
elif choice == "📥 Data Entry Form":
    data_entry_form.show()
elif choice == "✏️ Edit Data Entry Form":
    edit_data_entry_form.show()
elif choice == "🗂️ PM25 Calculation":
    pm25_calculation.show()
elif choice == "🗂️ Supervisor Review Section":
    supervisor_review_section.show()
elif choice == "⚙️ Admin Panel":
    admin_panel()
