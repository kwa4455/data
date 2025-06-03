
import streamlit as st
from contextlib import contextmanager
from .user_utils import register_user_request,spreadsheet
from .recovery import reset_password, recover_username
from constants import REG_REQUESTS_SHEET, LOG_SHEET

def show_registration_form(sheet):
    st.subheader("🆕 Register")

    # Registration form
    with st.form("register_form"):
        username = st.text_input("Username")
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        role = st.selectbox("Role", ["officer", "editor"])  # Can be adjusted later in admin panel
        submitted = st.form_submit_button("Register")

        if submitted:
            # Check if passwords match
            if password != confirm:
                st.error("❌ Passwords do not match")
            elif not username or not name or not email or not password:
                st.error("❌ All fields must be filled in.")
            else:
                # Register user and move the data to the registration request sheet
                success, message = register_user_request(username, name, email, password, role,spreadsheet)
                if success:
                    st.success(message)
                else:
                    st.error(message)



def display_password_reset_form(sheet):
    st.subheader("🔑 Reset Password")
    email = st.text_input("Enter your email")
    new_password = st.text_input("Enter new password", type="password")
    if st.button("Reset Password"):
        success, message = reset_password(email, new_password, sheet)
        st.success(message) if success else st.error(message)

def display_username_recovery_form(sheet):
    st.subheader("🆔 Recover Username")
    email = st.text_input("Enter your email", key="recover_email")
    if st.button("Recover Username", key="recover_username_btn"):
        success, message = recover_username(email, sheet)
        st.success(message) if success else st.error(message)

def show_account_recovery(sheet):
    tab1, tab2 = st.tabs(["🔑 Reset Password", "🆔 Recover Username"])
    with tab1:
        display_password_reset_form(sheet)
    with tab2:
        display_username_recovery_form(sheet)



def add_glass_style():
    st.markdown("""
    <style>
    /* Glassmorphism Base Styles */
    section[data-testid="stSidebar"] > div {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border-radius: 1rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        padding: 1.5rem;
        color: #1c1c1c;
    }

    

    .glass-box {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 1rem;
        padding: 1.5rem;
        margin-top: 1rem;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
        color: #1c1c1c;
        transition: transform 0.2s ease-in-out;
    }
    .glass-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.25);
    }

    .stApp {
        background: linear-gradient(135deg, #f5f5f5 0%, #fefffe 100%);
        font-family: 'Segoe UI', sans-serif;
    }

    /* Extended styles for buttons, inputs, sliders, and charts */
    button[kind="primary"] {
        background: rgba(255, 255, 255, 0.12) !important;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #1c1c1c !important;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
        transition: all 0.2s ease-in-out;
    }
    button[kind="primary"]:hover {
        background: rgba(255, 255, 255, 0.2) !important;
        transform: scale(1.02);
    }

    input, textarea, .stSelectbox, .stTextInput, .stNumberInput {
        background: rgba(255, 255, 255, 0.12) !important;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem;
        color: #1c1c1c !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    .css-1r6slb0, .css-14xtw13 {
        background: rgba(255, 255, 255, 0.12) !important;
        border-radius: 0.5rem;
        padding: 0.25rem;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }

    .element-container:has(canvas) {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 1rem;
        padding: 1rem;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    }
    </style>
    """, unsafe_allow_html=True)

@contextmanager
def glass_box():
    st.markdown('<div class="glass-box">', unsafe_allow_html=True)
    yield
    st.markdown('</div>', unsafe_allow_html=True)

