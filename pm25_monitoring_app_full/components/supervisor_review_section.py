import streamlit as st
import pandas as pd
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
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode


def show():
    require_role(["admin", "supervisor"])

    st.markdown("""
        <div style='text-align: center;'>
            <h2>👷🏽‍♀️ Supervisor Review Section </h2>
            <p style='color: grey;'>For Supervisors to review, inspect, and audit monitoring records</p>
        </div>
        <hr>
    """, unsafe_allow_html=True)

    st.write("This page will display records and allow Supervisors to inspect and audit records.")

    # === Load and Display Existing Data & Merge START/STOP ===
    st.header("📡 Submitted Monitoring Records")
    df = load_data_from_sheet(sheet)
    display_and_merge_data(df, spreadsheet, MERGED_SHEET)

    # Keep a copy of original data to compare changes for highlighting
    df['_original'] = df.copy(deep=True).to_dict(orient='records')

    # Build Grid options
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, resizable=True, min_column_width=120)

    # JS code to highlight changed cells and add padding/wrapping for readability
    highlight_js = JsCode("""
    function(params) {
        const original = params.data._original ? params.data._original[params.colDef.field] : undefined;
        if (original !== undefined && params.value !== original) {
            return {
                backgroundColor: '#fff3cd',
                color: '#856404',
                fontWeight: 'bold',
                padding: '10px',
                whiteSpace: 'normal',
                overflowWrap: 'break-word'
            };
        }
        return {
            padding: '10px',
            whiteSpace: 'normal',
            overflowWrap: 'break-word'
        };
    }
    """)

    for col in df.columns:
        if col != '_original':
            gb.configure_column(col, cellStyle=highlight_js)

    grid_options = gb.build()

    # Auto size columns on grid ready event
    grid_options["onGridReady"] = JsCode("""
        function(params) {
            params.api.sizeColumnsToFit();
        }
    """)

    # Set row height to 40 px for better readability
    grid_options['getRowHeight'] = JsCode("function() { return 40; }")

    # Display editable grid
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        allow_unsafe_jscode=True,
        use_container_width=True,
        height=500,
        reload_data=False
    )

    # Undo/revert functionality
    if st.button("↩️ Undo All Changes"):
        st.experimental_rerun()  # simply reload the page to discard changes

    # --- View Saved Entries ---
    st.subheader("📂 View Saved PM₂.₅ Entries")
    try:
        calc_data = spreadsheet.worksheet(CALC_SHEET).get_all_records()
        df_calc = pd.DataFrame(calc_data)

        gb_calc = GridOptionsBuilder.from_dataframe(df_calc)
        gb_calc.configure_default_column(resizable=True, min_column_width=120)
        calc_grid_options = gb_calc.build()
        calc_grid_options["onGridReady"] = JsCode("""
            function(params) {
                params.api.sizeColumnsToFit();
            }
        """)
        calc_grid_options['getRowHeight'] = JsCode("function() { return 40; }")

        AgGrid(
            df_calc,
            gridOptions=calc_grid_options,
            allow_unsafe_jscode=True,
            use_container_width=True,
            height=400,
        )

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
                filtered_df = filtered_df[filtered_df["Date _Start"] == pd.Timestamp(selected_date)]
            if selected_site != "All":
                filtered_df = filtered_df[filtered_df["Site"] == selected_site]

            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.info("ℹ No saved entries yet.")
    except Exception as e:
        st.error(f"❌ Failed to load saved entries: {e}")

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
