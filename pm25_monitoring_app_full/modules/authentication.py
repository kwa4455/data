import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import streamlit_authenticator as stauth
from .user_utils import load_users_from_sheet, get_user_role
from .ui_forms import show_registration_form, show_account_recovery


def login(sheet):


    users = load_users_from_sheet(sheet)

    authenticator = stauth.Authenticate(
        users,
        "pm25_app",
        "abcdef",
        cookie_expiry_days=1
    )

    with st.container():
        st.markdown("## 🔐 Login to EPA Ghana")
        st.markdown("🌿 PM₂.₅ Monitoring App Login")
        st.markdown("Please log in to access the system. Contact admin if you don’t have an account.")

        name, auth_status, username = authenticator.login("Login", location="main")

        if auth_status is False:
            st.error("❌ Incorrect username or password")
        elif auth_status is None:
            st.info("🕒 Please enter your login credentials")
        elif auth_status:
            st.session_state["name"] = name
            st.session_state["username"] = username
            st.session_state["role"] = get_user_role(username, sheet)
            st.session_state["authenticated"] = True
            st.session_state.show_register = False
            st.session_state.show_recovery = False
            return True, authenticator

    # Help options
    st.divider()
    st.subheader("🔧 Need Help?")
    col1, col2 = st.columns(2)

    if "show_register" not in st.session_state:
        st.session_state.show_register = False
    if "show_recovery" not in st.session_state:
        st.session_state.show_recovery = False

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
