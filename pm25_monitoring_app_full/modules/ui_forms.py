
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
        role = st.selectbox("Role", ["collector", "editor"])  # Can be adjusted later in admin panel
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

def apply_custom_theme():
    if "theme" not in st.session_state:
        st.session_state.theme = "Light"
    if "font_size" not in st.session_state:
        st.session_state.font_size = "Medium"

    theme_choice = st.sidebar.selectbox(
        "🎨 Choose Theme",
        ["Light", "Dark", "Blue", "Green", "Purple"],
        index=["Light", "Dark", "Blue", "Green", "Purple"].index(st.session_state.theme)
    )
    st.session_state.theme = theme_choice

    font_choice = st.sidebar.radio(
        "🔠 Font Size",
        ["Small", "Medium", "Large"],
        index=["Small", "Medium", "Large"].index(st.session_state.font_size)
    )
    st.session_state.font_size = font_choice

    if st.sidebar.button("🔄 Reset to Defaults"):
        st.session_state.theme = "Light"
        st.session_state.font_size = "Medium"
        st.success("Reset to Light theme and Medium font!")
        st.rerun()

    themes = {
        "Light": {
            "background": "rgba(255, 255, 255, 0.4)",
            "text": "#004d40",
            "button": "#00796b",
            "hover": "#004d40",
            "input_bg": "rgba(255, 255, 255, 0.6)",
            "font": "'Segoe UI', 'Roboto', sans-serif"
        },
        "Dark": {
            "background":"rgba(22, 27, 34, 0.4)",
            "text": "#e6edf3",
            "button": "#238636",
            "hover": "#2ea043",
            "input_bg": "rgba(33, 38, 45, 0.6)",
            "font": "'Fira Code', monospace"
        },
        "Blue": {
            "background": "rgba(210, 230, 255, 0.4)",
            "text": "#0a2540",
            "button": "#1e88e5",
            "hover": "#1565c0",
            "input_bg": "rgba(255, 255, 255, 0.6)",
            "font": "'Poppins', sans-serif"
        },
        "Green": {
            "background": "rgba(223, 255, 231, 0.4)", 
            "text": "#1b5e20",
            "button": "#43a047",
            "hover": "#2e7d32",
            "input_bg": "rgba(255, 255, 255, 0.6)",
            "font": "'Ubuntu', sans-serif"
        },
        "Purple": {
            "background": "rgba(240, 225, 255, 0.4)",
            "text": "#4a148c",
            "button": "#8e24aa",
            "hover": "#6a1b9a",
            "input_bg": "rgba(255, 255, 255, 0.6)",
            "font": "'Comic Neue', cursive"
        }
    }

    font_map = {"Small": "14px", "Medium": "16px", "Large": "18px"}
    theme = themes[st.session_state.theme]
    font_size = font_map[st.session_state.font_size]
    font_family = theme.get("font", "'Segoe UI', 'Roboto', sans-serif")

    def generate_css(theme: dict, font_size: str, font_family: str) -> str:
        return f"""
        <style>
        html, body, .stApp, [class^="css"], button, input, label, textarea, select {{
            font-size: {font_size} !important;
            color: {theme["text"]} !important;
            font-family: {font_family};
        }}
        .stApp {{
            background-color: {theme["background"]} !important;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            background-attachment: fixed;
            transition: background 0.5s ease, color 0.5s ease;
        }}
        html, body, [class^="css"] {{
            background-color: transparent !important;
        }}
        h1, h2, h3 {{
            font-weight: bold;
        }}
        .stTextInput > div > input,
        .stSelectbox > div > div,
        .stRadio > div,
        textarea {{
            background-color: {theme["input_bg"]} !important;
            color: {theme["text"]} !important;
            border: 1px solid {theme["button"]};
            backdrop-filter: blur(6px);
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
        .stButton>button, .stDownloadButton>button {{
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.7em 1.5em;
            font-weight: bold;
            font-size: 1rem;
            box-shadow: 0 0 15px #52b788;
            transition: 0.3s ease;
        }}
        .stButton>button:hover, .stDownloadButton>button:hover {{
            box-shadow: 0 0 25px #74c69d, 0 0 35px #74c69d;
            transform: scale(1.05);
        }}
        .glass-container {{
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        .stContainer {{
            font-size: {font_size};
            color: {theme["text"]};
        }}
        .dataframe, .stDataFrame, .stTable {{
            background-color: rgba(255, 255, 255, 0.1) !important;
            color: {theme["text"]} !important;
            border-radius: 10px;
        }}
        .stTable tbody tr:hover {{
            background-color: rgba(255, 255, 255, 0.2) !important;
        }}
        .css-1d391kg, .css-1lcbmhc, .stSidebar, section[data-testid="stSidebar"] {{
            background-color: {theme["background"]} !important;
            color: {theme["text"]} !important;
            backdrop-filter: blur(10px);
            border-right: 1px solid rgba(255,255,255,0.2);
        }}
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        ::-webkit-scrollbar-thumb {{
            background: #74c69d;
            border-radius: 10px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: #52b788;
        }}
        .glow-text {{
            text-align: center;
            font-size: 3em;
            color: #52b788;
            text-shadow: 0 0 5px #52b788, 0 0 10px #52b788, 0 0 20px #52b788;
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
        /* Animations */
        .fade-in {{
            animation: fadeIn 1s ease-in;
        }}
        .slide-in {{
            animation: slideIn 0.8s ease-out;
        }}
        @keyframes fadeIn {{
            0% {{ opacity: 0; }}
            100% {{ opacity: 1; }}
        }}
        @keyframes slideIn {{
            0% {{ transform: translateY(20px); opacity: 0; }}
            100% {{ transform: translateY(0); opacity: 1; }}
        }}
        </style>
        """

    st.markdown(generate_css(theme, font_size, font_family), unsafe_allow_html=True)



