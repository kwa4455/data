import streamlit as st
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode
from resource import (
    load_data_from_sheet,
    add_data,
    merge_start_stop,
    save_merged_data_to_sheet,
    delete_row,
    restore_specific_deleted_record,
    filter_by_site_and_date,
    make_unique_headers,
    display_and_merge_data,
    sheet,
    spreadsheet
)
from modules.authentication import require_role
from constants import MERGED_SHEET, CALC_SHEET


def show():
    require_role(["admin", "supervisor"])

    # Page Header
    st.markdown("""
        <div style='text-align: center;'>
            <h2>👷🏽‍♀️ Supervisor Review Section </h2>
            <p style='color: grey;'>For Supervisors to review, inspect, and audit monitoring records</p>
        </div>
        <hr>
    """, unsafe_allow_html=True)

    st.write("This page will display records and allow Supervisors to inspect and audit records.")

    # === Load & Display Existing Monitoring Data ===
    st.header("📡 Submitted Monitoring Records")
    df = load_data_from_sheet(sheet)
    display_and_merge_data(df, spreadsheet, MERGED_SHEET)

    # Editable AgGrid for submitted monitoring records
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True)
    grid_options = gb.build()

    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        fit_columns_on_grid_load=True,
        use_container_width=True
    )

    edited_df = grid_response["data"]

    if st.button("💾 Save Edited Monitoring Records"):
        try:
            safe_df = edited_df.copy()
            safe_df.fillna("", inplace=True)
            worksheet = spreadsheet.worksheet(MERGED_SHEET)
            worksheet.clear()
            worksheet.append_rows([safe_df.columns.tolist()] + safe_df.values.tolist())
            st.success("✅ Edited records saved successfully!")
        except Exception as e:
            st.error(f"❌ Failed to save edited data: {e}")

    # === View Saved PM2.5 Entries ===
    st.subheader("📂 View Saved PM₂.₅ Entries")
    try:
        calc_data = spreadsheet.worksheet(CALC_SHEET).get_all_records()
        df_calc = pd.DataFrame(calc_data)
        AgGrid(df_calc)

        if not df_calc.empty:
            df_calc["Date"] = pd.to_datetime(df_calc["Date _Start"], errors="coerce").dt.date
            df_calc["PM₂.₅ (µg/m³)"] = pd.to_numeric(df_calc["PM₂.₅ (µg/m³)"], errors="coerce")

            with st.expander("🔍 Filter Saved Entries"):
                selected_date = st.date_input("📅 Filter by Date", value=None)
                selected_site = st.selectbox(
                    "📌 Filter by Site",
                    options=["All"] + sorted(df_calc["Site"].unique()),
                    key="site_filter"
                )

                filtered_df = df_calc.copy()
                if selected_date:
                    filtered_df = filtered_df[filtered_df["Date _Start"] == selected_date]
                if selected_site != "All":
                    filtered_df = filtered_df[filtered_df["Site"] == selected_site]

                st.dataframe(filtered_df, use_container_width=True)
        else:
            st.info("ℹ No saved entries yet.")
    except Exception as e:
        st.error(f"❌ Failed to load saved entries: {e}")

    # === View Deleted Records ===
    with st.expander("👷🏾‍♂️ View Deleted Records"):
        try:
            deleted_sheet = spreadsheet.worksheet("Deleted Records")
            deleted_data = deleted_sheet.get_all_values()

            if len(deleted_data) > 1:
                headers = make_unique_headers(deleted_data[0])
                rows = deleted_data[1:]
                df_deleted = pd.DataFrame(rows, columns=headers)

                st.dataframe(df_deleted, use_container_width=True)
            else:
                st.info("No deleted records found.")
        except Exception as e:
            st.error(f"❌ Could not load Deleted Records: {e}")
