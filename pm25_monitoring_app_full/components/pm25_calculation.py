import streamlit as st
import pandas as pd
from datetime import datetime
from resource import spreadsheet
from constants import MERGED_SHEET, CALC_SHEET
from modules.authentication import require_role

def show():
    require_role(["admin", "officer"])
    
    
    # --- Page Title ---
    st.markdown("""
        <div style='text-align: center;'>
            <h2> 🧶 PM₂.₅ Concentration Calculator </h2>
            <p style='color: grey;'>Enter Pre and Post Weights to calculate PM₂.₅ concentrations in µg/m³ .</p>
        </div>
        <hr>
    """, unsafe_allow_html=True)


    # --- Load Merged Data ---
    try:
        merged_data = spreadsheet.worksheet(MERGED_SHEET).get_all_records()
        df_merged = pd.DataFrame(merged_data)
        df_merged.columns = df_merged.columns.str.strip()

        if not {"Elapsed Time Diff (min)", "Average Flow Rate (L/min)"}.issubset(df_merged.columns):
            st.error("❌ Required columns missing: 'Elapsed Time Diff (min)', 'Average Flow Rate (L/min)'")
            st.stop()
    except Exception as e:
        st.error(f"❌ Failed to load merged sheet: {e}")
        st.stop()

    # --- Site Filter ---
    if "Site" in df_merged.columns:
        try:
            available_sites = sorted(df_merged["Site"].dropna().unique())
            site_options = ["All Sites"] + available_sites
            most_recent_site = df_merged["Site"].dropna().iloc[0] if not df_merged.empty else "All Sites"

            st.subheader("🗺️ Filter by Site")
            selected_site = st.selectbox("📍 Select Site", options=site_options, index=site_options.index(most_recent_site))
            if selected_site != "All Sites":
                filtered_df = df_merged[df_merged["Site"] == selected_site].copy()
            else:
                filtered_df = df_merged.copy()
        except Exception as e:
            st.warning(f"⚠ Could not auto-select site: {e}")
            filtered_df = df_merged.copy()
    else:
        st.warning("⚠ 'Site' column not found — skipping site filter.")
        filtered_df = df_merged.copy()

    # --- Date Filter ---
    if "Date_Start" in filtered_df.columns:
        try:
            filtered_df = filtered_df.copy()
            filtered_df["Date_Start"] = pd.to_datetime(filtered_df["Date_Start"], errors="coerce")
            filtered_df = filtered_df.dropna(subset=["Date_Start"])

            min_date = filtered_df["Date_Start"].min().date()
            max_date = filtered_df["Date_Start"].max().date()

            st.subheader("📅 Filter by Start Date")
            date_range = st.date_input("Select Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
                mask = (filtered_df["Date_Start"].dt.date >= start_date) & (filtered_df["Date_Start"].dt.date <= end_date)
                filtered_df = filtered_df.loc[mask].copy()
        except Exception as e:
            st.warning(f"⚠ Could not filter by date: {e}")
    else:
        st.warning("⚠ 'Date_Start' column not found — skipping date filter.")

    # --- Add Pre/Post Weight Columns Safely ---
    filtered_df = filtered_df.copy()
    filtered_df["Pre Weight (g)"] = 0.0
    filtered_df["Post Weight (g)"] = 0.0

    # --- Data Editor ---
    st.subheader("📊 Enter Weights")
    editable_columns = ["Pre Weight (g)", "Post Weight (g)"]
    edited_df = st.data_editor(
        filtered_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Pre Weight (g)": st.column_config.NumberColumn("Pre Weight (g)", help="Mass before sampling (grams)"),
            "Post Weight (g)": st.column_config.NumberColumn("Post Weight (g)", help="Mass after sampling (grams)")
        },
        disabled=[col for col in filtered_df.columns if col not in editable_columns],
    )

    # --- PM₂.₅ Calculation Function ---
    def calculate_pm(row):
        try:
            elapsed = float(row["Elapsed Time Diff (min)"])
            flow = float(row["Average Flow Rate (L/min)"])
            pre = float(row["Pre Weight (g)"])
            post = float(row["Post Weight (g)"])
            mass_mg = (post - pre) * 1000

            if elapsed < 1200:
                return "Elapsed < 1200"
            if flow <= 0.05:
                return "Invalid Flow"
            if post < pre:
                return "Post < Pre"

            volume_m3 = (flow * elapsed) / 1000
            if volume_m3 == 0:
                return "Zero Volume"

            conc = (mass_mg * 1000) / volume_m3
            return round(conc, 2)
        except Exception as e:
            return f"Error: {e}"

    # --- Calculate PM₂.₅ ---
    edited_df["PM₂.₅ (µg/m³)"] = edited_df.apply(calculate_pm, axis=1)

    # --- Display Calculated Data ---
    st.subheader("📊 Calculated Results")
    st.dataframe(edited_df, use_container_width=True)

    # --- CSV Export ---
    csv = edited_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Results as CSV",
        data=csv,
        file_name="pm25_results.csv",
        mime="text/csv"
    )

    if st.button("✅ Save Edited DataFrame"):
        try:
            safe_df = edited_df.copy()
            for col in safe_df.select_dtypes(include=["datetime64[ns]", "datetime64", "object"]):
                if pd.api.types.is_datetime64_any_dtype(safe_df[col]):
                    safe_df[col] = safe_df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
            rows_to_save = safe_df.values.tolist()
            st.write(f"First row to save: {rows_to_save[0]}")

            sheet_titles = [ws.title for ws in spreadsheet.worksheets()]
            if CALC_SHEET not in sheet_titles:
                calc_ws = spreadsheet.add_worksheet(title=CALC_SHEET, rows="1000", cols=str(len(safe_df.columns)))
                calc_ws.append_row(safe_df.columns.tolist())
            else:
                calc_ws = spreadsheet.worksheet(CALC_SHEET)

            calc_ws.append_rows(rows_to_save, value_input_option="USER_ENTERED")
            st.success(f"✅ Saved {len(rows_to_save)} rows successfully.")
        except Exception as e:
            st.error(f"❌ Error saving data: {e}")

    if st.checkbox("📖 Show Saved Entries in Sheet"):
        try:
            saved_data = spreadsheet.worksheet(CALC_SHEET).get_all_records(head=1)
            df_saved = pd.DataFrame(saved_data)
            st.dataframe(df_saved, use_container_width=True)
        except Exception as e:
            st.warning(f"⚠ Could not load saved entries: {e}")

