import streamlit as st
import pandas as pd
from datetime import datetime
from resource import (
    load_data_from_sheet,
    add_data,
    merge_start_stop,
    save_merged_data_to_sheet,
    sheet,
    spreadsheet,
    display_and_merge_data
)
from constants import MERGED_SHEET

def show():
    st.subheader("📥 Data Entry Form")
    
# Streamlit page config

# Inject Google Fonts and custom CSS for glassmorphism and font clarity
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">

    <style>
    /* === Global Font and Text Effects === */
    html, body, [class*="css"]  {
        font-family: 'Poppins', sans-serif;
        text-shadow: 0 1px 2px rgba(0,0,0,0.08);
        color: #1f1f1f;
        background-color: #f4f7fa;
    }

    /* === App Title Styling === */
    .main > div:first-child h1 {
        color: #0a3d62;
        font-size: 2.8rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.15);
        margin-bottom: 0.5rem;
    }

    /* === Sidebar Glass Effect === */
    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(14px) saturate(160%);
        -webkit-backdrop-filter: blur(14px) saturate(160%);
        border: 1px solid rgba(255, 255, 255, 0.25);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.25);
    }

    /* === Sidebar Navigation Styling === */
    section[data-testid="stSidebar"] .st-radio > div {
        background: rgba(255, 255, 255, 0.85);
        color: #000;
        border-radius: 12px;
        padding: 0.4rem 0.6rem;
        margin-bottom: 0.5rem;
        transition: all 0.2s ease;
    }
    section[data-testid="stSidebar"] .st-radio > div:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    /* === Info box styling === */
    .stAlert {
        background-color: rgba(232, 244, 253, 0.9);
        border-left: 6px solid #1f77b4;
        border-radius: 8px;
        padding: 1rem;
    }

    /* === Success message styling === */
    .stSuccess {
        background-color: rgba(230, 255, 230, 0.9);
        border-left: 6px solid #33cc33;
        border-radius: 8px;
        padding: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown(
    """
    <div style='text-align: center;'>
        <h2>📋 Field Monitoring Data Entry</h2>
        <p style='color: grey;'>Use this page to input daily observations, instrument readings, and site information.</p>
    </div>
    <hr>
    """,
    unsafe_allow_html=True
)


# --- Dropdown Options ---
ids = ["", '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
site_id_map = {
    '1': 'Kaneshie First Light',
    '2': 'Tetteh Quarshie',
    '3': 'Achimota',
    '4': 'La',
    '5': 'Mallam Market',
    '6': 'Graphic Road',
    '7': 'Weija',
    '8': 'Kasoa',
    '9': 'Tantra Hill',
    '10': 'Amasaman'
}
officers = ['Obed', 'Clement', 'Peter', 'Ben', 'Mawuli']
wind_directions = ["", "N", "NE", "E", "SE", "S", "SW", "W", "NW"]
weather_conditions = ["", "Sunny", "Cloudy", "Partly Cloudy", "Rainy", "Windy", "Hazy", "Stormy", "Foggy"]

# --- Entry Type Selection ---
entry_type = st.selectbox("📝 Select Entry Type", ["", "START", "STOP"], key="entry_type_selectbox")

if entry_type:
    id_selected = st.selectbox("📌 Select Site ID", ids, key="site_id_selectbox")  # Add unique key here

    # Automatically get and display site name
    site_selected = site_id_map.get(id_selected, "")
    if site_selected:
        st.text_input("📍 Site", value=site_selected, disabled=True, key="site_name_textbox")  # Add unique key here

    officer_selected = st.multiselect("🧑‍🔬 Monitoring Officer(s)", officers, key="officer_selectbox")  # Add unique key here
    driver_name = st.text_input("🧑‍🌾 Driver's Name", key="driver_name_input")  # Add unique key here

# === START Section ===
if entry_type == "START":
    with st.expander("🟢 Start Day Monitoring", expanded=True):
        start_date = st.date_input("📆 Start Date", value=datetime.today(), key="start_date_input")  # Add unique key here
        start_time = st.time_input("⏱️ Start Time", value=datetime.now().time(), key="start_time_input")  # Add unique key here
        start_obs = st.text_area("🧿 First Day Observation", key="start_observation_input")  # Add unique key here

        st.markdown("#### 🌧️ Initial Atmospheric Conditions")
        start_temp = st.number_input("🌡️ Temperature (°C)", step=0.1, key="start_temp_input")  # Add unique key here
        start_rh = st.number_input("🌬️ Relative Humidity (%)", step=0.1, key="start_rh_input")  # Add unique key here
        start_pressure = st.number_input("🧭 Pressure (mbar)", step=0.1, key="start_pressure_input")  # Add unique key here
        start_weather = st.selectbox("🌦️ Weather", weather_conditions, key="start_weather_selectbox")  # Add unique key here
        start_wind_speed = st.text_input("💨 Wind Speed (e.g. 10 km/h)", key="start_wind_speed_input")  # Add unique key here
        start_wind_direction = st.selectbox("🌪️ Wind Direction", wind_directions, key="start_wind_direction_selectbox")  # Add unique key here

        st.markdown("#### ⚙ Initial Sampler Information")
        start_elapsed = st.number_input("⏰ Initial Elapsed Time (min)", step=1, key="start_elapsed_input")  # Add unique key here
        start_flow = st.number_input("🧯 Initial Flow Rate (L/min)", step=0.1, key="start_flow_input")  # Add unique key here

        if st.button("✅ Submit Start Day Data", key="start_submit_button"):  # Add unique key here
            if all([id_selected, site_selected, officer_selected, driver_name]):
                start_row = [
                    "START", id_selected, site_selected, ", ".join(officer_selected), driver_name,
                    start_date.strftime("%Y-%m-%d"), start_time.strftime("%H:%M:%S"),
                    start_temp, start_rh, start_pressure, start_weather,
                    start_wind_speed, start_wind_direction,
                    start_elapsed, start_flow, start_obs
                ]
                add_data(start_row, st.session_state.username)  # Pass username here
                st.success("✅ Start day data submitted successfully!")
            else:
                st.error("⚠ Please complete all required fields before submitting.")

# === STOP Section ===
elif entry_type == "STOP":
    with st.expander("🔴 Stop Day Monitoring", expanded=True):
        stop_date = st.date_input("📆 Stop Date", value=datetime.today(), key="stop_date_input")  # Add unique key here
        stop_time = st.time_input("⏱️ Stop Time", value=datetime.now().time(), key="stop_time_input")  # Add unique key here
        stop_obs = st.text_area("🧿 Final Day Observation", key="stop_observation_input")  # Add unique key here

        st.markdown("#### 🌧️ Final Atmospheric Conditions")
        stop_temp = st.number_input("🌡️ Final Temperature (°C)", step=0.1, key="stop_temp_input")  # Add unique key here
        stop_rh = st.number_input("🌬️ Final Relative Humidity (%)", step=0.1, key="stop_rh_input")  # Add unique key here
        stop_pressure = st.number_input("🧭 Final Pressure (mbar)", step=0.1, key="stop_pressure_input")  # Add unique key here
        stop_weather = st.selectbox("🌦️ Final Weather", weather_conditions, key="stop_weather_selectbox")  # Add unique key here
        stop_wind_speed = st.text_input("💨 Final Wind Speed (e.g. 12 km/h)", key="stop_wind_speed_input")  # Add unique key here
        stop_wind_direction = st.selectbox("🌪️ Final Wind Direction", wind_directions, key="stop_wind_direction_selectbox")  # Add unique key here

        st.markdown("#### ⚙ Final Sampler Information")
        stop_elapsed = st.number_input("⏰ Final Elapsed Time (min)", step=1, key="stop_elapsed_input")  # Add unique key here
        stop_flow = st.number_input("🧯 Final Flow Rate (L/min)", step=0.1, key="stop_flow_input")  # Add unique key here

        if st.button("✅ Submit Stop Day Data", key="stop_submit_button"):  # Add unique key here
            if all([id_selected, site_selected, officer_selected, driver_name]):
                stop_row = [
                    "STOP", id_selected, site_selected, ", ".join(officer_selected), driver_name,
                    stop_date.strftime("%Y-%m-%d"), stop_time.strftime("%H:%M:%S"),
                    stop_temp, stop_rh, stop_pressure, stop_weather,
                    stop_wind_speed, stop_wind_direction,
                    stop_elapsed, stop_flow, stop_obs
                ]
                add_data(stop_row, st.session_state.username)  # Pass username here
                st.success("✅ Stop day data submitted successfully!")
            else:
                st.error("⚠ Please complete all required fields before submitting.")

# Show Submitted Records
if st.checkbox("📖 Show Submitted Monitoring Records", key="submitted_records_checkbox"):
    try:
        df = load_data_from_sheet(sheet)
        df_saved = display_and_merge_data(df, spreadsheet, MERGED_SHEET)
        st.dataframe(df_saved, use_container_width=True)
    except Exception as e:
        st.warning(f"⚠ Could not load Submitted Monitoring Records: {e}")

# --- Footer ---
st.markdown("""
    <hr style="margin-top: 40px; margin-bottom:10px">
    <div style='text-align: center; color: grey; font-size: 0.9em;'>
        © 2025 EPA Ghana · Developed by Clement Mensah Ackaah 🦺 · Built with 😍 using Streamlit
    </div>
""", unsafe_allow_html=True)
