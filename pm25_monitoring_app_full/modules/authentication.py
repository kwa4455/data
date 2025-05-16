
import streamlit as st
import streamlit_authenticator as stauth
from .user_utils import load_users_from_sheet, get_user_role

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
    
    name, auth_status, username = authenticator.login("Login", location="main")

    if auth_status:
        st.session_state["name"] = name
        st.session_state["username"] = username
        st.session_state["role"] = get_user_role(username, sheet)
        return True, authenticator

    # Show login feedback
    if auth_status is False:
        st.error("❌ Incorrect username or password")
    elif auth_status is None:
        st.info("🕒 Please enter your login credentials")

    # Additional help UI
    from .ui_forms import show_registration_form, show_account_recovery
    st.divider()
    st.subheader("🔧 Need Help?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 Register New Account"):
            show_registration_form(sheet)
    with col2:
        if st.button("🔑 Forgot Password or Username"):
            show_account_recovery(sheet)

    return False, authenticator


def logout_button(authenticator):
    authenticator.logout("Logout", "sidebar")

def require_role(allowed_roles):
    role = st.session_state.get("role")
    if not role:
        st.error("🚫 You must be logged in to view this page.")
        st.stop()
    if role.lower() not in [r.lower() for r in allowed_roles]:
        st.error(f"🚫 Access denied for role: {role}")
        st.stop()
