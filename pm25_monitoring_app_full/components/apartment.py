import streamlit as st
import streamlit.components.v1 as cp
from modules.authentication import require_role

def show():
    require_role(["admin", "collector", "editor", "supervisor"])

     st.markdown(
        """
        <div style='text-align: center;'>
            <h2>📋 🛖 Home </h2>
            <p style='color: grey;'>Use this page to input daily observations, instrument readings, and site information.</p>
        </div>
        <hr>
        """,
        unsafe_allow_html=True
    )
    st.markdown("""
    
    Please navigate through the following pages according to your assigned role:

    - 🏛️ Home
    - 🛰️ Data entry Form
    - 🌡️ Edit Data Form
    - 🧪 PM Calculator
    - 📖 Supervisor and Review Section
    - ⚙️ Admin Panel

    Only the pages for which you have authorization will be available for access.
    """)


    
    # Chat Input
    st.markdown("---")
    prompt = st.chat_input("Say something and/or attach an image", accept_file=True, file_type=["jpg", "jpeg", "png"])
    if prompt and prompt.text:
        st.markdown(prompt.text)
    if prompt and prompt["files"]:
        st.image(prompt["files"][0])

    # Feedback
    sentiment_mapping = ["one", "two", "three", "four", "five"]
    selected = st.feedback("stars")
    if selected is not None:
        st.markdown(f"You selected {sentiment_mapping[selected]} star(s).")

    # Info
    st.success("📢 New updates coming soon! Stay tuned for enhanced analysis features and interactive visualizations.")

    

    st.markdown("""
        <hr style="margin-top: 40px; margin-bottom:10px">
        <div style='text-align: center; color: grey; font-size: 0.9em;'>
            © 2025 EPA Ghana · Developed by Clement Mensah Ackaah 🦺 · Built with 😍 using Streamlit | 
            <a href="mailto:clement.ackaah@epa.gov.gh">Contact Support</a>
        </div>
    """, unsafe_allow_html=True)
