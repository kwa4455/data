import streamlit as st
import streamlit.components.v1 as cp
from modules.authentication import require_role

def show():
    require_role(["admin", "collector", "editor",supervisor])

    # Set defaults
    if "theme" not in st.session_state:
        st.session_state.theme = "Light"
    if "font_size" not in st.session_state:
        st.session_state.font_size = "Medium"

    # Sidebar - Appearance Controls
    st.sidebar.header("🎨 Appearance Settings")

    theme_choice = st.sidebar.selectbox(
        "Choose Theme",
        ["Light", "Dark", "Blue", "Green", "Purple"],
        index=["Light", "Dark", "Blue", "Green", "Purple"].index(st.session_state.theme)
    )
    st.session_state.theme = theme_choice

    font_choice = st.sidebar.radio("Font Size", ["Small", "Medium", "Large"],
                                   index=["Small", "Medium", "Large"].index(st.session_state.font_size))
    st.session_state.font_size = font_choice

    if st.sidebar.button("🔄 Reset to Defaults"):
        st.session_state.theme = "Light"
        st.session_state.font_size = "Medium"
        st.success("Reset to Light theme and Medium font!")
        st.rerun()

    themes = {
        "Light": {"background": "linear-gradient(135deg, #e0f7fa, #ffffff)", "text": "#004d40", "button": "#00796b", "hover": "#004d40", "input_bg": "#ffffff"},
        "Dark": {"background": "linear-gradient(135deg, #263238, #37474f)", "text": "#e0f2f1", "button": "#26a69a", "hover": "#00897b", "input_bg": "#37474f"},
        "Blue": {"background": "linear-gradient(135deg, #e3f2fd, #90caf9)", "text": "#0d47a1", "button": "#1e88e5", "hover": "#1565c0", "input_bg": "#ffffff"},
        "Green": {"background": "linear-gradient(135deg, #dcedc8, #aed581)", "text": "#33691e", "button": "#689f38", "hover": "#558b2f", "input_bg": "#ffffff"},
        "Purple": {"background": "linear-gradient(135deg, #f3e5f5, #ce93d8)", "text": "#4a148c", "button": "#8e24aa", "hover": "#6a1b9a", "input_bg": "#ffffff"},
    }

    font_map = {"Small": "14px", "Medium": "16px", "Large": "18px"}
    theme = themes[st.session_state.theme]
    font_size = font_map[st.session_state.font_size]

    def generate_css(theme: dict, font_size: str) -> str:
        return f"""<style> ... (same CSS content as before) ... </style>"""

    st.markdown(generate_css(theme, font_size), unsafe_allow_html=True)

    with st.sidebar:
        try:
            st.image("epa-logo.png", width=150)
        except:
            pass

        st.markdown("### 🧑‍💻 Developer Information")
        st.markdown("""
        - **Developed by:** Clement Mensah Ackaah  
        - **Email:** clement.ackaah@epa.gov.gh / clementackaah70@gmail.com  
        - **GitHub:** [Visit GitHub](https://github.com/kwa4455)  
        - **LinkedIn:** [Visit LinkedIn](https://www.linkedin.com/in/clementmensahackaah)  
        - **Project Repo:** [Air Quality Dashboard](https://github.com/kwa4455/air-quality-analysis-dashboard)
        """)

    cp.html(f"""<div style="...">{'👋 Welcome to the Air Quality Dashboard!'}</div>""", height=120)

    st.markdown("## 🌍 About the Dashboard")
    st.markdown("""
    ### 📈 Air Quality Analysis Tool
    ... (same dashboard info as before) ...
    """)

    st.markdown("---")
    st.markdown("## 📚 Understanding AQI (Air Quality Index)")
    st.markdown(f"""<div class="aqi-card"> ... AQI education content ... </div>""", unsafe_allow_html=True)

    levels = {
        ...  # same AQI level dictionary
    }
    for title, desc in levels.items():
        with st.expander(title):
            st.markdown(f"<div><b>{desc}</b></div>", unsafe_allow_html=True)

    st.markdown(f"""<div class="aqi-card"> ... AQI table ... </div>""", unsafe_allow_html=True)

    st.markdown("### 🔗 Quick Links")
    st.markdown(f"""<div style="..."> ... links ... </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="instruction-card">', unsafe_allow_html=True)
    st.markdown("### 📋 How to Upload Data")
    st.markdown(""" ... (instructions content) ... """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    prompt = st.chat_input("Say something and/or attach an image", accept_file=True, file_type=["jpg", "jpeg", "png"])
    if prompt and prompt.text:
        st.markdown(prompt.text)
    if prompt and prompt["files"]:
        st.image(prompt["files"][0])

    sentiment_mapping = ["one", "two", "three", "four", "five"]
    selected = st.feedback("stars")
    if selected is not None:
        st.markdown(f"You selected {sentiment_mapping[selected]} star(s).")

    st.success("📢 New updates coming soon! Stay tuned for enhanced analysis features and interactive visualizations.")

    st.markdown("""
        <hr style="margin-top: 40px; margin-bottom:10px">
        <div style='text-align: center; color: grey; font-size: 0.9em;'>
            © 2025 EPA Ghana · Developed by Clement Mensah Ackaah 🦺 · Built with 😍 using Streamlit | 
            <a href="mailto:clement.ackaah@epa.gov.gh">Contact Support</a>
        </div>
    """, unsafe_allow_html=True)
