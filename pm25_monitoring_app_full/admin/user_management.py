import streamlit as st
from modules.authentication import require_role
from modules.user_utils import (
    spreadsheet,
    approve_user,
    ensure_users_sheet,
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
                    st.session_state.user_approved = user["Username"]  # Flag for approval
                    st.session_state.approval_message = msg  # Store the message to display later

    # -- Section 2: Delete Approved Users --
    st.subheader("🗑 Manage Existing Users")
    users_sheet = ensure_users_sheet(spreadsheet)
    approved_users = users_sheet.get_all_records()

    usernames = [user["Username"] for user in approved_users]

    if usernames:
        user_to_delete = st.selectbox("Select a user to delete:", usernames)

        # Ask for confirmation before deleting
        confirm_delete = st.radio(
            "Are you sure you want to delete this user?",
            options=["Yes", "No"],
            index=1,  # Default to "No"
            key=f"confirm_delete_{user_to_delete}"
        )

        if confirm_delete == "Yes" and st.button("🚨 Delete Selected User"):
            # Proceed to delete the user
            deleted_from_users = delete_user_from_users_sheet(user_to_delete, users_sheet)
            deleted_from_requests = delete_registration_request(user_to_delete, spreadsheet)
            
            if deleted_from_users and deleted_from_requests:
                log_registration_event(user_to_delete, "deleted", admin_username, spreadsheet)
                st.success(f"User '{user_to_delete}' has been successfully deleted.")
                st.session_state.user_deleted = user_to_delete  # Flag for deletion
                st.session_state.deletion_message = f"User '{user_to_delete}' deleted successfully."

    else:
        st.info("No approved users to manage.")

    # Conditional display based on session state
    if "user_approved" in st.session_state:
        st.success(f"User '{st.session_state.user_approved}' has been approved.")
        del st.session_state.user_approved  # Clear after showing the message

    if "user_deleted" in st.session_state:
        st.success(st.session_state.deletion_message)
        del st.session_state.user_deleted  # Clear after showing the message

def delete_user_from_users_sheet(username, users_sheet):
    """
    Function to delete the user from the users sheet.
    Returns True if successfully deleted, otherwise False.
    """
    data = users_sheet.get_all_values()
    for i, row in enumerate(data):
        if i == 0:  # Skip header row
            continue
        if row[0] == username:  # If username matches
            users_sheet.delete_rows(i + 1)
            return True
    return False
