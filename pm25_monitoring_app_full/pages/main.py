import streamlit as st
from modules.authentication import require_role

def show():
    require_role(["viewer", "editor", "admin"])
    st.title("📊 Main Dashboard")
    st.write("Welcome to the PM₂.₅ monitoring dashboard.")
