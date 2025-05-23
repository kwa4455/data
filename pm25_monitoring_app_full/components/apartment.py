import streamlit as st
from modules.authentication import require_role

def show():
    require_role(["admin", "collector", "editor", "supervisor"])

    # Language selection
    lang = st.selectbox("🌐 Select Language / Pɛ kasa", ["English", "Twi"])

    text = {
        "title": {
            "English": "📋 🛖 Home",
            "Twi": "📋 🛖 Fie"
        },
        "welcome": {
            "English": "👋 Welcome!",
            "Twi": "👋 Akwaaba!"
        },
        "navigation_instruction": {
            "English": "Please navigate through the following pages according to your assigned role:",
            "Twi": "Mesrɛ, kɔ nkɔfa nkrataa yi so sɛnea w'apɛsɛmenmu te:"
        },
        "footer": {
            "English": "📢 New updates coming soon! Stay tuned for enhanced analysis features and interactive visualizations.",
            "Twi": "📢 Nsɛm foforo reba ntɛm! Twɛn nhyehyɛe foforo ne nhwɛanim a ɛka ho."
        },
        "copyright": {
            "English": "© 2025 EPA Ghana · Developed by Clement Mensah Ackaah 🦺 · Built with 😍 using Streamlit |",
            "Twi": "© 2025 EPA Ghana · Clement Mensah Ackaah na ɔbɔɔ ho 🦺 · Yɛde 😍 yɛɛ no wɔ Streamlit so |"
        },
        "contact": {
            "English": "Contact Support",
            "Twi": "Frɛ Mmoafoɔ"
        }
    }

    st.markdown(
        f"""
        <div style='text-align: center;'>
            <h2>{text['title'][lang]}</h2>
            <p style='color: grey;'>{text['welcome'][lang]}</p>
        </div>
        <hr>
        """,
        unsafe_allow_html=True
    )

    st.markdown(f"**{text['navigation_instruction'][lang]}**")

    st.markdown("""
    - 🏛️ Home
    - 🛰️ Data entry Form &nbsp; ℹ️ <span title='Collector: Enter raw field data'>🧍‍♂️</span>
    - 🌡️ Edit Data Form &nbsp; ℹ️ <span title='Editor: Modify existing data entries'>✏️</span>
    - 🧪 PM Calculator &nbsp; ℹ️ <span title='Calculate PM₂.₅ concentration from sample volume and mass'>⚖️</span>
    - 📖 Supervisor and Review Section &nbsp; ℹ️ <span title='Supervisor: Review submissions and provide feedback'>🔍</span>
    - ⚙️ Admin Panel &nbsp; ℹ️ <span title='Admin: Manage users, permissions, and system settings'>🛠️</span>
    """, unsafe_allow_html=True)

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
    st.success(text["footer"][lang])

    st.markdown(
        f"""
        <hr style="margin-top: 40px; margin-bottom:10px">
        <div style='text-align: center; color: grey; font-size: 0.9em;'>
            {text["copyright"][lang]} 
            <a href="mailto:clement.ackaah@epa.gov.gh">{text["contact"][lang]}</a>
        </div>
        """,
        unsafe_allow_html=True
    )
