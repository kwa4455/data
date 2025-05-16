
import streamlit_authenticator as stauth

def ensure_users_sheet(spreadsheet):
    try:
        return spreadsheet.worksheet("Users")
    except:
        sheet = spreadsheet.add_worksheet("Users", rows="100", cols="5")
        sheet.append_row(["Username", "Name", "Email", "Password", "Role"])
        return sheet

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

import bcrypt
import gspread

def register_user_to_sheet(username, name, email, password, role, sheet):
    users = sheet.get_all_records()

    # Check for duplicate username or email
    for user in users:
        if user["Username"].lower() == username.lower():
            return False, "❌ Username already exists"
        if user["Email"].lower() == email.lower():
            return False, "❌ Email already registered"

    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    sheet.append_row([username, name, email, hashed_pw, role])
    return True, "✅ User registered successfully"


def update_user_details_in_sheet(username, new_name=None, new_email=None, new_password=None, sheet=None):
    data = sheet.get_all_values()
    for i, row in enumerate(data):
        if i == 0: continue
        if row[0] == username:
            if new_name: data[i][1] = new_name
            if new_email: data[i][2] = new_email
            if new_password: data[i][3] = stauth.Hasher([new_password]).generate()[0]
            sheet.update(f"A{i+1}:E{i+1}", [data[i]])
            return True
    return False

def get_user_role(username, sheet):
    users = sheet.get_all_records()
    for user in users:
        if user["Username"] == username:
            return user["Role"]
    return "viewer"
def get_all_users(sheet):
    return sheet.get_all_records()

def delete_user_from_sheet(username, sheet):
    data = sheet.get_all_values()
    for i, row in enumerate(data):
        if i == 0: continue  # Skip header
        if row[0] == username:
            sheet.delete_rows(i + 1)
            return True
    return False
