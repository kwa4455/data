import streamlit as st
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

from modules.authentication import require_role
from modules.user_utils import (
    approve_user,
    delete_registration_request,
    log_registration_event,
)
from constants import SPREADSHEET_ID, REG_REQUESTS_SHEET


# === Google Sheets Setup ===
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
spreadsheet = client.open_by_key(SPREADSHEET_ID)


def admin_panel():
    require_role(["admin", "supervisor"])

    reg_sheet = spreadsheet.worksheet(REG_REQUESTS_SHEET)
    records = reg_sheet.get_all_records()

    if not records:
        st.info("✅ No pending registration requests.")
        return

    for idx, record in enumerate(records):
        with st.expander(f"📥 {record['username']} - {record['email']}"):
            st.write(f"**Full Name**: {record['name']}")
            st.write(f"**Requested At**: {record.get('timestamp', 'N/A')}")

            selected_role = st.selectbox(
                "Assign Role",
                ["collector", "editor", "supervisor", "admin"],
                key=f"role_{record['username']}_{idx}"
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ Approve", key=f"approve_{record['username']}_{idx}"):
                    new_user = {
                        "username": record["username"],
                        "email": record["email"],
                        "name": record["name"],
                        "password_hash": record["password_hash"],  # or "password"
                        "role": selected_role
                    }
                    approve_user(new_user)
                    delete_registration_request(record["username"])
                    log_registration_event(record["username"], "Approved", st.session_state.get("username"))
                    st.success(f"✅ {record['username']} approved with role '{selected_role}'.")
                    st.experimental_rerun()

            with col2:
                if st.button("❌ Reject", key=f"reject_{record['username']}_{idx}"):
                    delete_registration_request(record["username"])
                    log_registration_event(record["username"], "Rejected", st.session_state.get("username"))
                    st.warning(f"🚫 {record['username']} was rejected.")
                    st.experimental_rerun()
