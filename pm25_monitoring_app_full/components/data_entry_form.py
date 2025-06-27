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

def required_label(label):
    return f"<span style='color:red;'>*</span> <strong>{label}</strong>"


def show():
    require_role(["admin", "officer"])

    st.markdown("""
        <style>
            .editor-subtitle {
                color: var(--text-color);
            }
        </style>
        <div style='text-align: center;'>
            <h2>✍️ Data Entry Form </h2>
            <p class='editor-subtitle'>This page allows authorized users to enter air quality monitoring field data.</p>
        </div>
        <hr>
    """, unsafe_allow_html=True)

    ids = ["", '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
    site_id_map = {
        '1': {'name': 'Kaneshie First Light', 'lat': 5.568443, 'lon': -0.241189},
        '2': {'name': 'Tetteh Quarshie Roundabout', 'lat': 5.618210, 'lon': -0.176112},
        '3': {'name': 'Achimota Interchange', 'lat': 5.612332, 'lon': -0.229281},
        '4': {'name': 'La', 'lat': 5.562830, 'lon': -0.144382},
        '5': {'name': 'Mallam Market', 'lat': 5.571559, 'lon': -0.279552},
        '6': {'name': 'Graphic Road', 'lat': 5.554906, 'lon': -0.216888},
        '7': {'name': 'Weija', 'lat': 5.554087, 'lon': -0.308612},
        '8': {'name': 'Kasoa', 'lat': 5.538664, 'lon': -0.399573},
        '9': {'name': 'Tantra Hill', 'lat': 5.645072, 'lon': -0.247072},
        '10': {'name': 'Amasaman', 'lat': 5.698762, 'lon': -0.292757}
    }

    tab1, tab2 = st.tabs(["📝 Submit Data", "🔄 Merge & Review"])

    with tab1:
        st.markdown(required_label("📝 Select Entry Type"), unsafe_allow_html=True)
        entry_type = st.selectbox("Select Entry Type", ["", "START", "STOP"])
        if not entry_type:
            return

        st.markdown(required_label("📌 Select Site ID"), unsafe_allow_html=True)
        id_selected = st.selectbox("", ids)
        site_info = site_id_map.get(id_selected)
        if site_info:
            st.text_input("📍 Site", value=site_info['name'], disabled=True)
            st.text_input("📌 Latitude", value=site_info['lat'], disabled=True)
            st.text_input("📌 Longitude", value=site_info['lon'], disabled=True)

        st.subheader("5. Officer(s) Involved")
        st.markdown(required_label("🧑‍🔬 Monitoring Officer(s)"), unsafe_allow_html=True)
        officers = ['Obed Korankye', 'Clement Ackaah', 'Peter Ohene-Twum', 'Benjamin Essien', 'Mawuli Amegah']
        officer_selected = st.multiselect("", officers)

        st.markdown(required_label("🚗 Select Driver"), unsafe_allow_html=True)
        driver = st.selectbox("", ["-- Select --", "Kanazoe Sia", "Kofi Adjei", "Fatau"])

        if entry_type == "START":
            with st.expander("🟢 Start Day Monitoring", expanded=True):
                st.subheader("3. Date and Time")
                st.markdown(required_label("🗕️ Start Date"), unsafe_allow_html=True)
                start_date = st.date_input("", value=datetime.today())
                start_time = get_custom_time("⏱️ Start Time", "start")

                st.markdown(required_label("🧿 First Day Observation"), unsafe_allow_html=True)
                start_obs = st.text_area("")

                st.markdown("#### 🌧️ Initial Atmospheric Conditions")
                weather_conditions = ["-- Select --", "Sunny", "Cloudy", "Partly Cloudy", "Rainy", "Windy", "Hazy", "Stormy", "Foggy"]
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

                st.markdown(required_label("🌦️ Weather"), unsafe_allow_html=True)
                start_weather = st.selectbox("", weather_conditions)

                if start_weather != "-- Select --":
                    temp_options = ["-- Select --"] + weather_defaults[start_weather]["temp"]
                    rh_options = ["-- Select --"] + weather_defaults[start_weather]["rh"]
                    st.markdown(required_label("🌡️ Temperature (°C)"), unsafe_allow_html=True)
                    start_temp = st.selectbox("", temp_options)
                    st.markdown(required_label("💧 Humidity (%)"), unsafe_allow_html=True)
                    start_rh = st.selectbox("", rh_options)
                else:
                    start_temp = start_rh = "-- Select --"

                st.markdown(required_label("🧽 Pressure (mbar)"), unsafe_allow_html=True)
                start_pressure = st.number_input("", step=0.1)
                st.markdown(required_label("💨 Wind Speed (km/h)"), unsafe_allow_html=True)
                start_wind_speed = st.selectbox("", ["-- Select --"] + list(range(0, 51)))
                start_wind_speed = float(start_wind_speed) if start_wind_speed != "-- Select --" else None

                st.markdown(required_label("🌪️ Wind Direction"), unsafe_allow_html=True)
                start_wind_direction = st.selectbox("", ["-- Select --", "N", "NE", "E", "SE", "S", "NNE", "NEN", "SWS", "SES", "SSW", "SW", "W", "NW"])

                st.markdown("#### ⚙ Initial Sampler Information")
                st.markdown(required_label("⏰ Initial Elapsed Time (min)"), unsafe_allow_html=True)
                start_elapsed = st.number_input("Elapsed Time (min)", step=0.1, key="start_elapsed")
                st.markdown(required_label("🧯 Initial Flow Rate (L/min)"), unsafe_allow_html=True)
                start_flow = st.selectbox("", options=[5, 16.7], index=0)

                if st.button("✅ Submit Start Day Data"):
                    required_start_fields = {
                        "Site ID": id_selected,
                        "Site": site_info['name'],
                        "Latitude": site_info['lat'],
                        "Longitude": site_info['lon'],
                        "Officers": officer_selected,
                        "Driver": driver if driver != "-- Select --" else None,
                        "Start Date": start_date,
                        "Start Time": start_time,
                        "Start Observation": start_obs.strip(),
                        "Weather": start_weather if start_weather != "-- Select --" else None,
                        "Temperature": start_temp if start_temp != "-- Select --" else None,
                        "Humidity": start_rh if start_rh != "-- Select --" else None,
                        "Pressure": start_pressure,
                        "Wind Speed": start_wind_speed,
                        "Wind Direction": start_wind_direction if start_wind_direction != "-- Select --" else None,
                        "Elapsed Time": start_elapsed,
                        "Flow Rate": start_flow,
                    }
                    missing_fields = [field for field, value in required_start_fields.items() if not value]
                    if missing_fields:
                        st.error(f"⚠ Please complete all required fields: {', '.join(missing_fields)}")
                        return

                    start_row = [
                        "START", id_selected, site_info['name'], site_info['lat'], site_info['lon'], ", ".join(officer_selected), driver,
                        start_date.strftime("%Y-%m-%d"), start_time.strftime("%H:%M:%S"),
                        start_temp, start_rh, start_pressure, start_weather,
                        start_wind_speed, start_wind_direction,
                        start_elapsed, start_flow, start_obs
                    ]
                    add_data(start_row, st.session_state.username)
                    st.success("✅ Start day data submitted successfully!")

        elif entry_type == "STOP":
            with st.expander("🔴 Stop Day Monitoring", expanded=True):
                st.markdown(required_label("🗖️ Stop Date"), unsafe_allow_html=True)
                stop_date = st.date_input("", value=datetime.today())
                stop_time = get_custom_time("⏱️ Stop Time", "stop")
                st.markdown(required_label("🧿 Final Day Observation"), unsafe_allow_html=True)
                stop_obs = st.text_area("")

                weather_conditions = ["-- Select --", "Sunny", "Cloudy", "Partly Cloudy", "Rainy", "Windy", "Hazy", "Stormy", "Foggy"]
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

                st.markdown(required_label("🌦️ Final Weather"), unsafe_allow_html=True)
                stop_weather = st.selectbox("", weather_conditions)

                if stop_weather != "-- Select --":
                    temp_options = ["-- Select --"] + weather_defaults[stop_weather]["temp"]
                    rh_options = ["-- Select --"] + weather_defaults[stop_weather]["rh"]
                    st.markdown(required_label("🌡️ Final Temperature (°C)"), unsafe_allow_html=True)
                    stop_temp = st.selectbox("", temp_options)
                    st.markdown(required_label("💧 Final Humidity (%)"), unsafe_allow_html=True)
                    stop_rh = st.selectbox("", rh_options)
                else:
                    stop_temp = stop_rh = "-- Select --"

                st.markdown(required_label("🧽 Final Pressure (mbar)"), unsafe_allow_html=True)
                stop_pressure = st.number_input("", step=0.1)
                st.markdown(required_label("💨 Final Wind Speed (km/h)"), unsafe_allow_html=True)
                stop_wind_speed = st.selectbox("", ["-- Select --"] + list(range(0, 51)))
                stop_wind_speed = float(stop_wind_speed) if stop_wind_speed != "-- Select --" else None
                st.markdown(required_label("🌪️ Final Wind Direction"), unsafe_allow_html=True)
                stop_wind_direction = st.selectbox("", ["-- Select --", "N", "NE", "E", "SE", "S", "NNE", "NEN", "SWS", "SES", "SSW", "SW", "W", "NW"])

                st.markdown("#### ⚙ Final Sampler Information")
                st.markdown(required_label("⏰ Final Elapsed Time (min)"), unsafe_allow_html=True)
                stop_elapsed = st.number_input("Elapsed Time (min)", step=0.1, key="stop_elapsed")
                st.markdown(required_label("🧯 Final Flow Rate (L/min)"), unsafe_allow_html=True)
                stop_flow = st.selectbox("", options=[5, 16.7], index=0)

                if st.button("✅ Submit Stop Day Data"):
                    required_stop_fields = {
                        "Site ID": id_selected,
                        "Site": site_info['name'],
                        "Latitude": site_info['lat'],
                        "Longitude": site_info['lon'],
                        "Officers": officer_selected,
                        "Driver": driver if driver != "-- Select --" else None,
                        "Stop Date": stop_date,
                        "Stop Time": stop_time,
                        "Stop Observation": stop_obs.strip(),
                        "Weather": stop_weather if stop_weather != "-- Select --" else None,
                        "Temperature": stop_temp if stop_temp != "-- Select --" else None,
                        "Humidity": stop_rh if stop_rh != "-- Select --" else None,
                        "Pressure": stop_pressure,
                        "Wind Speed": stop_wind_speed,
                        "Wind Direction": stop_wind_direction if stop_wind_direction != "-- Select --" else None,
                        "Elapsed Time": stop_elapsed,
                        "Flow Rate": stop_flow,
                    }
                    missing_fields = [field for field, value in required_stop_fields.items() if not value]
                    if missing_fields:
                        st.error(f"⚠ Please complete all required fields: {', '.join(missing_fields)}")
                        return

                    stop_row = [
                        "STOP", id_selected, site_info['name'], site_info['lat'], site_info['lon'], ", ".join(officer_selected), driver,
                        stop_date.strftime("%Y-%m-%d"), stop_time.strftime("%H:%M:%S"),
                        stop_temp, stop_rh, stop_pressure, stop_weather,
                        stop_wind_speed, stop_wind_direction,
                        stop_elapsed, stop_flow, stop_obs
                    ]
                    add_data(stop_row, st.session_state.username)
                    st.success("✅ Stop day data submitted successfully!")

    with tab2:
        st.subheader("🔄 Merge START and STOP Entries")

        df = load_data_from_sheet(sheet)
        if df.empty:
            st.info("ℹ️ No observation data found.")
        else:
            display_and_merge_data(df, spreadsheet, MERGED_SHEET)
