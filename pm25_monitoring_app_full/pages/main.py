import streamlit as st

def show():
    st.title("🏠 Welcome to PM₂.₅ Monitoring App")
    st.write(f"👤 Logged in as: {st.session_state.get('username')} ({st.session_state.get('role')})")
    st.info("Use the sidebar to navigate through the app.")
