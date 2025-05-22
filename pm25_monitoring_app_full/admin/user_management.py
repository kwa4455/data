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

    # Get admin username from session
    admin_username = st.session_state.get("username", "unknown_admin")

    # Load pending registration requests
    sheet = ensure_reg_requests_sheet(spreadsheet)
    requests = sheet.get_all_records()

    if not requests:
        st.info("No pending registration requests.")
        return

    for user in requests:
        with st.expander(f"Request from {user['Username']}"):
            st.write(f"Name: {user['Name']}")
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
                st.experimental_rerun()  # Refresh UI

            
