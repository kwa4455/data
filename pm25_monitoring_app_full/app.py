import streamlit as st
import streamlit_authenticator as stauth
from modules.user_management import login, logout_button
from pages import main, data_entry, edit_records, pm_calculation, admin_tools

st.set_page_config(page_title="PM₂.₅ Monitoring App", layout="wide")

# === Session Login ===
login()

# === Sidebar Menu ===
st.sidebar.title("📋 Navigation")
menu = st.sidebar.radio("Go to", ["🏠 Main Page", "📝 Data Entry", "✏️ Edit Records", "📊 PM Calculation", "🛠 Admin Tools"])

logout_button()

# === Render Pages ===
if menu == "🏠 Main Page":
    main.show()
elif menu == "📝 Data Entry":
    data_entry.show()
elif menu == "✏️ Edit Records":
    edit_records.show()
elif menu == "📊 PM Calculation":
    pm_calculation.show()
elif menu == "🛠 Admin Tools":
    admin_tools.show()
