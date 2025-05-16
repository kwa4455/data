import streamlit as st
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from modules.user_utils import (
    get_all_users,
    update_user_details_in_sheet,
    delete_user_from_sheet,
    ensure_users_sheet
)
from modules.authentication import require_role

# === Authenticate Google Sheets ===
creds_json = st.secrets["GOOGLE_CREDENTIALS"]
creds_dict = json.loads(creds_json)

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
spreadsheet = client.open_by_key(SPREADSHEET_ID)
users_sheet = ensure_users_sheet(spreadsheet)

# === Admin Panel Page ===
def show():
    require_role(["admin"])
    st.title("🔐 Admin Panel - User Management")

    users = get_all_users(users_sheet)

    if not users:
        st.info("No registered users found.")
        return

    st.subheader("👥 Registered Users")
    usernames = [user["Username"] for user in users]
    selected_username = st.selectbox("Select a user", usernames)

    user = next((u for u in users if u["Username"] == selected_username), None)
    if not user:
        st.error("User not found.")
        return

    with st.form("edit_user_form"):
        new_name = st.text_input("Full Name", value=user["Name"])
        new_email = st.text_input("Email", value=user["Email"])
        new_role = st.selectbox("Role", ["admin", "editor", "viewer"], index=["admin", "editor", "viewer"].index(user["Role"]))
        new_password = st.text_input("New Password (leave blank to keep current)", type="password")
        submitted = st.form_submit_button("Update User")

        if submitted:
            success = update_user_details_in_sheet(
                username=user["Username"],
                new_name=new_name,
                new_email=new_email,
                new_password=new_password if new_password else None,
                new_role=new_role,
                sheet=users_sheet
            )
            if success:
                st.success("✅ User details updated.")
            else:
                st.error("❌ Failed to update user.")

    st.divider()
    if st.button("❌ Delete This User"):
        if user["Username"] == st.session_state["username"]:
            st.warning("⚠️ You cannot delete your own account while logged in.")
        else:
            delete_user_from_sheet(user["Username"], users_sheet)
            st.success("✅ User deleted. Refresh page to see changes.")
