import streamlit as st
from modules.authentication import require_role

def show():
    require_role(["admin", "collector", "editor", "supervisor"])

    # Language selector
    lang = st.sidebar.selectbox("🌐 Select Language / Pɛ krataa kasa", ("English", "Twi"))

    # Translations dictionary
    translations = {
        "English": {
            "title": "📋 🛖 Home",
            "welcome": "👋 Welcome!",
            "nav_instruction": "Please navigate through the following pages according to your assigned role:",
            "nav_note": "Only the pages for which you have authorization will be available for access.",
            "new_updates": "📢 New updates coming soon! Stay tuned for enhanced analysis features and interactive visualizations.",
            "footer": "© 2025 EPA Ghana · Developed by Clement Mensah Ackaah 🦺 · Built with 😍 using Streamlit | ",
            "contact_support": "Contact Support",
            "role_tooltips": {
                "admin": "Admin: Full access including user management.",
                "collector": "Collector: Can submit and edit data entries.",
                "editor": "Editor: Can modify existing data.",
                "supervisor": "Supervisor: Reviews and approves data entries."
            }
        },
        "Twi": {
            "title": "📋 🛖 Fie",
            "welcome": "👋 Akwaaba!",
            "nav_instruction": "Fa wo dwumadie mu kwan so kɔ krataa no mu:",
            "nav_note": "Wobɛtumi akɔ nkrataa a wopɛ kwan kɛkɛ so.",
            "new_updates": "📢 Nsɛmma foforo reba ntɛm! Twɛn anɔpa nhyehyɛe foforo ne nsusuiɛ a wɔayɛ no yie.",
            "footer": "© 2025 EPA Ghana · Ɔde Clement Mensah Ackaah 🦺 na ɔyɛɛ no · Yɛde 😍 yɛɛ Streamlit | ",
            "contact_support": "Kɔ so frɛ Yɛboa",
            "role_tooltips": {
                "admin": "Admin: Wunya kwan nyinaa ne sɛ ɔbɛhwɛ wɔn a wɔde wɔn din akɔ mu.",
                "collector": "Collector: Wobɛtumi de data ahyɛ mu anaa asi mu bio.",
                "editor": "Editor: Wobɛtumi asi data a ɛwɔ hɔ mu bio.",
                "supervisor": "Supervisor: Ɔhwɛ ne sɛ ɔbɛhwɛ na wagye data atom."
            }
        }
    }

    t = translations[lang]

    # Header
    st.markdown(
        f"""
        <div style='text-align: center;'>
            <h2>{t['title']}</h2>
            <p style='color: grey;'> {t['welcome']}</p>
        </div>
        <hr>
        """,
        unsafe_allow_html=True
    )

    # Navigation instructions
    st.markdown(f"""
    {t['nav_instruction']}

    - 🏛️ Home
    - 🛰️ Data entry Form <span title="{t['role_tooltips']['collector']}">🛈</span>
    - 🌡️ Edit Data Form <span title="{t['role_tooltips']['editor']}">🛈</span>
    - 🧪 PM Calculator <span title="{t['role_tooltips']['collector']}">🛈</span>
    - 📖 Supervisor and Review Section <span title="{t['role_tooltips']['supervisor']}">🛈</span>
    - ⚙️ Admin Panel <span title="{t['role_tooltips']['admin']}">🛈</span>

    {t['nav_note']}
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
    st.success(t['new_updates'])

    # Footer
    st.markdown(f"""
        <hr style="margin-top: 40px; margin-bottom:10px">
        <div style='text-align: center; color: grey; font-size: 0.9em;'>
            {t['footer']} <a href="mailto:clement.ackaah@epa.gov.gh">{t['contact_support']}</a>
        </div>
    """, unsafe_allow_html=True)
