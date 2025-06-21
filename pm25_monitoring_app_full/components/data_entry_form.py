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
from modules.authentication import require_role


def get_custom_time(label, key_prefix, hour_key="hour", minute_key="minute"):
    col1, col2 = st.columns(2)
    with col1:
        hour = st.selectbox(f"{label} - Hour", list(range(0, 24)), key=f"{key_prefix}_{hour_key}")
    with col2:
        minute = st.selectbox(f"{label} - Minute", list(range(0, 60, 1)), key=f"{key_prefix}_{minute_key}")
    return datetime.strptime(f"{hour}:{minute}", "%H:%M").time()


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
    wind_directions = ["-- Select --", "N", "NE", "E", "SE", "S","NNE", "NEN","SWS", "SES", "SSW","SW", "W", "NW"]
    weather_conditions = ["-- Select --", "Sunny", "Cloudy", "Partly Cloudy", "Rainy", "Windy", "Hazy", "Stormy", "Foggy"]
    drivers = ["Kanazoe Sia", "Kofi Adjei", "Fatau"]
    wind_speed_options = list(range(0, 51))  # in km/h

    weather_defaults = {
        "Sunny": {"temp": list(range(25, 41)), "rh": list(range(40, 91))},
        "Rainy": {"temp": list(range(20, 27)), "rh": list(range(70, 101))},
        "Cloudy": {"temp": list(range(25, 35)), "rh": list(range(40, 91))},
        "Partly Cloudy": {"temp": list(range(21, 35)), "rh": list(range(35, 91))},
        "Windy": {"temp": list(range(20, 30)), "rh": list(range(40, 91))},
        "Hazy": {"temp": list(range(20, 31)), "rh": list(range(40, 91))},
        "Stormy": {"temp": list(range(17, 25)), "rh": list(range(80, 101))},
        "Foggy": {"temp": list(range(15, 22)), "rh": list(range(85, 101))}
    }

    entry_type = st.selectbox("📝 Select Entry Type", ["", "START", "STOP"])

    if entry_type:
        id_selected = st.selectbox("📌 Select Site ID", ids)
        site_selected = site_id_map.get(id_selected, "")
        if site_selected:
            st.text_input("📍 Site", value=site_selected, disabled=True)

        st.subheader("5. Officer(s) Involved")
        officer_selected = st.multiselect("🧑‍🔬 Monitoring Officer(s)", officers)
        driver = st.selectbox("🚗 Select Driver", ["-- Select --"] + drivers)

    # ----------- START ENTRY -----------
    if entry_type == "START":
        with st.expander("🟢 Start Day Monitoring", expanded=True):
            st.subheader("3. Date and Time")
            start_date = st.date_input("📅 Start Date", value=datetime.today())
            start_time = get_custom_time("⏱️ Start Time", "start")

            start_obs = st.text_area("🧿 First Day Observation")
            st.markdown("#### 🌧️ Initial Atmospheric Conditions")
            start_weather = st.selectbox("🌦️ Weather", weather_conditions)

            if start_weather != "-- Select --":
                temp_options = ["-- Select --"] + weather_defaults[start_weather]["temp"]
                rh_options = ["-- Select --"] + weather_defaults[start_weather]["rh"]
                start_temp = st.selectbox("🌡️ Temperature (°C)", temp_options)
                start_rh = st.selectbox("💧 Humidity (%)", rh_options)
            else:
                start_temp = start_rh = "-- Select --"

            start_pressure = st.number_input("🧭 Pressure (mbar)", step=0.1)
            start_wind_speed = st.selectbox("💨 Wind Speed (km/h)", ["-- Select --"] + wind_speed_options)
            start_wind_speed = float(start_wind_speed) if start_wind_speed != "-- Select --" else None
            start_wind_direction = st.selectbox("🌪️ Wind Direction", wind_directions)

            st.markdown("#### ⚙ Initial Sampler Information")
            start_elapsed = st.number_input("⏰ Initial Elapsed Time (min)", step=0.1)
            start_flow = st.selectbox("🧯 Initial Flow Rate (L/min)", options=[5, 16.7], index=0)

            if st.button("✅ Submit Start Day Data"):
                if not all([id_selected, site_selected, officer_selected, driver]) or driver == "-- Select --":
                    st.error("⚠ Please complete all required fields before submitting.")
                    return
                if start_weather == "-- Select --" or start_temp == "-- Select --" or start_rh == "-- Select --" or start_wind_direction == "-- Select --":
                    st.error("⚠ Please select valid weather, temperature, humidity, and wind direction.")
                    return

                start_row = [
                    "START", id_selected, site_selected, ", ".join(officer_selected), driver,
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
            stop_time = get_custom_time("⏱️ Stop Time", "stop")
            stop_obs = st.text_area("🧿 Final Day Observation")

            stop_weather = st.selectbox("🌦️ Final Weather", weather_conditions)

            if stop_weather != "-- Select --":
                temp_options = ["-- Select --"] + weather_defaults[stop_weather]["temp"]
                rh_options = ["-- Select --"] + weather_defaults[stop_weather]["rh"]
                stop_temp = st.selectbox("🌡️ Final Temperature (°C)", temp_options)
                stop_rh = st.selectbox("💧 Final Humidity (%)", rh_options)
            else:
                stop_temp = stop_rh = "-- Select --"

            stop_pressure = st.number_input("🧭 Final Pressure (mbar)", step=0.1)
            stop_wind_speed = st.selectbox("💨 Final Wind Speed (km/h)", ["-- Select --"] + wind_speed_options)
            stop_wind_speed = float(stop_wind_speed) if stop_wind_speed != "-- Select --" else None
            stop_wind_direction = st.selectbox("🌪️ Final Wind Direction", wind_directions)

            st.markdown("#### ⚙ Final Sampler Information")
            stop_elapsed = st.number_input("⏰ Final Elapsed Time (min)", step=0.1)
            stop_flow = st.selectbox("🧯 Final Flow Rate (L/min)", options=[5, 16.7], index=0)

            if st.button("✅ Submit Stop Day Data"):
                if not all([id_selected, site_selected, officer_selected, driver]) or driver == "-- Select --":
                    st.error("⚠ Please complete all required fields before submitting.")
                    return
                if stop_weather == "-- Select --" or stop_temp == "-- Select --" or stop_rh == "-- Select --" or stop_wind_direction == "-- Select --":
                    st.error("⚠ Please select valid weather, temperature, humidity, and wind direction.")
                    return

                stop_row = [
                    "STOP", id_selected, site_selected, ", ".join(officer_selected), driver,
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
