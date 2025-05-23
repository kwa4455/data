import streamlit as st
from modules.authentication import require_role

def show():
    require_role(["admin", "collector", "editor", "supervisor"])

    # Language selection
    lang = st.selectbox("🌐 Select Language / Pɛ kasa", ["English", "Twi"])

    # Multilingual dictionary
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
        },
        "tooltips": {
            "data_entry": {
                "English": "Collector: Enter raw field data",
                "Twi": "Collector: Kɔ na kɔhyɛ mfidie mu data"
            },
            "edit_data": {
                "English": "Editor: Modify existing data entries",
                "Twi": "Editor: Sesa data a ɛwɔ hɔ dedaw"
            },
            "pm_calc": {
                "English": "Calculate PM₂.₅ concentration from sample volume and mass",
                "Twi": "Bɔ PM₂.₅ a ɛwɔ sample ne dodow so"
            },
            "supervisor": {
                "English": "Supervisor: Review submissions and provide feedback",
                "Twi": "Supervisor: Hwɛ nsɛm a wɔde too hɔ na ma adwenkyerɛ"
            },
            "admin": {
                "English": "Admin: Manage users, permissions, and system settings",
                "Twi": "Admin: Hwɛ nnipa, mmoa ho kwan, ne nsɛnhyɛsoɔ"
            }
        }
    }

    # Header
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

    # Pages with tooltips
    st.markdown(f"""
        <ul style="line-height: 2;">
            <li>🏛️ Home</li>
            <li>🛰️ Data entry Form 
                <span title="{text['tooltips']['data_entry'][lang]}">🧍‍♂️</span>
            </li>
            <li>🌡️ Edit Data Form 
                <span title="{text['tooltips']['edit_data'][lang]}">✏️</span>
            </li>
            <li>🧪 PM Calculator 
                <span title="{text['tooltips']['pm_calc'][lang]}">⚖️</span>
            </li>
            <li>📖 Supervisor and Review Section 
                <span title="{text['tooltips']['supervisor'][lang]}">🔍</span>
            </li>
            <li>⚙️ Admin Panel 
                <span title="{text['tooltips']['admin'][lang]}">🛠️</span>
            </li>
        </ul>
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

    # Info
    st.success(text["footer"][lang])

    # Footer
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
