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

    # Fetch the registration sheet
    reg_sheet = ensure_reg_requests_sheet(spreadsheet)
    records = reg_sheet.get_all_records()

    # If no records, show a message and return
    if not records:
        st.info("✅ No pending registration requests.")
        return

    # Iterate over the registration records
    for idx, record in enumerate(records):
        # Safe access with get() method to prevent KeyErrors
        with st.expander(f"📥 {record.get('username', 'Unknown')} - {record.get('email', 'Unknown')}"):
            st.write(f"**Full Name**: {record.get('name', 'N/A')}")
            st.write(f"**Requested At**: {record.get('timestamp', 'N/A')}")

            selected_role = st.selectbox(
                "Assign Role",
                ["collector", "editor", "supervisor", "admin"],
                key=f"role_{record.get('username', 'unknown')}_{idx}"
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ Approve", key=f"approve_{record.get('username', 'unknown')}_{idx}"):
                    try:
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
                        st.success(f"✅ {record['username']} approved with role '{selected_role}'.")
                    except Exception as e:
                        st.error(f"❌ An error occurred: {str(e)}")
                    st.experimental_rerun()

            with col2:
                if st.button("❌ Reject", key=f"reject_{record.get('username', 'unknown')}_{idx}"):
                    try:
                        delete_registration_request(record["username"])
                        log_registration_event(record["username"], "Rejected", st.session_state.get("username"))
                        st.warning(f"🚫 {record['username']} was rejected.")
                    except Exception as e:
                        st.error(f"❌ An error occurred: {str(e)}")
                    st.experimental_rerun()
