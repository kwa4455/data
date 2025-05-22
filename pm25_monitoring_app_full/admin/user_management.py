import streamlit as st
from modules.authentication import require_role
from modules.user_utils import (
    spreadsheet,
    approve_user,
    delete_registration_request,
    log_registration_event,
    ensure_reg_requests_sheet
)
from constants import REG_REQUESTS_SHEET

def admin_panel():
    require_role(["admin", "supervisor"])
    st.header("🛠 Admin Panel: Approve Users")

    admin_username = st.session_state.get("username", "unknown_admin")

    # -- Section 1: Pending Requests --
    st.subheader("📥 Pending Registration Requests")
    sheet = ensure_reg_requests_sheet(spreadsheet)
    requests = sheet.get_all_records()

    if not requests:
        st.info("No pending registration requests.")
    else:
        for user in requests:
            with st.expander(f"Request from {user['Username']}"):
                st.write(f"Name: {user['Full Name']}")
                st.write(f"Email: {user['Email']}")
                st.write(f"Requested Role: {user['Role']}")

                assigned_role = st.selectbox(
                    f"Assign Role to {user['Username']}",
                    ["viewer", "collector", "editor", "admin"],
                    index=["viewer", "collector", "editor", "admin"].index(user["Role"]),
                    key=f"role_{user['Username']}"
                )

                if st.button(f"✅ Approve {user['Username']}", key=user["Username"]):
                    user["Role"] = assigned_role
                    msg = approve_user(user, admin_username, spreadsheet)
                    st.success(msg)
                    st.experimental_rerun()

    # -- Section 2: Delete Approved Users --
    st.subheader("🗑 Manage Existing Users")
    users_sheet = ensure_users_sheet(spreadsheet)
    approved_users = users_sheet.get_all_records()

    usernames = [user["Username"] for user in approved_users]

    if usernames:
        user_to_delete = st.selectbox("Select a user to delete:", usernames)
        if st.button("🚨 Delete Selected User"):
            deleted = delete_user(user_to_delete, spreadsheet)
            if deleted:
                log_registration_event(user_to_delete, "deleted", admin_username, spreadsheet)
                st.success(f"User '{user_to_delete}' deleted.")
                st.experimental_rerun()
            else:
                st.error("User not found or could not be deleted.")
    else:
        st.info("No approved users to manage.")
