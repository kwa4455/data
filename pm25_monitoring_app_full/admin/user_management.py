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
from modules.email_utils import send_email  # <-- Email utility
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

                col1, col2 = st.columns([1, 1])

                with col1:
                    if st.button(f"✅ Approve {user['Username']}", key=f"approve_{user['Username']}"):
                        user["Role"] = assigned_role
                        msg = approve_user(user, admin_username, spreadsheet)
                        st.success(msg)
                        log_registration_event(user["Username"], "approved", admin_username, spreadsheet)

                        send_email(
                            recipient=user["Email"],
                            subject="✅ Your Registration has been Approved",
                            body=f"Hi {user['Full Name']},\n\nYour account has been approved with the role: {assigned_role}.\n\nWelcome aboard!\n\n- Admin Team"
                        )

                        st.session_state.approve_user_rerun = True
                        st.rerun()

                with col2:
                    if st.button(f"❌ Disapprove {user['Username']}", key=f"disapprove_{user['Username']}"):
                        delete_registration_request(user["Username"], spreadsheet)
                        log_registration_event(user["Username"], "disapproved", admin_username, spreadsheet)

                        send_email(
                            recipient=user["Email"],
                            subject="❌ Your Registration has been Disapproved",
                            body=f"Hi {user['Full Name']},\n\nWe regret to inform you that your registration request has been disapproved.\n\nIf you have questions, please contact the admin.\n\n- Admin Team"
                        )

                        st.warning(f"User '{user['Username']}' has been disapproved.")
                        st.session_state.disapprove_user_rerun = True
                        st.rerun()

    # -- Section 2: Delete Approved Users --
    st.subheader("🗑 Manage Existing Users")
    users_sheet = ensure_users_sheet(spreadsheet)
    approved_users = users_sheet.get_all_records()
    usernames = [user["Username"] for user in approved_users]

    if usernames:
        user_to_delete = st.selectbox("Select a user to delete:", usernames)

        confirm_delete = st.radio(
            "Are you sure you want to delete this user?",
            options=["Yes", "No"],
            index=1,
            key=f"confirm_delete_{user_to_delete}"
        )

        if confirm_delete == "Yes" and st.button("🚨 Delete Selected User"):
            deleted_from_users = delete_user_from_users_sheet(user_to_delete, users_sheet)
            deleted_from_requests = delete_registration_request(user_to_delete, spreadsheet)

            if deleted_from_users and deleted_from_requests:
                log_registration_event(user_to_delete, "deleted", admin_username, spreadsheet)
                st.success(f"User '{user_to_delete}' has been successfully deleted.")
                st.session_state.delete_user_rerun = True
                st.rerun()
            else:
                st.error(f"Failed to delete user '{user_to_delete}'.")
        elif confirm_delete == "No":
            st.info(f"User deletion of '{user_to_delete}' was cancelled.")
    else:
        st.info("No approved users to manage.")

def delete_user_from_users_sheet(username, users_sheet):
    data = users_sheet.get_all_values()
    for i, row in enumerate(data):
        if i == 0:
            continue
        if row[0] == username:
            users_sheet.delete_rows(i + 1)
            return True
    return False
