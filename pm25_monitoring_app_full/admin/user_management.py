import streamlit as st

from modules.authentication import require_role
from modules.user_utils import (
    get_gspread_client,
    approve_user,
    delete_registration_request,
    log_registration_event,
    SPREADSHEET_ID,
    REG_REQUESTS_SHEET,
)


def admin_panel():
    require_role(["admin", "supervisor"])

    # Get registration requests from Google Sheet
    gc = get_gspread_client()
    reg_sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(REG_REQUESTS_SHEET)
    records = reg_sheet.get_all_records()

    # No pending requests
    if not records:
        st.info("✅ No pending registration requests.")
        return

    # Loop through and render each request
    for idx, record in enumerate(records):
        with st.expander(f"📥 {record['username']} - {record['email']}"):
            st.write(f"**Full Name**: {record['name']}")
            st.write(f"**Requested At**: {record['timestamp']}")

            # Select role with unique key
            selected_role = st.selectbox(
                "Assign Role",
                ["collector", "editor", "supervisor", "admin"],
                key=f"role_{record['username']}_{idx}"
            )

            col1, col2 = st.columns(2)

            # Approve Button
            with col1:
                if st.button("✅ Approve", key=f"approve_{record['username']}_{idx}"):
                    new_user = {
                        "username": record["username"],
                        "email": record["email"],
                        "name": record["name"],
                        "password_hash": record["password_hash"],
                        "role": selected_role
                    }
                    approve_user(new_user)
                    delete_registration_request(record["username"])
                    log_registration_event(record["username"], "Approved", st.session_state.get("username"))
                    st.success(f"✅ {record['username']} approved with role '{selected_role}' and added to Users sheet.")
                    st.experimental_rerun()

            # Reject Button
            with col2:
                if st.button("❌ Reject", key=f"reject_{record['username']}_{idx}"):
                    delete_registration_request(record["username"])
                    log_registration_event(record["username"], "Rejected", st.session_state.get("username"))
                    st.warning(f"🚫 {record['username']} was rejected.")
                    st.experimental_rerun()
