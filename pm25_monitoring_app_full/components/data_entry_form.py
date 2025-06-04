import streamlit as st
import streamlit_antd_components as sac
from datetime import datetime, time
from resource import (
    load_data_from_sheet,
    add_data,
    display_and_merge_data,
    sheet,
    spreadsheet
)
from constants import MERGED_SHEET
from modules.authentication import require_role

def show():
    require_role(["admin", "officer"])

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
    wind_directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    weather_conditions = ["Sunny", "Cloudy", "Partly Cloudy", "Rainy", "Windy", "Hazy", "Stormy", "Foggy"]

    def get_custom_time(label_prefix, key_prefix):
        hour = st.selectbox(f"{label_prefix} Hour", list(range(24)), key=f"{key_prefix}_hour")
        valid_minutes = [m for m in range(60) if m not in [0, 15, 30, 45]]
        minute = st.selectbox(f"{label_prefix} Minute (exclude 00,15,30,45)", valid_minutes, key=f"{key_prefix}_minute")
        return time(hour=hour, minute=minute)

    # Entry type using AntD segmented control
    entry_type = sac.segmented(
        items=["START", "STOP"],
        label="📝 Select Entry Type",
        key="entry_type_segmented"
    )

    if entry_type:
        # Use Streamlit selectbox for site ID because sac.selectbox does not exist
        id_selected = st.selectbox("📌 Select Site ID", [""] + list(site_id_map.keys()), key="site_id_selectbox")
        site_selected = site_id_map.get(id_selected, "")
        if site_selected:
            st.text_input("📍 Site", value=site_selected, disabled=True, key="site_name_textbox")

        # Multi-select for officers
        officer_selected = sac.multi_select(
            label="🧑‍🔬 Monitoring Officer(s)",
            options=officers,
            key="officer_selectbox"
        )

        # Text input for driver name
        driver_name = sac.input_text("🧑‍🌾 Driver's Name", key="driver_name_input")

    if entry_type == "START":
        with st.expander("🟢 Start Day Monitoring", expanded=True):
            start_date = sac.date_picker("📆 Start Date", value=datetime.today(), key="start_date_input")
            start_time = get_custom_time("⏱️ Start Time", "start")

            start_obs = st.text_area("🧿 First Day Observation", key="start_observation_input")

            st.markdown("#### 🌧️ Initial Atmospheric Conditions")
            start_temp = sac.input_number("🌡️ Temperature (°C)", step=1, key="start_temp_input")
            start_rh = sac.input_number("🌬️ Relative Humidity (%)", step=1, key="start_rh_input")
            start_pressure = sac.input_number("🧭 Pressure (mbar)", step=0.1, key="start_pressure_input")
            # Use Streamlit selectbox for weather (no sac.selectbox)
            start_weather = st.selectbox("🌦️ Weather", weather_conditions, key="start_weather_selectbox")
            start_wind_speed = sac.input_text("💨 Wind Speed (e.g. 10 km/h)", key="start_wind_speed_input")
            # Use Streamlit selectbox for wind direction
            start_wind_direction = st.selectbox("🌪️ Wind Direction", wind_directions, key="start_wind_direction_selectbox")

            st.markdown("#### ⚙ Initial Sampler Information")
            start_elapsed = sac.input_number("⏰ Initial Elapsed Time (min)", step=0.1, key="start_elapsed_input")
            start_flow = sac.input_number("🧯 Initial Flow Rate (L/min)", step=1, key="start_flow_input")

            if sac.button("✅ Submit Start Day Data", key="start_submit_button"):
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
            stop_date = sac.date_picker("📆 Stop Date", value=datetime.today(), key="stop_date_input")
            stop_time = get_custom_time("⏱️ Stop Time", "stop")
            stop_obs = st.text_area("🧿 Final Day Observation", key="stop_observation_input")

            st.markdown("#### 🌧️ Final Atmospheric Conditions")
            stop_temp = sac.input_number("🌡️ Final Temperature (°C)", step=1, key="stop_temp_input")
            stop_rh = sac.input_number("🌬️ Final Relative Humidity (%)", step=1, key="stop_rh_input")
            stop_pressure = sac.input_number("🧭 Final Pressure (mbar)", step=0.1, key="stop_pressure_input")
            stop_weather = st.selectbox("🌦️ Final Weather", weather_conditions, key="stop_weather_selectbox")
            stop_wind_speed = sac.input_text("💨 Final Wind Speed (e.g. 12 km/h)", key="stop_wind_speed_input")
            stop_wind_direction = st.selectbox("🌪️ Final Wind Direction", wind_directions, key="stop_wind_direction_selectbox")

            st.markdown("#### ⚙ Final Sampler Information")
            stop_elapsed = sac.input_number("⏰ Final Elapsed Time (min)", step=0.1, key="stop_elapsed_input")
            stop_flow = sac.input_number("🧯 Final Flow Rate (L/min)", step=1, key="stop_flow_input")

            if sac.button("✅ Submit Stop Day Data", key="stop_submit_button"):
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
