import streamlit as st
import pandas as pd
import numpy as np
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

    # --- Page Title & Description ---
    st.markdown("""
        <div style='text-align: center;'>
            <h2>👷🏽‍♀️ Supervisor Review Section </h2>
            <p style='color: grey;'>For Supervisors to review, inspect, and audit monitoring records</p>
        </div>
        <hr>
    """, unsafe_allow_html=True)

    st.write("This page will display records and allow Supervisors to inspect and audit records.")

    # === Load Data ===
    df = load_data_from_sheet(sheet)

    # Display & merge existing data (your existing function)
    display_and_merge_data(df, spreadsheet, MERGED_SHEET)

    # === Editable AgGrid with Highlight and Undo/Revert ===
    st.header("📡 Submitted Monitoring Records (Editable)")

    # Backup original df in session state (for revert)
    if "original_df" not in st.session_state:
        st.session_state["original_df"] = df.copy()

    # Use the session state df if available, else the loaded one
    working_df = st.session_state.get("working_df", st.session_state["original_df"]).copy()

    # Add unique row id for tracking changes
    working_df["_row_id"] = np.arange(len(working_df))

    # Save original values in each row for cell style comparison
    working_df["_original"] = working_df.to_dict("records")

    # Build grid options
    gb = GridOptionsBuilder.from_dataframe(working_df)
    gb.configure_default_column(editable=True)

    # JS for highlighting changed cells (yellow background)
    highlight_js = JsCode("""
    function(params) {
        if (params.value !== params.data._original[params.colDef.field]) {
            return {backgroundColor: '#fff3cd', color: '#856404', fontWeight: 'bold'};
        }
        return null;
    }
    """)

    # Apply the cell style to all columns except helper columns
    for col in working_df.columns:
        if col not in ["_row_id", "_original"]:
            gb.configure_column(col, cellStyle=highlight_js)

    grid_options = gb.build()

    # Display the editable AgGrid
    grid_response = AgGrid(
        working_df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        use_container_width=True,
        height=400,  # set a fixed height for good visual
    )

    # Get edited dataframe, remove helper columns
    edited_df = pd.DataFrame(grid_response["data"]).drop(columns=["_row_id", "_original"], errors="ignore")

    # Save edited dataframe to session state to keep edits between reruns
    st.session_state["working_df"] = edited_df.copy()

    # Buttons in a horizontal layout (using columns)
    col1, col2, col3 = st.columns([1, 1, 3])

    with col1:
        if st.button("↩️ Revert to Original Data"):
            st.session_state["working_df"] = st.session_state["original_df"].copy()
            st.experimental_rerun()

    with col2:
        if st.button("💾 Save Edited Monitoring Records"):
            try:
                safe_df = st.session_state["working_df"].copy()
                safe_df.fillna("", inplace=True)
                worksheet = spreadsheet.worksheet(MERGED_SHEET)
                worksheet.clear()
                worksheet.append_rows([safe_df.columns.tolist()] + safe_df.values.tolist())
                st.success("✅ Edited records saved successfully!")
                # Update original to saved after saving
                st.session_state["original_df"] = safe_df.copy()
            except Exception as e:
                st.error(f"❌ Failed to save edited data: {e}")

    # --- View Saved Entries ---
    st.subheader("📂 View Saved PM₂.₅ Entries")
    try:
        calc_data = spreadsheet.worksheet(CALC_SHEET).get_all_records()
        df_calc = pd.DataFrame(calc_data)
        AgGrid(df_calc, use_container_width=True, height=300)

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

    # --- Deleted Records Section ---
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
