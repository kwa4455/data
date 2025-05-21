import streamlit as st
from utils.authentication import require_role
from .ui_forms import show_registration_form, show_account_recovery
from .user_utils import load_users_from_sheet, get_user_role,approve_user
from modules.authentication import require_role

require_role(["admin", "supervisor"])

gc = get_gspread_client()
reg_sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(REG_REQUESTS_SHEET)
records = reg_sheet.get_all_records()

if not records:
    st.info("✅ No pending registration requests.")
else:
    for record in records:
        with st.expander(f"📥 {record['username']} - {record['email']}"):
            st.write(f"**Full Name**: {record['name']}")
            st.write(f"**Requested At**: {record['timestamp']}")

            # Role selection dropdown
            selected_role = st.selectbox(
                "Assign Role", ["collector", "editor", "supervisor", "admin"], key=f"role_{record['username']}"
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve", key=f"approve_{record['username']}"):
                    new_user = {
                        "username": record["username"],
                        "email": record["email"],
                        "name": record["name"],
                        "password_hash": record["password_hash"],
                        "role": selected_role  # Use the selected role
                    }
                    approve_user(new_user)
                    delete_registration_request(record["username"])
                    log_registration_event(record["username"], "Approved", st.session_state.get("username"))
                    st.success(f"✅ {record['username']} approved with role '{selected_role}' and added to Users sheet.")
                    st.experimental_rerun()
            with col2:
                if st.button("❌ Reject", key=f"reject_{record['username']}"):
                    delete_registration_request(record["username"])
                    log_registration_event(record["username"], "Rejected", st.session_state.get("username"))
                    st.warning(f"🚫 {record['username']} was rejected.")
                    st.experimental_rerun()
