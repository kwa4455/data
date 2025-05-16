import streamlit as st
import streamlit_authenticator as stauth

from modules.user_management import login, logout_button, ensure_users_sheet
from pages import main, data_entry, edit_records, pm_calculation, admin
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# === Setup Streamlit Page ===
st.set_page_config(page_title="PM₂.₅ Monitoring App", layout="wide")

# === Google Sheets Auth ===
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

# === Authenticate User ===
logged_in, authenticator = login(users_sheet)
if not logged_in:
    st.stop()

# === Sidebar Navigation ===
st.sidebar.title("📋 Navigation")
menu = st.sidebar.radio("Go to", [
    "🏠 Main Page", 
    "📝 Data Entry", 
    "✏️ Edit Records", 
    "📊 PM Calculation", 
    "🛠 Admin"
])

# === Logout Button ===
logout_button(authenticator)

# === Page Routing ===
if menu == "🏠 Main Page":
    main.show()
elif menu == "📝 Data Entry":
    data_entry.show()
elif menu == "✏️ Edit Records":
    edit_records.show()
elif menu == "📊 PM Calculation":
    pm_calculation.show()
elif menu == "🛠 Admin":
    from modules.user_management import require_role
    require_role(["admin"])  # 🚫 Restrict access
    admin.show()
