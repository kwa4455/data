import streamlit as st
from modules.authentication import require_role

def show():
    require_role(["admin", "collector", "editor", "supervisor"])

    # Language selection
    lang = st.selectbox("🌐 Select Language / Pɛ kasa", ["English", "Twi"])

    # Translations
    text = {
        "title": {"English": "📋 🛖 Home", "Twi": "📋 🛖 Fie"},
        "welcome": {
            "English": "👋 Welcome! We're excited to have you here. Use the navigation below to get started.",
            "Twi": "👋 Akwaaba! Yɛpɛ sɛ wopɛ sɛ woyɛ adwuma no. Fa akwan no so na yɛ ase."
        },
        "nav_instruction": {
            "English": "🔍 Navigate Based on Your Role",
            "Twi": "🔍 Fa w'apɛsɛmenmu so kɔ krataa no so"
        },
        "note": {
            "English": "Only the pages for which you have authorization will be available for access.",
            "Twi": "Wubenya kwan kɔ nkrataa a wunya ho kwan nkutoo so."
        },
        "tooltips": {
            "home": {"English": "Landing page after login", "Twi": "Fie krataa a ɛda kan"},
            "entry": {"English": "Submit new data entries", "Twi": "To data foforɔ so"},
            "edit": {"English": "Edit or update submitted entries", "Twi": "Sesa data a wɔde too hɔ"},
            "calc": {"English": "Calculate PM2.5 concentrations", "Twi": "Bɔ PM2.5 dodow"},
            "review": {"English": "Supervisors can review and approve entries", "Twi": "Supervisors betumi ahwɛ nsɛm no"},
            "admin": {"English": "Admin-only access to manage users", "Twi": "Admins nkutoo betumi adi dwuma wɔ ho"}
        },
        "footer": {
            "English": "📢 New updates coming soon! Stay tuned for enhanced analysis features and interactive visualizations.",
            "Twi": "📢 Nsɛm foforo reba ntɛm! Twɛn nhyehyɛe ne nhwɛanim foforo."
        },
        "copyright": {
            "English": "© 2025 EPA Ghana · Developed by Clement Mensah Ackaah 🦺 · Built with 😍 using Streamlit |",
            "Twi": "© 2025 EPA Ghana · Clement Mensah Ackaah na ɔbɔɔ ho 🦺 · Yɛde 😍 yɛɛ no wɔ Streamlit so |"
        },
        "contact": {"English": "Contact Support", "Twi": "Frɛ Mmoafoɔ"}
    }

    # Custom CSS
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
            .home-title {
                font-size: 2.3em;
                font-weight: 800;
                margin-bottom: 0;
            }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown(f"""
        <div style='text-align: center;'>
            <div class='home-title'>{text['title'][lang]}</div>
            <p style='color: grey;'>{text['welcome'][lang]}</p>
        </div>
        <hr>
    """, unsafe_allow_html=True)

    # Navigation
    st.markdown(f"### {text['nav_instruction'][lang]}")
    st.markdown(f"""
        <ul>
            <li class='nav-item' title="{text['tooltips']['home'][lang]}">🏛️ <strong>{text['title'][lang]}</strong></li>
            <li class='nav-item' title="{text['tooltips']['entry'][lang]}">🛰️ <strong>Data Entry Form</strong></li>
            <li class='nav-item' title="{text['tooltips']['edit'][lang]}">🌡️ <strong>Edit Data Form</strong></li>
            <li class='nav-item' title="{text['tooltips']['calc'][lang]}">🧪 <strong>PM Calculator</strong></li>
            <li class='nav-item' title="{text['tooltips']['review'][lang]}">📖 <strong>Supervisor & Review Section</strong></li>
            <li class='nav-item' title="{text['tooltips']['admin'][lang]}">⚙️ <strong>Administrative Panel</strong></li>
        </ul>
        <p><em>{text['note'][lang]}</em></p>
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
    st.success(text["footer"][lang])

    # Footer
    st.markdown(f"""
        <hr style="margin-top: 40px; margin-bottom:10px">
        <div class='footer' style='text-align: center; color: grey; font-size: 0.9em;'>
            {text['copyright'][lang]}
            <a href="mailto:clement.ackaah@epa.gov.gh">{text['contact'][lang]}</a>
        </div>
    """, unsafe_allow_html=True)
