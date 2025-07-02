import streamlit as st
import pandas as pd
from datetime import datetime
from resource import spreadsheet
from constants import MERGED_SHEET, CALC_SHEET
from modules.authentication import require_role
from gspread.exceptions import WorksheetNotFound

def show():
    require_role(["admin", "officer"])

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

    # --- Load merged sheet ---
    try:
        raw_data = spreadsheet.worksheet(MERGED_SHEET).get_all_values()
        df_merged = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        df_merged.columns = df_merged.columns.str.strip().str.replace('\s+', ' ', regex=True)

        required_cols = {"Elapsed Time Diff (min)", "Average Flow Rate (L/min)", "Site", "Date_Start", "Time_Start"}
        if not required_cols.issubset(df_merged.columns):
            st.error(f"❌ Missing columns: {required_cols - set(df_merged.columns)}")
            st.stop()
    except Exception as e:
        st.error(f"❌ Could not load merged sheet: {e}")
        st.stop()

    # --- Filter by Site ---
    sites = sorted(df_merged["Site"].dropna().unique())
    default_site = df_merged["Site"].dropna().iloc[0]
    site_options = ["All Sites"] + sites

    st.subheader("🗺️ Filter by Site")
    selected_site = st.selectbox("📍 Select Site", options=site_options, index=site_options.index(default_site))
    filtered_df = df_merged[df_merged["Site"] == selected_site] if selected_site != "All Sites" else df_merged.copy()

    # --- Filter by Date Range ---
    try:
        filtered_df["Date_Start"] = pd.to_datetime(filtered_df["Date_Start"], errors="coerce")
        filtered_df = filtered_df.dropna(subset=["Date_Start"])
        min_date = filtered_df["Date_Start"].min().date()
        max_date = filtered_df["Date_Start"].max().date()

        st.subheader("📅 Filter by Start Date")
        date_range = st.date_input("Select Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        if isinstance(date_range, tuple):
            start_date, end_date = date_range
            filtered_df = filtered_df[
                (filtered_df["Date_Start"].dt.date >= start_date) &
                (filtered_df["Date_Start"].dt.date <= end_date)
            ]
    except Exception as e:
        st.warning(f"⚠ Could not filter by date: {e}")

    # --- Add Pre/Post columns if missing ---
    for col in ["Pre Weight (g)", "Post Weight (g)"]:
        if col not in filtered_df.columns:
            filtered_df[col] = 0.0
        else:
            filtered_df[col] = pd.to_numeric(filtered_df[col], errors="coerce").fillna(0.0)

    # --- Editable Table ---
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
        except Exception:
            return "Error"

    edited_df["PM₂.₅ (µg/m³)"] = edited_df.apply(calculate_pm, axis=1)

    # --- Show Table ---
    st.subheader("📊 Calculated Results")
    st.dataframe(edited_df, use_container_width=True)

    # --- Download CSV ---
    csv = edited_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download as CSV", data=csv, file_name="pm25_results.csv", mime="text/csv")

    # --- Partial Sync Button ---
    if st.button("🔄 Sync to PM Calculation Sheet (Partial Update)"):
        try:
            sync_df = edited_df.copy()
            for col in sync_df.select_dtypes(include=["datetime64[ns]", "datetime64"]):
                sync_df[col] = sync_df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
            sync_df = sync_df[pd.to_numeric(sync_df["PM₂.₅ (µg/m³)"], errors="coerce").notna()].copy()

            # Create unique key for matching
            sync_df["unique_key"] = sync_df["Site"].astype(str) + "_" + sync_df["Date_Start"].astype(str) + "_" + sync_df["Time_Start"].astype(str)

            # Load existing data
            sheet_titles = [ws.title for ws in spreadsheet.worksheets()]
            if CALC_SHEET not in sheet_titles:
                calc_ws = spreadsheet.add_worksheet(title=CALC_SHEET, rows="1000", cols=str(len(sync_df.columns)))
                calc_ws.append_row(sync_df.drop(columns="unique_key").columns.tolist())
                existing_keys = {}
                rows_data = []
            else:
                calc_ws = spreadsheet.worksheet(CALC_SHEET)
                existing_data = calc_ws.get_all_values()
                headers = existing_data[0]
                rows_data = existing_data[1:]
                df_existing = pd.DataFrame(rows_data, columns=headers)
                df_existing["unique_key"] = df_existing["Site"].astype(str) + "_" + df_existing["Date_Start"].astype(str) + "_" + df_existing["Time_Start"].astype(str)
                existing_keys = dict(zip(df_existing["unique_key"], df_existing.index))

            updates = 0
            additions = 0

            for _, row in sync_df.iterrows():
                row_data = row.drop(labels="unique_key").tolist()
                key = row["unique_key"]
                if key in existing_keys:
                    row_number = existing_keys[key] + 2  # account for header and 1-based indexing
                    calc_ws.update(f"A{row_number}", [row_data])
                    updates += 1
                else:
                    calc_ws.append_row(row_data, value_input_option="USER_ENTERED")
                    additions += 1

            st.success(f"✅ Sync complete: {updates} updated, {additions} added.")
        except Exception as e:
            st.error(f"❌ Sync failed: {e}")

    # --- Show Sheet ---
    if st.checkbox("📖 Show Synced PM Calculation Sheet"):
        try:
            saved_data = spreadsheet.worksheet(CALC_SHEET).get_all_records(head=1)
            df_saved = pd.DataFrame(saved_data)
            st.dataframe(df_saved, use_container_width=True)
        except Exception as e:
            st.warning(f"⚠ Could not load synced entries: {e}")
