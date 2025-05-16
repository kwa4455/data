
import streamlit as st
from .user_utils import register_user_to_sheet
from .recovery import reset_password, recover_username

def show_registration_form(sheet):
    st.subheader("🆕 Register")
    with st.form("register_form"):
        username = st.text_input("Username")
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        role = st.selectbox("Role", ["viewer", "editor"])
        submitted = st.form_submit_button("Register")

        if submitted:
            if password != confirm:
                st.error("❌ Passwords do not match")
            else:
                success, message = register_user_to_sheet(username, name, email, password, role, sheet)
                st.success(message) if success else st.error(message)

def display_password_reset_form(sheet):
    st.subheader("🔑 Reset Password")
    email = st.text_input("Enter your email")
    new_password = st.text_input("Enter new password", type="password")
    if st.button("Reset Password"):
        success, message = reset_password(email, new_password, sheet)
        st.success(message) if success else st.error(message)

def display_username_recovery_form(sheet):
    st.subheader("🆔 Recover Username")
    email = st.text_input("Enter your email")
    if st.button("Recover Username"):
        success, message = recover_username(email, sheet)
        st.success(message) if success else st.error(message)

def show_account_recovery(sheet):
    tab1, tab2 = st.tabs(["🔑 Reset Password", "🆔 Recover Username"])
    with tab1:
        display_password_reset_form(sheet)
    with tab2:
        display_username_recovery_form(sheet)
