
import streamlit as st
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
        role = st.selectbox("Role", ["viewer", "editor"])  # Can be adjusted later in admin panel
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



import streamlit as st

def inject_global_css(theme, font_size=16):
    """
    Injects global CSS styling into the Streamlit app based on the provided theme and font size.
    
    Parameters:
    - theme: dict with keys like 'text', 'background', 'input_bg', 'button', 'hover'
    - font_size: int (default = 16), sets base font size in pixels
    """
    st.markdown(f"""
    <style>
    html, body, .stApp {{
        font-size: {font_size}px;
        color: {theme["text"]};
        background-color: {theme["background"]};
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        transition: background 0.5s ease, color 0.5s ease;
    }}

    [class^="css"], button, input, label, textarea, select {{
        font-size: {font_size}px !important;
        color: {theme["text"]} !important;
    }}

    .stTextInput > div > input,
    .stSelectbox > div > div,
    .stRadio > div,
    textarea {{
        background-color: {theme["input_bg"]} !important;
        color: {theme["text"]} !important;
        border: 1px solid {theme["button"]};
        backdrop-filter: blur(6px);
        -webkit-backdrop-filter: blur(6px);
    }}

    div.stButton > button,
    .stDownloadButton > button {{
        background-color: {theme["button"]};
        color: white;
        border-radius: 10px;
        padding: 0.7em 1.5em;
        font-weight: bold;
        font-size: 1rem;
        box-shadow: 0 0 15px {theme["hover"]};
        transition: all 0.3s ease;
    }}

    div.stButton > button:hover,
    .stDownloadButton > button:hover {{
        background-color: {theme["hover"]};
        box-shadow: 0 0 25px {theme["hover"]}, 0 0 35px {theme["hover"]};
        transform: scale(1.05);
    }}

    .glass-container {{
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 15px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        padding: 1.5rem;
        margin-bottom: 2rem;
    }}

    ::-webkit-scrollbar {{
        width: 8px;
    }}
    ::-webkit-scrollbar-thumb {{
        background: {theme["button"]};
        border-radius: 10px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: {theme["hover"]};
    }}

    .glow-text {{
        text-align: center;
        font-size: 3em;
        color: {theme["hover"]};
        text-shadow: 0 0 5px {theme["hover"]}, 0 0 10px {theme["hover"]}, 0 0 20px {theme["hover"]};
        margin-bottom: 20px;
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
        backdrop-filter: blur(8px);
    }}
    </style>
    """, unsafe_allow_html=True)

