import streamlit as st
import pandas as pd
from datetime import datetime, time
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
from modules.authentication import require_role

def show():
    require_role(["admin", "officer"])
    
    st.markdown("""
        <style>
            .editor-subtitle {
                color: var(--text-color);
            }
        </style>
        <div style='text-align: center;'>
            <h2>✍🏼 Data Entry Form </h2>
            <p class='editor-subtitle'>This page allows authorized users to enter air quality monitoring field data.</p>
        </div>
        <hr>
    """, unsafe_allow_html=True)

    # --- Options ---
    ids = ["", '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
    site_id_map = {
        '1': 'Kaneshie First Light',
        '2': 'Tetteh Quarshie Roundabout',
        '3': 'Achimota Interchange',
        '4': 'La',
        '5': 'Mallam Market',
        '6': 'Graphic Road',
        '7': 'Weija',
        '8': 'Kasoa',
        '9': 'Tantra Hill',
        '10': 'Amasaman'
    }
    officers = ['Obed Korankye', 'Clement Ackaah', 'Peter Ohene-Twum', 'Benjamin Essien', 'Mawuli Amegah']
    wind_directions = ["-- Select --", "N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    weather_conditions = ["-- Select --", "Sunny", "Cloudy", "Partly Cloudy", "Rainy", "Windy", "Hazy", "Stormy", "Foggy"]

    weather_defaults = {
        "Sunny": {"temp": list(range(25, 41)), "rh": list(range(10, 41, 5))},
        "Cloudy": {"temp": list(range(20, 31)), "rh": list(range(40, 71, 5))},
        "Partly Cloudy": {"temp": list(range(21, 33)), "rh": list(range(35, 66, 5))},
        "Rainy": {"temp": list(range(18, 27)), "rh": list(range(70, 101, 5))},
        "Windy": {"temp": list(range(15, 26)), "rh": list(range(30, 61, 5))},
        "Hazy": {"temp": list(range(20, 31)), "rh": list(range(30, 71, 5))},
        "Overcast": {"temp": list(range(18, 28)), "rh": list(range(50, 81, 5))},
        "Stormy": {"temp": list(range(17, 25)), "rh": list(range(80, 101, 5))},
        "Foggy": {"temp": list(range(15, 22)), "rh": list(range(85, 101, 5))}
    }

    def get_custom_time(label_prefix, key_prefix, hour_key, minute_key):
        hour = st.selectbox(f"{label_prefix} Hour", list(range(0, 24)), key=f"{key_prefix}_{hour_key}")
        valid_minutes = [m for m in range(60) if m not in [0, 15, 30, 45]]
        minute = st.selectbox(f"{label_prefix} Minute (not 00, 15, 30, 45)", valid_minutes, key=f"{key_prefix}_{minute_key}")
        return time(hour=hour, minute=minute)

    entry_type = st.selectbox("📝 Select Entry Type", ["", "START", "STOP"])

    if entry_type:
        id_selected = st.selectbox("📌 Select Site ID", ids)
        site_selected = site_id_map.get(id_selected, "")
        if site_selected:
            st.text_input("📍 Site", value=site_selected, disabled=True)
        officer_selected = st.multiselect("🧑‍🔬 Monitoring Officer(s)", officers)
        driver_name = st.text_input("🧑‍🌾 Driver's Name")

    # ----------- START ENTRY -----------
    if entry_type == "START":
        with st.expander("🟢 Start Day Monitoring", expanded=True):
            start_date = st.date_input("📆 Start Date", value=datetime.today())
            start_time = get_custom_time("⏱️ Start Time", "start", "hour", "minute")
            start_obs = st.text_area("🧿 First Day Observation")

            st.markdown("#### 🌧️ Initial Atmospheric Conditions")
            start_weather = st.selectbox("🌦️ Weather", weather_conditions)

            if start_weather != "-- Select --":
                temp_options = ["-- Select --"] + weather_defaults.get(start_weather, {}).get("temp", [])
                rh_options = ["-- Select --"] + weather_defaults.get(start_weather, {}).get("rh", [])
                start_temp = st.selectbox("🌡️ Temperature (°C)", temp_options)
                start_rh = st.selectbox("💧 Relative Humidity (%)", rh_options)
            else:
                start_temp = start_rh = "-- Select --"

            start_pressure = st.number_input("🧭 Pressure (mbar)", step=0.1)
            start_wind_speed = st.text_input("💨 Wind Speed (e.g. 10 km/h)")
            start_wind_direction = st.selectbox("🌪️ Wind Direction", wind_directions)

            st.markdown("#### ⚙ Initial Sampler Information")
            start_elapsed = st.number_input("⏰ Initial Elapsed Time (min)", step=0.1)
            start_flow = st.number_input("🧯 Initial Flow Rate (L/min)", value="5.0",disabled=True)
            

            if st.button("✅ Submit Start Day Data"):
                if not all([id_selected, site_selected, officer_selected, driver_name]):
                    st.error("⚠ Please complete all required fields before submitting.")
                    return
                if start_weather == "-- Select --" or start_temp == "-- Select --" or start_rh == "-- Select --" or start_wind_direction == "-- Select --":
                    st.error("⚠ Please select valid weather, temp, RH, and wind direction.")
                    return

                start_row = [
                    "START", id_selected, site_selected, ", ".join(officer_selected), driver_name,
                    start_date.strftime("%Y-%m-%d"), start_time.strftime("%H:%M:%S"),
                    start_temp, start_rh, start_pressure, start_weather,
                    start_wind_speed, start_wind_direction,
                    start_elapsed, start_flow, start_obs
                ]
                add_data(start_row, st.session_state.username)
                st.success("✅ Start day data submitted successfully!")

    # ----------- STOP ENTRY -----------
    elif entry_type == "STOP":
        with st.expander("🔴 Stop Day Monitoring", expanded=True):
            stop_date = st.date_input("📆 Stop Date", value=datetime.today())
            stop_time = get_custom_time("⏱️ Stop Time", "stop", "hour", "minute")
            stop_obs = st.text_area("🧿 Final Day Observation")

            st.markdown("#### 🌧️ Final Atmospheric Conditions")
            stop_weather = st.selectbox("🌦️ Final Weather", weather_conditions)

            if stop_weather != "-- Select --":
                temp_options = ["-- Select --"] + weather_defaults.get(stop_weather, {}).get("temp", [])
                rh_options = ["-- Select --"] + weather_defaults.get(stop_weather, {}).get("rh", [])
                stop_temp = st.selectbox("🌡️ Final Temperature (°C)", temp_options)
                stop_rh = st.selectbox("💧 Final Relative Humidity (%)", rh_options)
            else:
                stop_temp = stop_rh = "-- Select --"

            stop_pressure = st.number_input("🧭 Final Pressure (mbar)", step=0.1)
            stop_wind_speed = st.text_input("💨 Final Wind Speed (e.g. 12 km/h)")
            stop_wind_direction = st.selectbox("🌪️ Final Wind Direction", wind_directions)

            st.markdown("#### ⚙ Final Sampler Information")
            stop_elapsed = st.number_input("⏰ Final Elapsed Time (min)", step=0.1)
            stop_flow = st.number_input("🧯 Final Flow Rate (L/min)", value="5.0", disabled=True)
            

            if st.button("✅ Submit Stop Day Data"):
                if not all([id_selected, site_selected, officer_selected, driver_name]):
                    st.error("⚠ Please complete all required fields before submitting.")
                    return
                if stop_weather == "-- Select --" or stop_temp == "-- Select --" or stop_rh == "-- Select --" or stop_wind_direction == "-- Select --":
                    st.error("⚠ Please select valid weather, temp, RH, and wind direction.")
                    return

                stop_row = [
                    "STOP", id_selected, site_selected, ", ".join(officer_selected), driver_name,
                    stop_date.strftime("%Y-%m-%d"), stop_time.strftime("%H:%M:%S"),
                    stop_temp, stop_rh, stop_pressure, stop_weather,
                    stop_wind_speed, stop_wind_direction,
                    stop_elapsed, stop_flow, stop_obs
                ]
                add_data(stop_row, st.session_state.username)
                st.success("✅ Stop day data submitted successfully!")

    # ----------- Show Data Records -----------
    if st.checkbox("📖 Show Submitted Monitoring Records"):
        try:
            df = load_data_from_sheet(sheet)
            df_saved = display_and_merge_data(df, spreadsheet, MERGED_SHEET)
            st.dataframe(df_saved, use_container_width=True)
        except Exception as e:
            st.warning(f"⚠ Could not load Submitted Monitoring Records: {e}")
