import streamlit as st
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
from constants import MERGED_SHEET, MAIN_SHEET
from modules.authentication import require_role

def show():
    require_role(["admin", "officer"])

    ids = [""] + [str(i) for i in range(1, 11)]
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
    wind_directions = ["", "N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    weather_conditions = ["", "Sunny", "Cloudy", "Partly Cloudy", "Rainy", "Windy", "Hazy", "Stormy", "Foggy"]

    def get_custom_time(label_prefix, key_prefix, hour_key, minute_key):
        hour = st.selectbox(
            label=f"{label_prefix} Hour",
            options=[str(h) for h in range(0, 24)],
            key=f"{key_prefix}_{hour_key}"
        )
        valid_minutes = [m for m in range(60) if m not in [0, 15, 30, 45]]
        minute = st.selectbox(
            label=f"{label_prefix} Minute (not 00, 15, 30, 45)",
            options=[str(m) for m in valid_minutes],
            key=f"{key_prefix}_{minute_key}"
        )
        return time(hour=int(hour), minute=int(minute))

    entry_type = st.radio(
        label="📝 Select Entry Type",
        options=["", "START", "STOP"],
        key="entry_type_segmented"
    )

    if entry_type and entry_type != "":
        id_selected = st.selectbox(
            "📌 Select Site ID",
            options=ids,
            index=0,
            key="site_id_selectbox"
        )
        site_selected = site_id_map.get(id_selected, "")
        if site_selected:
            st.text_input("📍 Site", value=site_selected, disabled=True, key="site_name_textbox")

        officer_selected = st.multiselect(
            label="🧑‍🔬 Monitoring Officer(s)",
            options=officers,
            key="officer_selectbox"
        )
        driver_name = st.text_input("🧑‍🌾 Driver's Name", key="driver_name_input")

        if entry_type == "START":
            with st.expander("🟢 Start Day Monitoring", expanded=True):
                start_date = st.date_input("📆 Start Date", value=datetime.today(), key="start_date_input")
                start_time = get_custom_time("⏱️ Start Time", "start", "hour", "minute")
                start_obs = st.text_area("🧿 First Day Observation", key="start_observation_input")

                st.markdown("#### 🌧️ Initial Atmospheric Conditions")
                start_temp = st.number_input("🌡️ Temperature (°C)", key="start_temp_input", step=1)
                start_rh = st.number_input("🌬️ Relative Humidity (%)", key="start_rh_input", step=1)
                start_pressure = st.number_input("🧭 Pressure (mbar)", key="start_pressure_input", step=0.1)
                start_weather = st.selectbox("🌦️ Weather", weather_conditions, key="start_weather_selectbox")
                start_wind_speed = st.text_input("💨 Wind Speed (e.g. 10 km/h)", key="start_wind_speed_input")
                start_wind_direction = st.selectbox("🌪️ Wind Direction", wind_directions, key="start_wind_direction_selectbox")

                st.markdown("#### ⚙ Initial Sampler Information")
                start_elapsed = st.number_input("⏰ Initial Elapsed Time (min)", key="start_elapsed_input", step=0.1)
                start_flow = st.number_input("🧯 Initial Flow Rate (L/min)", key="start_flow_input", step=1)

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
                stop_time = get_custom_time("⏱️ Stop Time", "stop", "hour", "minute")
                stop_obs = st.text_area("🧿 Final Day Observation", key="stop_observation_input")

                st.markdown("#### 🌧️ Final Atmospheric Conditions")
                stop_temp = st.number_input("🌡️ Final Temperature (°C)", key="stop_temp_input", step=1)
                stop_rh = st.number_input("🌬️ Final Relative Humidity (%)", key="stop_rh_input", step=1)
                stop_pressure = st.number_input("🧭 Final Pressure (mbar)", key="stop_pressure_input", step=0.1)
                stop_weather = st.selectbox("🌦️ Final Weather", weather_conditions, key="stop_weather_selectbox")
                stop_wind_speed = st.text_input("💨 Final Wind Speed (e.g. 12 km/h)", key="stop_wind_speed_input")
                stop_wind_direction = st.selectbox("🌪️ Final Wind Direction", wind_directions, key="stop_wind_direction_selectbox")

                st.markdown("#### ⚙ Final Sampler Information")
                stop_elapsed = st.number_input("⏰ Final Elapsed Time (min)", key="stop_elapsed_input", step=0.1)
                stop_flow = st.number_input("🧯 Final Flow Rate (L/min)", key="stop_flow_input", step=1)

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
            st.markdown("<div class='custom-table-wrapper'>", unsafe_allow_html=True)
            st.dataframe(df_saved, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"⚠ Could not load Submitted Monitoring Records: {e}")
