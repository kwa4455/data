import streamlit as st
import pandas as pd
from datetime import datetime
from resource import spreadsheet
from constants import MERGED_SHEET, CALC_SHEET
from modules.authentication import require_role
from gspread.exceptions import APIError, WorksheetNotFound

def show():
    require_role(["admin", "officer"])

    # --- Page Title ---
    st.markdown("""
        <style>
            @media (prefers-color-scheme: dark) {
                .pm25-subtitle {
                    color: white;
                }
            }
            @media (prefers-color-scheme: light) {
                .pm25-subtitle {
                    color: black;
                }
            }
        </style>

        <div style='text-align: center;'>
            <h2> 🧶 PM₂.₅ Concentration Calculator </h2>
            <p class='pm25-subtitle'>Enter Pre and Post Weights to calculate PM₂.₅ concentrations in µg/m³.</p>
        </div>
        <hr>
    """, unsafe_allow_html=True)

    # --- Load Merged Sheet Data ---
    try:
        raw_data = spreadsheet.worksheet(MERGED_SHEET).get_all_values()
        df_merged = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        df_merged.columns = df_merged.columns.str.strip().str.replace('\s+', ' ', regex=True)

        required_cols = {"Elapsed Time Diff (min)", "Average Flow Rate (L/min)"}
        if not required_cols.issubset(df_merged.columns):
            st.error(f"❌ Missing required columns: {required_cols - set(df_merged.columns)}")
            st.stop()
    except Exception as e:
        st.error(f"❌ Could not load merged sheet: {e}")
        st.stop()

    # --- Filter by Site ---
    if "Site" in df_merged.columns:
        sites = sorted(df_merged["Site"].dropna().unique())
        options = ["All Sites"] + sites
        default = df_merged["Site"].dropna().iloc[0] if not df_merged.empty else "All Sites"

        st.subheader("🗺️ Filter by Site")
        selected_site = st.selectbox("📍 Select Site", options=options, index=options.index(default))
        filtered_df = df_merged[df_merged["Site"] == selected_site] if selected_site != "All Sites" else df_merged.copy()
    else:
        st.warning("⚠ 'Site' column not found.")
        filtered_df = df_merged.copy()

    # --- Filter by Date ---
    if "Date_Start" in filtered_df.columns:
        try:
            filtered_df["Date_Start"] = pd.to_datetime(filtered_df["Date_Start"], errors="coerce")
            filtered_df = filtered_df.dropna(subset=["Date_Start"])
            min_date = filtered_df["Date_Start"].min().date()
            max_date = filtered_df["Date_Start"].max().date()

            st.subheader("📅 Filter by Start Date")
            date_range = st.date_input("Select Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

            if isinstance(date_range, tuple):
                start_date, end_date = date_range
                mask = (filtered_df["Date_Start"].dt.date >= start_date) & (filtered_df["Date_Start"].dt.date <= end_date)
                filtered_df = filtered_df[mask]
        except Exception as e:
            st.warning(f"⚠ Date filter failed: {e}")

    # --- Add/Edit Pre/Post Weight Columns ---
    filtered_df["Pre Weight (g)"] = filtered_df.get("Pre Weight (g)", 0.0)
    filtered_df["Post Weight (g)"] = filtered_df.get("Post Weight (g)", 0.0)

    # --- Data Editor ---
    st.subheader("📊 Enter Weights")
    editable_cols = ["Pre Weight (g)", "Post Weight (g)"]
    edited_df = st.data_editor(
        filtered_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Pre Weight (g)": st.column_config.NumberColumn("Pre Weight (g)", help="Mass before sampling (grams)"),
            "Post Weight (g)": st.column_config.NumberColumn("Post Weight (g)", help="Mass after sampling (grams)")
        },
        disabled=[col for col in filtered_df.columns if col not in editable_cols],
    )

    # --- PM₂.₅ Calculation ---
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

    edited_df["PM₂.₅ (µg/m³)"] = edited_df.apply(calculate_pm, axis=1)

    # --- Display Calculated Results ---
    st.subheader("📊 Calculated Results")
    st.dataframe(edited_df, use_container_width=True)

    # --- Download Button ---
    csv = edited_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download as CSV", data=csv, file_name="pm25_results.csv", mime="text/csv")

    # --- Save to PM CALC Sheet ---
    if st.button("✅ Save Results to PM Calculation Sheet"):
        try:
            save_df = edited_df.copy()
            for col in save_df.select_dtypes(include=["datetime64", "datetime64[ns]"]):
                save_df[col] = save_df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

            rows = save_df.values.tolist()

            # Ensure header exists
            sheet_titles = [ws.title for ws in spreadsheet.worksheets()]
            if CALC_SHEET not in sheet_titles:
                calc_ws = spreadsheet.add_worksheet(title=CALC_SHEET, rows="1000", cols=str(len(save_df.columns)))
                calc_ws.append_row(save_df.columns.tolist())
            else:
                calc_ws = spreadsheet.worksheet(CALC_SHEET)

            calc_ws.append_rows(rows, value_input_option="USER_ENTERED")
            st.success(f"✅ Saved {len(rows)} rows to {CALC_SHEET}.")
        except Exception as e:
            st.error(f"❌ Failed to save: {e}")

    # --- Optional: Show Saved Entries ---
    if st.checkbox("📖 Show Saved PM Calculation Entries"):
        try:
            saved_data = spreadsheet.worksheet(CALC_SHEET).get_all_records(head=1)
            df_saved = pd.DataFrame(saved_data)
            st.dataframe(df_saved, use_container_width=True)
        except Exception as e:
            st.warning(f"⚠ Could not load saved entries: {e}")
