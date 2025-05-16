
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import streamlit_authenticator as stauth

# === Setup Google Sheets Client ===
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

# === User Sheet Management ===
def ensure_users_sheet(spreadsheet):
    try:
        sheet = spreadsheet.worksheet("Users")
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet("Users", rows="100", cols="5")
        sheet.append_row(["Username", "Name", "Email", "Password", "Role"])
    return sheet

# === Load Users from Sheet ===
def load_users_from_sheet(sheet):
    users = sheet.get_all_records()
    credentials = {"usernames": {}}
    for user in users:
        credentials["usernames"][user["Username"]] = {
            "name": user["Name"],
            "email": user["Email"],
            "password": user["Password"]
        }
    return credentials

# === Register User ===
def register_user_to_sheet(username, name, email, password, role, sheet):
    users = sheet.get_all_records()
    if any(user["Username"] == username for user in users):
        return False, "Username already exists."

    hashed_pw = stauth.Hasher([password]).generate()[0]
    sheet.append_row([username, name, email, hashed_pw, role])
    return True, "User registered successfully."

# === Update User Details ===
def update_user_details_in_sheet(username, new_name=None, new_email=None, new_password=None, sheet=None):
    data = sheet.get_all_values()
    for i, row in enumerate(data):
        if i == 0: continue  # Skip header
        if row[0] == username:
            if new_name:
                data[i][1] = new_name
            if new_email:
                data[i][2] = new_email
            if new_password:
                data[i][3] = stauth.Hasher([new_password]).generate()[0]
            sheet.update(f"A{i+1}:E{i+1}", [data[i]])
            return True
    return False

# === Reset Password (Role-based: only for non-admins) ===
def reset_password(email, new_password, sheet):
    data = sheet.get_all_values()
    for i, row in enumerate(data):
        if i == 0: continue  # Skip header
        if row[2] == email:
            if row[4].lower() == "admin":
                return False, "❌ Admin users cannot reset password via this form."
            hashed_pw = stauth.Hasher([new_password]).generate()[0]
            data[i][3] = hashed_pw
            sheet.update(f"A{i+1}:E{i+1}", [data[i]])
            return True, "✅ Password reset successfully."
    return False, "❌ Email not found."

# === Recover Username (Role-based message enhancement) ===
def recover_username(email, sheet):
    users = sheet.get_all_records()
    for user in users:
        if user["Email"] == email:
            return True, f"✅ Your username is: {user['Username']} (Role: {user['Role']})"
    return False, "❌ Email not found."

# === Role-based Access Control ===
def require_role(allowed_roles):
    role = st.session_state.get("role")
    if not role:
        st.error("🚫 You must be logged in to view this page.")
        st.stop()
    if role.lower() not in [r.lower() for r in allowed_roles]:
        st.error(f"🚫 Access denied for role: {role}")
        st.stop()

# === UI Components ===
def display_password_reset_form(sheet):
    st.subheader("🔑 Reset Password")
    email = st.text_input("Enter your email")
    new_password = st.text_input("Enter new password", type="password")
    if st.button("Reset Password"):
        success, message = reset_password(email, new_password, sheet)
        st.success(message) if success else st.error(message)

def display_username_recovery_form(sheet):
    st.subheader("🆔 Recover Username")
    email = st.text_input("Enter your email")
    if st.button("Recover Username"):
        success, message = recover_username(email, sheet)
        st.success(message) if success else st.error(message)


def login(sheet):
    users = load_users_from_sheet(sheet)
    authenticator = stauth.Authenticate(
        users,
        "pm25_app",
        "abcdef",
        cookie_expiry_days=1
    )
    name, auth_status, username = authenticator.login("Login", "main")

    if auth_status is False:
        st.error("❌ Incorrect username or password")
    elif auth_status is None:
        st.warning("🕒 Please enter your credentials")
    elif auth_status:
        st.session_state["name"] = name
        st.session_state["username"] = username
        st.session_state["role"] = get_user_role(username, sheet)
        return True, authenticator
    return False, None

def logout_button(authenticator):
    authenticator.logout("Logout", "sidebar")

def get_user_role(username, sheet):
    users = sheet.get_all_records()
    for user in users:
        if user["Username"] == username:
            return user["Role"]
    return "viewer"  # fallback default
