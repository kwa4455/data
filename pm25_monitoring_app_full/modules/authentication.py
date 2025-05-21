import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import streamlit_authenticator as stauth
from .user_utils import load_users_from_sheet, get_user_role, approve_user
from .ui_forms import show_registration_form, show_account_recovery

def login(sheet):
    users = load_users_from_sheet(sheet)

    authenticator = stauth.Authenticate(
        users,
        "pm25_app",
        "abcdef",
        cookie_expiry_days=1
    )

    st.title("🌿 PM₂.₅ Monitoring App Login")
    st.markdown("Please log in to access the system. Contact admin if you don’t have an account.")

    # === Authenticator Login ===
    name, auth_status, username = authenticator.login("Login", location="main")

    if auth_status is False:
        st.error("❌ Incorrect username or password")
    elif auth_status is None:
        st.info("🕒 Please enter your login credentials")
    elif auth_status:
        # Successful login
        st.session_state["name"] = name
        st.session_state["username"] = username
        st.session_state["role"] = get_user_role(username, sheet)
        st.session_state["authenticated"] = True  # Mark the user as authenticated

        # Clear any form flags on successful login
        st.session_state.show_register = False
        st.session_state.show_recovery = False
        return True, authenticator

    # === Handle Form State Flags ===
    if "show_register" not in st.session_state:
        st.session_state.show_register = False
    if "show_recovery" not in st.session_state:
        st.session_state.show_recovery = False

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

    if st.session_state.show_register:
        show_registration_form(sheet)

    if st.session_state.show_recovery:
        show_account_recovery(sheet)

    return False, None

def logout_button(authenticator):
    authenticator.logout("Logout", "sidebar")

def require_login():
    """Ensure the user is logged in, else redirect to Home page."""
    if not st.session_state.get("authenticated", False):  # Ensure `authenticated` is checked
        st.error("🔐 You must log in to access this page.")
        switch_page("app")  # Redirect to the main app page
        st.stop()
        
def require_role(required_roles):
    # Check if the user is logged in (i.e., username is in session state)
    if "username" not in st.session_state:
        st.error("🚫 Please log in to access this page.")  # Show error if not logged in
        st.stop()  # Stop further execution

    # Ensure the role is available in session state
    user_role = st.session_state.get("role")
    if not user_role:
        st.error("🚫 User role not found.")
        st.stop()  # Stop further execution

    # Check if the user's role matches one of the required roles
    if user_role not in required_roles:
        st.error("🚫 You do not have permission to access this page.")
        st.stop()  # Stop further execution

def require_role(allowed_roles):
    if not st.session_state.get("authenticated", False):  # Ensure `authenticated` is checked
        st.error("🚫 Please log in to access this page.")
        st.stop()

    role = st.session_state.get("role", "").lower()
    if role not in [r.lower() for r in allowed_roles]:
        st.error("⛔ You are not authorized to view this page.")
        st.stop()
