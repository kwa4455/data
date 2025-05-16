# admin_page.py
import streamlit as st

def show():
    st.title("🛠 Admin")
    st.write("This page includes tools for user management and data export.")

    # Test content to verify display
    if st.button("Test Button"):
        st.success("Button works!")
