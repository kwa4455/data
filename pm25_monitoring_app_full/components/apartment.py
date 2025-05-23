import streamlit as st
import streamlit.components.v1 as cp
from modules.authentication import require_role

def show():
    require_role(["admin", "collector", "editor", "supervisor"])

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

    st.markdown("## 🌍 About the Dashboard")
    st.markdown("""
    ### 📈 Air Quality Analysis Tool
    Upload, visualize, and monitor air quality data collected from:

    - 🏛️ Reference Grade Instruments
    - 🛰️ Quant AQ Monitors
    - 🌡️ Gravimetric Samplers
    - 🧪 Clarity Sensors
    - 📟 AirQo Devices

    Get insights, analyze seasonal trends, and make informed decisions!
    """)

    # AQI Education Section
    st.markdown("---")
    st.markdown("## 📚 Understanding AQI (Air Quality Index)")

    st.markdown(f"""
    <div class="aqi-card">
    <p>The <strong>Air Quality Index (AQI)</strong> measures the quality of air and provides important health-related information. It helps you understand when to take action to protect your health!</p>

    <h4>🧮 How AQI is Calculated</h4>
    <ul>
    <li>Each major pollutant (PM₂.₅, PM₁₀, O₃, CO, SO₂, NO₂) gets its own index.</li>
    <li>The final AQI is the <strong>highest</strong> individual pollutant index.</li>
    </ul>

    <h4>🔢 Basic AQI Formula</h4>
    <p style="text-align:center;">
    <em>
    AQI = ((I<sub>high</sub> - I<sub>low</sub>) / (C<sub>high</sub> - C<sub>low</sub>)) × (C - C<sub>low</sub>) + I<sub>low</sub>
    </em>
    </p>
    </div>
    """, unsafe_allow_html=True)

    levels = {
        "📗 Good (0-50)": "Air quality is satisfactory and poses little or no risk.",
        "📒 Moderate (51-100)": "Air quality is acceptable; some pollutants may be a concern for a small number of sensitive individuals.",
        "📙 Unhealthy for Sensitive Groups (101-150)": "Members of sensitive groups may experience health effects. The general public is not likely to be affected.",
        "📕 Unhealthy (151-200)": "Everyone may begin to experience health effects; sensitive groups may experience more serious effects.",
        "📓 Very Unhealthy (201-300)": "Health warnings of emergency conditions. The entire population is more likely to be affected.",
        "📘 Hazardous (301-500)": "Health alert: everyone may experience more serious health effects. Emergency conditions."
    }

    for title, desc in levels.items():
        with st.expander(title):
            st.markdown(f"<div><b>{desc}</b></div>", unsafe_allow_html=True)

    # AQI Table
    st.markdown(f"""
    <div class="aqi-card">
    <h4>📊 AQI Categories Summary</h4>
    <table class="aqi-table">
    <thead>
    <tr><th>AQI Range</th><th>Category</th><th>Health Effects</th></tr>
    </thead>
    <tbody>
    <tr><td>0-50</td><td>Good</td><td>Little or no risk.</td></tr>
    <tr><td>51-100</td><td>Moderate</td><td>Acceptable, slight concern for sensitive individuals.</td></tr>
    <tr><td>101-150</td><td>Unhealthy for Sensitive Groups</td><td>Health effects possible for sensitive groups.</td></tr>
    <tr><td>151-200</td><td>Unhealthy</td><td>Everyone may experience health effects.</td></tr>
    <tr><td>201-300</td><td>Very Unhealthy</td><td>Health warnings for the entire population.</td></tr>
    <tr><td>301-500</td><td>Hazardous</td><td>Serious health effects for everyone.</td></tr>
    </tbody>
    </table>
    </div>
    """, unsafe_allow_html=True)

    # Quick Links
    st.markdown("### 🔗 Quick Links")
    st.markdown(f"""
    <div style="display: flex; gap: 20px; flex-wrap: wrap; justify-content: center;">
        <a href="https://www.epa.gov.gh/" target="_blank" style="padding: 10px 20px; background: {theme["button"]}; color: white; border-radius: 8px; text-decoration: none;">🌐 EPA Website</a>
        <a href="https://www.airnow.gov/aqi/aqi-basics/" target="_blank" style="padding: 10px 20px; background: {theme["hover"]}; color: white; border-radius: 8px; text-decoration: none;">📖 Learn about AQI</a>
    </div>
    """, unsafe_allow_html=True)

    # Instructions
    st.markdown("---")
    st.markdown('<div class="instruction-card">', unsafe_allow_html=True)
    st.markdown("### 📋 How to Upload Data")
    st.markdown("""
    ✅ Please upload your files in the following formats:

    - **Reference Grade Data:** `datetime`, `pm25`, `pm10`, `site`  
    - **Quant AQ Data:** `datetime`, `temp`, `rh`, `pm1`, `pm25`, `pm10`, `site`  
    - **Gravimetric Data:** `date`, `pm25`, `pm10`, `site`  
    - **Clarity Data:** `datetime`, `corrected_pm25`, `pm10`, `site`  
    - **AirQo Data:** `datetime`, `pm25`, `pm10`, `site`  

    ⚠️ Notes:  
    - Use `YYYY-MM-DD HH:MM:SS` format for date/time.  
    - Make sure column names are lowercase and match exactly.  
    - Avoid spaces or special characters in column names.
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

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

    # Footer
    st.markdown(f"""
    <div class="footer">
        Made with ❤️ by Clement Mensah Ackaah
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <hr style="margin-top: 40px; margin-bottom:10px">
        <div style='text-align: center; color: grey; font-size: 0.9em;'>
            © 2025 EPA Ghana · Developed by Clement Mensah Ackaah 🦺 · Built with 😍 using Streamlit | 
            <a href="mailto:clement.ackaah@epa.gov.gh">Contact Support</a>
        </div>
    """, unsafe_allow_html=True)
