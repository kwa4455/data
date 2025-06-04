import streamlit as st
import pandas as pd
from datetime import datetime
from datetime import time as dtime

from resource import (
    load_data_from_sheet,
    add_data,
    merge_start_stop,
    save_merged_data_to_sheet,
    delete_row,
    delete_merged_record_by_index,
    filter_by_site_and_date,
    backup_deleted_row,
    restore_specific_deleted_record,
    sheet,
    spreadsheet,
    display_and_merge_data
)
from constants import MERGED_SHEET
from modules.authentication import require_role



# Make sure this function is available globally
def get_custom_time(label, prefix, hour_key, minute_key, default_time=None):
    if default_time is None:
        default_time = datetime.now().time()

    col1, col2 = st.columns(2)
    hour = col1.number_input(
        f"{label} Hour", min_value=0, max_value=23,
        value=default_time.hour, key=f"{prefix}_{hour_key}"
    )
    minute = col2.number_input(
        f"{label} Minute", min_value=0, max_value=59,
        value=default_time.minute, key=f"{prefix}_{minute_key}"
    )
    return dtime(hour, minute)

# Your main show function
def show():
    require_role(["admin", "officer"])

    st.markdown("""
        <div style='text-align: center;'>
            <h2>✍🏼 Editor Tools</h2>
            <p style='color: grey;'>This page allows authorized users to update or delete submitted records.</p>
        </div>
        <hr>
    """, unsafe_allow_html=True)

    def render_record_edit_form(record_data):
        weather_options = ["Clear", "Cloudy", "Rainy", "Foggy", "Windy", "Hazy", "Dusty", "Other"]
        wind_dir_options = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "Variable", "Calm"]

        def get_str(key, default=""):
            return str(record_data.get(key, default))

        def get_float(key, default=0.0):
            try:
                return float(record_data.get(key, default))
            except (ValueError, TypeError):
                return default

        def get_date(key):
            try:
                return pd.to_datetime(record_data.get(key)).date()
            except Exception:
                return pd.Timestamp.now().date()

        def get_time(key):
            try:
                return pd.to_datetime(record_data.get(key)).time()
            except Exception:
                return pd.Timestamp.now().time()

        entry_type = st.selectbox("Entry Type", ["START", "STOP"], index=["START", "STOP"].index(get_str("Entry Type", "START")))
        site_id = st.text_input("ID", value=get_str("ID"))
        site = st.text_input("Site", value=get_str("Site"))
        monitoring_officer = st.text_input("Monitoring Officer", value=get_str("Monitoring Officer"))
        driver = st.text_input("Driver", value=get_str("Driver"))
        date = st.date_input("Date", value=get_date("Date"))

        # 👇 Use get_custom_time here
        time = get_custom_time("⏱️ Time", "edit", "hour", "minute", default_time=get_time("Time"))

        temperature = st.number_input("Temperature (°C)", value=get_float("Temperature (°C)"), step=0.1)
        rh = st.number_input("Relative Humidity (%)", value=get_float("RH (%)"), step=0.1)
        pressure = st.number_input("Pressure (mbar)", value=get_float("Pressure (mbar)"), step=0.1)

        weather_value = get_str("Weather", "Other")
        weather = st.selectbox("Weather", weather_options, index=weather_options.index(weather_value) if weather_value in weather_options else len(weather_options) - 1)

        wind_speed = st.number_input("Wind Speed (m/s)", value=get_float("Wind Speed (m/s)"), step=0.1)
        wind_dir_value = get_str("Wind Direction", "Variable")
        wind_direction = st.selectbox("Wind Direction", wind_dir_options, index=wind_dir_options.index(wind_dir_value) if wind_dir_value in wind_dir_options else wind_dir_options.index("Variable"))

        elapsed_time = st.number_input("Elapsed Time (min)", value=get_float("Elapsed Time (min)"), step=1.0)
        flow_rate = st.number_input("Flow Rate (L/min)", value=get_float("Flow Rate (L/min)"), step=0.1)
        observation = st.text_area("Observation", value=get_str("Observation"))

        return [
            entry_type, site_id, site, monitoring_officer, driver,
            date.strftime("%Y-%m-%d"), time.strftime("%H:%M:%S"),
            temperature, rh, pressure, weather,
            wind_speed, wind_direction,
            elapsed_time, flow_rate, observation
        ]

    def handle_merge_logic():
        df = load_data_from_sheet(sheet)
        merged_df = merge_start_stop(df)

        if not merged_df.empty:
            save_merged_data_to_sheet(merged_df, spreadsheet, sheet_name=MERGED_SHEET)
            st.success("🩸 Merged records updated.")
            st.dataframe(merged_df, use_container_width=True)
        else:
            st.warning("⚠ No matching records to merge.")

    st.sidebar.header("🔍 Filter Records")
    df_all = load_data_from_sheet(sheet)

    date_column = None
    for col in df_all.columns:
        if col.strip().lower() in ["date", "sampling date", "start date"]:
            date_column = col
            break

    if not date_column:
        st.error("☠️ No 'Date' column found. Please check your Google Sheet headers.")
        st.stop()

    df_all["Date"] = pd.to_datetime(df_all[date_column], errors='coerce').dt.date
    unique_sites = sorted(df_all["Site"].dropna().unique())
    selected_site = st.sidebar.selectbox("Filter by Site", ["All"] + unique_sites)
    selected_date = st.sidebar.date_input("Filter by Date", value=None)

    filtered_df = df_all.copy()
    if selected_site != "All":
        filtered_df = filtered_df[filtered_df["Site"] == selected_site]
    if selected_date:
        filtered_df = filtered_df[filtered_df["Date"] == selected_date]

    def edit_submitted_record():
        df = filtered_df.copy()
        if df.empty:
            st.warning("⚠ No records available to edit with selected filters.")
            return

        df["Submitted At"] = pd.to_datetime(df["Submitted At"], errors='coerce')
        df["Row Number"] = df.index + 2
        df["Record ID"] = df.apply(lambda x: f"{x['Entry Type']} | {x['ID']} | {x['Site']} | {x['Submitted At'].strftime('%Y-%m-%d %H:%M')}", axis=1)

        if 'selected_record' not in st.session_state:
            st.session_state.selected_record = None
        if 'edit_expanded' not in st.session_state:
            st.session_state.edit_expanded = False

        record_options = [""] + df["Record ID"].tolist()
        selected = st.selectbox("Select a record to edit:", record_options, index=record_options.index(st.session_state.selected_record) if st.session_state.selected_record in record_options else 0)

        if selected and selected != st.session_state.selected_record:
            st.session_state.selected_record = selected
            st.session_state.edit_expanded = True

        with st.expander("✍️ Edit Submitted Record", expanded=st.session_state.edit_expanded):
            if not st.session_state.selected_record:
                st.info("🧐 Please select a record from the dropdown above.")
            else:
                try:
                    selected_index = df[df["Record ID"] == st.session_state.selected_record].index[0]
                    record_data = df.loc[selected_index]
                    row_number = record_data["Row Number"]

                    with st.form("edit_form"):
                        updated_data = render_record_edit_form(record_data)
                        submitted = st.form_submit_button("Update Record")

                        if submitted:
                            for col_index, value in enumerate(updated_data, start=1):
                                sheet.update_cell(row_number, col_index, value)

                            st.success("🧠 Record updated successfully!")
                            st.session_state.selected_record = None
                            st.session_state.edit_expanded = False

                            handle_merge_logic()
                except Exception as e:
                    st.error(f"☠️ Error: {e}")

    edit_submitted_record()

    st.subheader("🗑️ Delete from Submitted Records")
    df_submitted = filtered_df.copy()

    if df_submitted.empty:
        st.info("No submitted records available with current filter.")
    else:
        df_submitted["Row Number"] = df_submitted.index + 2
        df_submitted["Record ID"] = df_submitted.apply(lambda x: f"{x['Entry Type']} | {x['ID']} | {x['Site']} | {x['Submitted At']}", axis=1)
        selected_record = st.selectbox("Select submitted record to delete:", [""] + df_submitted["Record ID"].tolist())

        if selected_record:
            row_to_delete = int(df_submitted[df_submitted["Record ID"] == selected_record]["Row Number"].values[0])
            if st.checkbox("✅ Confirm deletion of submitted record"):
                if st.button("🗑️ Delete Submitted Record"):
                    deleted_by = st.session_state.username
                    delete_row(sheet, row_to_delete, deleted_by)
                    st.success(f"✅ Submitted record deleted by {deleted_by} and backed up successfully.")
                    st.rerun()

    # --- Restore Deleted Records ---
    st.markdown("---")
    st.header("🗃️ Restore Deleted Record")

    try:
        backup_sheet = spreadsheet.worksheet("Deleted Records")
        deleted_rows = backup_sheet.get_all_values()

        if len(deleted_rows) <= 1:
            st.info("No deleted records available.")
        else:
            headers = deleted_rows[0]
            records = deleted_rows[1:]
            df_deleted = pd.DataFrame(records, columns=headers)

            if date_column and date_column in df_deleted.columns:
                df_deleted["Date"] = pd.to_datetime(df_deleted[date_column], errors='coerce').dt.date

                if selected_site != "All":
                    df_deleted = df_deleted[df_deleted["Site"] == selected_site]
                if selected_date:
                    df_deleted = df_deleted[df_deleted["Date"] == selected_date]

            if df_deleted.empty:
                st.info("No deleted records match the filter.")
            else:
                options = [
                    f"{i + 1}. " + " | ".join(row.iloc[:-2]) + f" (Deleted by: {row.iloc[-1]})"
                    for i, (_, row) in enumerate(df_deleted.iterrows())
                ]
                selection_list = [""] + options

                selected = st.selectbox("Select a deleted record to restore:", selection_list)

                if selected:
                    selected_index = options.index(selected)
                    selected_row = df_deleted.iloc[selected_index]

                    st.markdown("#### 👁️ Preview of Selected Record")
                    st.dataframe(selected_row.to_frame().T, use_container_width=True)

                    if st.button("↩️ Restore Selected Record"):
                        try:
                            # Delete row from deleted records sheet
                            backup_sheet.delete_rows(selected_index + 2)  # +2 for header & 1-based index

                            # Prepare restored row for main sheet (remove Deleted By column)
                            restored_row = selected_row.iloc[:-1].tolist()

                            # Append 'Restored By' username at the end
                            restored_row.append(st.session_state.username)

                            # Append restored row to main sheet
                            sheet.append_row(restored_row)

                            # Update merged data
                            handle_merge_logic()

                            st.success(f"🧠 Record restored by {st.session_state.username} and re-added successfully!")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Failed to restore record: {e}")

    except Exception as e:
        st.error(f"Failed to load deleted records: {e}")
