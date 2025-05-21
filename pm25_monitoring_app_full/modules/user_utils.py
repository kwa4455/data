import streamlit_authenticator as stauth
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
# === Google Sheets Auth ===
creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(st.secrets["SPREADSHEET_ID"])
users_sheet = ensure_users_sheet(spreadsheet)

def ensure_users_sheet(spreadsheet):
    """
    Ensures the 'Users' sheet exists, creates it if not.
    """
    try:
        return spreadsheet.worksheet("Users")
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet("Users", rows="100", cols="5")
        sheet.append_row(["Username", "Name", "Email", "Password", "Role"])
        return sheet

def approve_user(user_data):
    """
    Approves a user by moving their registration data from the registration sheet 
    to the Users sheet with an assigned role. Password is assumed to be hashed already.
    """
    # Ensure the Users sheet exists
    users_sheet = ensure_users_sheet(get_gspread_client().open_by_key(SPREADSHEET_ID))

    # Register the approved user to the Users sheet
    success, message = register_user_to_sheet(
        user_data["username"],
        user_data["name"],
        user_data["email"],
        user_data["password_hash"],  # We assume the password is already hashed
        user_data["role"],  # Role assigned at the time of approval
        users_sheet,
        is_hashed=True  # prevent rehashing
    )
    
    if not success:
        return f"⚠️ Failed to approve user: {message}"
    return f"✅ User {user_data['username']} approved successfully with role '{user_data['role']}'."


def load_users_from_sheet(sheet):
    """
    Loads user data from the Users sheet into a structured dictionary.
    """
    users = sheet.get_all_records()
    credentials = {"usernames": {}}
    for user in users:
        credentials["usernames"][user["Username"]] = {
            "name": user["Name"],
            "email": user["Email"],
            "password": user["Password"]
        }
    return credentials

def register_user_to_sheet(username, name, email, password, role, sheet, is_hashed=False):
    """
    Registers a new user to the Users sheet.
    If the password is not hashed, it hashes the password before storing.
    """
    users = sheet.get_all_records()
    
    # Check if the username or email already exists
    for user in users:
        if user["Username"] == username:
            return False, "⚠️ Username already exists."
        if user["Email"] == email:
            return False, "⚠️ Email already registered."
    
    # Hash the password if not already hashed
    final_pw = password if is_hashed else stauth.Hasher([password]).generate()[0]
    
    # Append the new user
    sheet.append_row([username, name, email, final_pw, role])
    return True, "✅ Registration successful. You can now log in."

def update_user_details_in_sheet(username, new_name=None, new_email=None, new_password=None, new_role=None, sheet=None):
    """
    Updates user details (name, email, password, role) in the Users sheet.
    """
    data = sheet.get_all_values()
    for i, row in enumerate(data):
        if i == 0: continue  # Skip header row
        if row[0] == username:
            if new_name: data[i][1] = new_name
            if new_email: data[i][2] = new_email
            if new_password:
                data[i][3] = stauth.Hasher([new_password]).generate()[0]
            if new_role: data[i][4] = new_role
            sheet.update(f"A{i+1}:E{i+1}", [data[i]])
            return True
    return False



def get_user_role(username, sheet):
    """
    Retrieves the role of a user based on their username from the Users sheet.
    """
    users = sheet.get_all_records()
    for user in users:
        if user["Username"] == username:
            return user["Role"]
    return "viewer"  # Default role if user is not found

def get_all_users(sheet):
    """
    Retrieves all users from the Users sheet.
    """
    return sheet.get_all_records()

def delete_user_from_sheet(username, sheet):
    """
    Deletes a user from the Users sheet by username.
    """
    data = sheet.get_all_values()
    for i, row in enumerate(data):
        if i == 0: continue  # Skip header row
        if row[0] == username:
            sheet.delete_rows(i + 1)
            return True
    return False
