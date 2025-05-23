import streamlit as st
from modules.authentication import require_role

def show():
    require_role(["admin", "collector", "editor", "supervisor"])

    # Custom CSS for hover and responsiveness
    st.markdown("""
        <style>
            .nav-item:hover {
                transform: scale(1.02);
                transition: transform 0.2s ease;
                color: #4CAF50 !important;
            }
            .footer a {
                color: inherit;
                text-decoration: underline;
            }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
        <div style='text-align: center;'>
            <h2>📋 🛖 Home</h2>
            <p style='color: grey;'>👋 Welcome!</p>
        </div>
        <hr>
    """, unsafe_allow_html=True)

    # Navigation
    st.markdown("""
        ### 🔍 Navigate Based on Your Role

        <ul>
            <li class='nav-item' title='Landing page after login'>🏛️ <strong>Home</strong></li>
            <li class='nav-item' title='Submit new data entries'>🛰️ <strong>Data Entry Form</strong></li>
            <li class='nav-item' title='Edit or update submitted entries'>🌡️ <strong>Edit Data Form</strong></li>
            <li class='nav-item' title='Calculate PM2.5 concentrations from merged entries'>🧪 <strong>PM Calculator</strong></li>
            <li class='nav-item' title='Supervisors can review and approve entries'>📖 <strong>Supervisor & Review Section</strong></li>
            <li class='nav-item' title='Admin-only access to manage users and configurations'>⚙️ <strong>Administrative Panel</strong></li>
        </ul>

        <p><em>Only the pages for which you have authorization will be available for access.</em></p>
    """, unsafe_allow_html=True)

    # Chat input
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

    # Info box
    st.success("📢 New updates coming soon! Stay tuned for enhanced analysis features and interactive visualizations.")

    # Footer
    st.markdown("""
        <hr style="margin-top: 40px; margin-bottom:10px">
        <div class='footer' style='text-align: center; color: grey; font-size: 0.9em;'>
            © 2025 EPA Ghana · Developed by Clement Mensah Ackaah 🦺 · Built with 😍 using Streamlit | 
            <a href="mailto:clement.ackaah@epa.gov.gh">Contact Support</a>
        </div>
    """, unsafe_allow_html=True)
