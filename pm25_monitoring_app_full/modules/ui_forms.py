
import streamlit as st
from .user_utils import register_user_request
from .recovery import reset_password, recover_username

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
                success, message = register_user_request(username, name, email, password, role, spreadsheet)
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


def inject_global_css():
    st.markdown("""
        <style>
        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
            background: url("https://images.unsplash.com/photo-1558981285-6f0c94958bb6") no-repeat center center fixed;
            background-size: cover;
            color: #fff;
        }
        </style>
    """, unsafe_allow_html=True)
    st.markdown("""
        <style>
        .stButton>button {
            background-color: #4CAF50; /* Green */
            border: none;
            color: white;
            padding: 15px 32px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
        }
        </style>
    """, unsafe_allow_html=True)
