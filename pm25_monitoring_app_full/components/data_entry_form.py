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
from constants import MERGED_SHEET,MAIN_SHEET
from modules.authentication import require_role


# Insert your CSS here
st.markdown("""
    <style>
    /* --- your CSS --- */
    body, .stApp {
        font-family: 'Poppins', sans-serif;
        transition: all 0.5s ease;
    }
    
    /* Light Mode */
    body.light-mode, .stApp.light-mode {
        background: linear-gradient(135deg, #f8fdfc, #d8f3dc);
        color: #1b4332;
    }
    
    /* Dark Mode */
    body.dark-mode, .stApp.dark-mode {
        background: linear-gradient(135deg, #0e1117, #161b22);
        color: #e6edf3;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(12px);
        border-right: 2px solid #74c69d;
        transition: all 0.5s ease;
    }

    /* Buttons */
    .stButton>button, .stDownloadButton>button {
        background: linear-gradient(135deg, #40916c, #52b788);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.7em 1.5em;
        font-weight: bold;
        font-size: 1rem;
        box-shadow: 0 0 15px #52b788;
        transition: 0.3s ease;
    }
    
    .stButton>button:hover, .stDownloadButton>button:hover {
        background: linear-gradient(135deg, #2d6a4f, #40916c);
        box-shadow: 0 0 25px #74c69d, 0 0 35px #74c69d;
        transform: scale(1.05);
    }

    /* Custom Scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-thumb {
        background: #74c69d;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #52b788;
    }

    /* Glowing Title */
    .glow-text {
        text-align: center;
        font-size: 3em;
        color: #52b788;
        text-shadow: 0 0 5px #52b788, 0 0 10px #52b788, 0 0 20px #52b788;
        margin-bottom: 20px;
    }

    /* Smooth theme transition */
    html, body, .stApp {
        transition: background 0.5s ease, color 0.5s ease;
    }

    /* Download Button Specific */
    .stDownloadButton>button {
        background: linear-gradient(135deg, #1b4332, #2d6a4f);
        box-shadow: 0 0 10px #1b4332;
    }

    /* Button Press Animation */
    .stButton>button:active, .stDownloadButton>button:active {
        transform: scale(0.97);
    }

    /* Tables */
    .stDataFrame, .stTable {
        background: rgba(255, 255, 255, 0.6);
        border-radius: 12px;
        backdrop-filter: blur(10px);
        padding: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        overflow: hidden;
        font-size: 15px;
    }

    /* Table Headers */
    thead tr th {
        background: linear-gradient(135deg, #52b788, #74c69d);
        color: white;
        font-weight: bold;
        text-align: center;
        padding: 0.5em;
    }

    /* Table Rows */
    tbody tr:nth-child(even) {
        background-color: #e9f7ef;
    }
    tbody tr:nth-child(odd) {
        background-color: #ffffff;
    }
    tbody tr:hover {
        background-color: #b7e4c7;
        transition: background-color 0.3s ease;
    }

    /* Graph iframe Glass Effect */
    .element-container iframe {
        background: rgba(255, 255, 255, 0.5) !important;
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 10px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
    }

    /* Dark Mode Table */
    body.dark-mode .stDataFrame, body.dark-mode .stTable {
        background: #161b22cc;
        border-radius: 10px;
        backdrop-filter: blur(8px);
        font-size: 15px;
        overflow: hidden;
    }
    body.dark-mode thead tr th {
        background: linear-gradient(135deg, #238636, #2ea043);
        color: #ffffff;
        font-weight: bold;
        text-align: center;
    }
    body.dark-mode tbody tr:nth-child(even) {
        background: linear-gradient(90deg, #21262d, #30363d);
        color: #e6edf3;
        transition: all 0.3s ease;
    }
    body.dark-mode tbody tr:nth-child(odd) {
        background: linear-gradient(90deg, #161b22, #21262d);
        color: #e6edf3;
        transition: all 0.3s ease;
    }
    body.dark-mode tbody tr:hover {
        background: linear-gradient(90deg, #21262d, #30363d);
        box-shadow: 0 0 15px #58a6ff;
        transform: scale(1.01);
    }

    /* Dark Mode Graph Glow */
    body.dark-mode .element-container iframe {
        background: rgba(22, 27, 34, 0.5) !important;
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 10px;
        border: 2px solid #58a6ff;
        box-shadow: 0 0 15px #58a6ff, 0 0 30px #79c0ff;
        animation: pulse-glow-dark 3s infinite ease-in-out;
    }

    /* Glow Animations */
    @keyframes pulse-glow {
      0% { box-shadow: 0 0 15px #74c69d, 0 0 30px #52b788; }
      50% { box-shadow: 0 0 25px #40916c, 0 0 45px #2d6a4f; }
      100% { box-shadow: 0 0 15px #74c69d, 0 0 30px #52b788; }
    }
    @keyframes pulse-glow-dark {
      0% { box-shadow: 0 0 15px #58a6ff, 0 0 30px #79c0ff; }
      50% { box-shadow: 0 0 25px #3b82f6, 0 0 45px #2563eb; }
      100% { box-shadow: 0 0 15px #58a6ff, 0 0 30px #79c0ff; }
    }
    </style>
""", unsafe_allow_html=True)


def show():
    require_role(["admin", "collector", "editor"])
    
    st.markdown("""
        <div style='text-align: center;'>
            <h2>🦚 Field Monitoring Data Entry</h2>
            <p style='color: grey;'> Use this page to input daily observations, instrument readings, and site information.</p>
        </div>
        <hr>
    """, unsafe_allow_html=True)
    
    
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

    entry_type = st.selectbox("📝 Select Entry Type", ["", "START", "STOP"], key="entry_type_selectbox")

    if entry_type:
        id_selected = st.selectbox("📌 Select Site ID", ids, key="site_id_selectbox")
        site_selected = site_id_map.get(id_selected, "")
        if site_selected:
            st.text_input("📍 Site", value=site_selected, disabled=True, key="site_name_textbox")
        officer_selected = st.multiselect("🧑‍🔬 Monitoring Officer(s)", officers, key="officer_selectbox")
        driver_name = st.text_input("🧑‍🌾 Driver's Name", key="driver_name_input")

    if entry_type == "START":
        with st.expander("🟢 Start Day Monitoring", expanded=True):
            start_date = st.date_input("📆 Start Date", value=datetime.today(), key="start_date_input")
            start_time = st.time_input("⏱️ Start Time", value=datetime.now().time(), key="start_time_input")
            start_obs = st.text_area("🧿 First Day Observation", key="start_observation_input")

            st.markdown("#### 🌧️ Initial Atmospheric Conditions")
            start_temp = st.number_input("🌡️ Temperature (°C)", step=0.1, key="start_temp_input")
            start_rh = st.number_input("🌬️ Relative Humidity (%)", step=0.1, key="start_rh_input")
            start_pressure = st.number_input("🧭 Pressure (mbar)", step=0.1, key="start_pressure_input")
            start_weather = st.selectbox("🌦️ Weather", weather_conditions, key="start_weather_selectbox")
            start_wind_speed = st.text_input("💨 Wind Speed (e.g. 10 km/h)", key="start_wind_speed_input")
            start_wind_direction = st.selectbox("🌪️ Wind Direction", wind_directions, key="start_wind_direction_selectbox")

            st.markdown("#### ⚙ Initial Sampler Information")
            start_elapsed = st.number_input("⏰ Initial Elapsed Time (min)", step=1, key="start_elapsed_input")
            start_flow = st.number_input("🧯 Initial Flow Rate (L/min)", step=0.1, key="start_flow_input")

            if st.button("✅ Submit Start Day Data", key="start_submit_button"):
                if all([id_selected, site_selected, officer_selected, driver_name]):
                    start_row = [
                        "START", id_selected, site_selected, ", ".join(officer_selected), driver_name,
                        start_date.strftime("%Y-%m-%d"), start_time.strftime("%H:%M:%S"),
                        start_temp, start_rh, start_pressure, start_weather,
                        start_wind_speed, start_wind_direction,
                        start_elapsed, start_flow, start_obs
                    ]
                    add_data(start_row, st.session_state.username)
                    st.success("✅ Start day data submitted successfully!")
                else:
                    st.error("⚠ Please complete all required fields before submitting.")

    elif entry_type == "STOP":
        with st.expander("🔴 Stop Day Monitoring", expanded=True):
            stop_date = st.date_input("📆 Stop Date", value=datetime.today(), key="stop_date_input")
            stop_time = st.time_input("⏱️ Stop Time", value=datetime.now().time(), key="stop_time_input")
            stop_obs = st.text_area("🧿 Final Day Observation", key="stop_observation_input")

            st.markdown("#### 🌧️ Final Atmospheric Conditions")
            stop_temp = st.number_input("🌡️ Final Temperature (°C)", step=0.1, key="stop_temp_input")
            stop_rh = st.number_input("🌬️ Final Relative Humidity (%)", step=0.1, key="stop_rh_input")
            stop_pressure = st.number_input("🧭 Final Pressure (mbar)", step=0.1, key="stop_pressure_input")
            stop_weather = st.selectbox("🌦️ Final Weather", weather_conditions, key="stop_weather_selectbox")
            stop_wind_speed = st.text_input("💨 Final Wind Speed (e.g. 12 km/h)", key="stop_wind_speed_input")
            stop_wind_direction = st.selectbox("🌪️ Final Wind Direction", wind_directions, key="stop_wind_direction_selectbox")

            st.markdown("#### ⚙ Final Sampler Information")
            stop_elapsed = st.number_input("⏰ Final Elapsed Time (min)", step=1, key="stop_elapsed_input")
            stop_flow = st.number_input("🧯 Final Flow Rate (L/min)", step=0.1, key="stop_flow_input")

            if st.button("✅ Submit Stop Day Data", key="stop_submit_button"):
                if all([id_selected, site_selected, officer_selected, driver_name]):
                    stop_row = [
                        "STOP", id_selected, site_selected, ", ".join(officer_selected), driver_name,
                        stop_date.strftime("%Y-%m-%d"), stop_time.strftime("%H:%M:%S"),
                        stop_temp, stop_rh, stop_pressure, stop_weather,
                        stop_wind_speed, stop_wind_direction,
                        stop_elapsed, stop_flow, stop_obs
                    ]
                    add_data(stop_row, st.session_state.username)
                    st.success("✅ Stop day data submitted successfully!")
                else:
                    st.error("⚠ Please complete all required fields before submitting.")

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
            © 2025 EPA Ghana · Developed by Clement Mensah Ackaah 🦺 · Built with 😍 using Streamlit | 
            <a href="mailto:clement.ackaah@epa.gov.gh">Contact Support</a>
        </div>
    """, unsafe_allow_html=True)
