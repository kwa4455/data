
import streamlit_authenticator as stauth

def reset_password(email, new_password, sheet):
    data = sheet.get_all_values()
    for i, row in enumerate(data):
        if i == 0: continue
        if row[2] == email:
            if row[4].lower() == "admin":
                return False, "❌ Admin users cannot reset password via this form."
            hashed_pw = stauth.Hasher([new_password]).generate()[0]
            data[i][3] = hashed_pw
            sheet.update(f"A{i+1}:E{i+1}", [data[i]])
            return True, "✅ Password reset successfully."
    return False, "❌ Email not found."

def recover_username(email, sheet):
    users = sheet.get_all_records()
    for user in users:
        if user["Email"] == email:
            return True, f"✅ Your username is: {user['Username']} (Role: {user['Role']})"
    return False, "❌ Email not found."
