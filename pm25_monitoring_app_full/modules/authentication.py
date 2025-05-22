import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import streamlit_authenticator as stauth
from .user_utils import load_users_from_sheet, get_user_role
from .ui_forms import show_registration_form, show_account_recovery
import streamlit as st
import streamlit_authenticator as stauth

def login(sheet):
    users = load_users_from_sheet(sheet)  # Your function to load user dict for stauth

    # Inject custom CSS styles for background and glass login card
    st.markdown("""
    <style>
    /* Full-screen forest background */
    body {
        background-image: url('https://images.unsplash.com/photo-1501785888041-af3ef285b470');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Centered glass card */
    .login-container {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 40px;
        width: 350px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.3);
        z-index: 9999;
    }

    .login-container h2 {
        margin-bottom: 30px;
    }

    /* Style Streamlit inputs inside container */
    .login-container .stTextInput>div>div>input {
        background-color: rgba(255,255,255,0.2) !important;
        color: white !important;
        border: none;
    }

    .login-container .stTextInput>div>div>input::placeholder {
        color: #ccc;
    }

    .login-container .stButton button {
        width: 100%;
        padding: 10px;
        border: none;
        border-radius: 25px;
        background-color: #ffffffaa;
        color: #000;
        font-weight: bold;
        cursor: pointer;
    }

    .login-container .stButton button:hover {
        background-color: #fff;
        color: #000;
    }

    </style>
    """, unsafe_allow_html=True)

    # Start the glass card container
    st.markdown('<div class="login-container">', unsafe_allow_html=True)

    # Title inside card
    st.markdown("<h2>🔐 Login to EPA Ghana</h2>", unsafe_allow_html=True)
    st.title("🌿 PM₂.₅ Monitoring App Login")
    st.markdown("Please log in to access the system. Contact admin if you don’t have an account.")

    # Initialize authenticator with users loaded from sheet
    authenticator = stauth.Authenticate(
        users,
        "pm25_app",       # cookie name
        "abcdef",         # key (change this in production)
        cookie_expiry_days=1
    )

    # Show login form
    name, auth_status, username = authenticator.login("Login", location="main")

    # Handle login outcomes
    if auth_status is False:
        st.error("❌ Incorrect username or password")
    elif auth_status is None:
        st.info("🕒 Please enter your login credentials")
    elif auth_status:
        # Successful login - save session state variables
        st.session_state["name"] = name
        st.session_state["username"] = username
        st.session_state["role"] = get_user_role(username, sheet)  # Your function to get user role
        st.session_state["authenticated"] = True

        # Reset form flags
        st.session_state.show_register = False
        st.session_state.show_recovery = False

        # Close container div before returning
        st.markdown('</div>', unsafe_allow_html=True)

        return True, authenticator

    # Initialize form flags if not present
    if "show_register" not in st.session_state:
        st.session_state.show_register = False
    if "show_recovery" not in st.session_state:
        st.session_state.show_recovery = False

    # Divider and help options
    st.divider()
    st.subheader("🔧 Need Help?")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🆕 Register New Account"):
            st.session_state.show_register = True
            st.session_state.show_recovery = False

    with col2:
        if st.button("🔑 Forgot Password or Username"):
            st.session_state.show_recovery = True
            st.session_state.show_register = False

    # Show registration or recovery forms if toggled
    if st.session_state.show_register:
        show_registration_form(sheet)  # Your form function here

    if st.session_state.show_recovery:
        show_account_recovery(sheet)  # Your recovery function here

    # Close the container div
    st.markdown('</div>', unsafe_allow_html=True)

    return False, None


def logout_button(authenticator):
    """Logout button in the sidebar."""
    authenticator.logout("Logout", "sidebar")

def require_login():
    """Redirect to login if the user is not authenticated."""
    if not st.session_state.get("authenticated", False):
        st.warning("🔐 Please log in to access this page.")
        switch_page("app")  # Name of your login/home page
        st.stop()

def require_role(allowed_roles):
    """Ensure the logged-in user has an allowed role."""
    if not st.session_state.get("authenticated", False):
        st.warning("🚫 Please log in to access this page.")
        switch_page("app")
        st.stop()

    user_role = st.session_state.get("role", "").lower()
    if user_role not in [role.lower() for role in allowed_roles]:
        st.error("⛔ You are not authorized to view this page.")
        switch_page("app")
        st.stop()
