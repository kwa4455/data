import streamlit as st
import pandas as pd
from datetime import datetime
from resource import spreadsheet
from constants import MERGED_SHEET, CALC_SHEET, WEIGHTS_SHEET 
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

    # Load merged sheet
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

    sites = sorted(df_merged["Site"].dropna().unique())
    default_site = df_merged["Site"].dropna().iloc[0]
    site_options = ["All Sites"] + sites

    st.subheader("🗺️ Filter by Site")
    selected_site = st.selectbox("📍 Select Site", options=site_options, index=site_options.index(default_site))
    filtered_df = df_merged[df_merged["Site"] == selected_site] if selected_site != "All Sites" else df_merged.copy()

    # Date filter
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

    # Add weight columns
    for col in ["Pre Weight (g)", "Post Weight (g)"]:
        if col not in filtered_df.columns:
            filtered_df[col] = 0.0
        else:
            filtered_df[col] = pd.to_numeric(filtered_df[col], errors="coerce").fillna(0.0)

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

    # PM calculation
    def calculate_pm(row):
        try:
            elapsed = float(row["Elapsed Time Diff (min)"])
            flow = float(row["Average Flow Rate (L/min)"])
            pre = float(row["Pre Weight (g)"])
            post = float(row["Post Weight (g)"])
            mass_mg = (post - pre) * 1000
            if elapsed < 1200: return "Elapsed < 1200"
            if flow <= 0.05: return "Invalid Flow"
            if post < pre: return "Post < Pre"
            volume_m3 = (flow * elapsed) / 1000
            if volume_m3 == 0: return "Zero Volume"
            return (mass_mg * 1000) / volume_m3
        except Exception:
            return "Error"

    edited_df["PM₂.₅ (µg/m³)"] = edited_df.apply(calculate_pm, axis=1)

    st.subheader("📊 Calculated Results")
    st.dataframe(edited_df, use_container_width=True)

    csv = edited_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download as CSV", data=csv, file_name="pm25_results.csv", mime="text/csv")

    # ✅ Auto-sync to both sheets
    if st.button("🔄 Save or Update to Both Sheets"):
        try:
            sync_df = edited_df.copy()
            for col in sync_df.select_dtypes(include=["datetime64[ns]", "datetime64"]):
                sync_df[col] = sync_df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

            # Clean weights
            sync_df = sync_df[(sync_df["Pre Weight (g)"] > 0) & (sync_df["Post Weight (g)"] > 0)].copy()
            if sync_df.empty:
                st.warning("⚠ No valid weight entries to sync.")
                return

            sync_df["Saved_At"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sync_df["unique_key"] = sync_df["Site"].astype(str) + "_" + sync_df["Date_Start"].astype(str) + "_" + sync_df["Time_Start"].astype(str)

            def load_or_create_sheet(sheet_name, cols):
                if sheet_name not in [ws.title for ws in spreadsheet.worksheets()]:
                    ws = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols=str(len(cols)))
                    ws.append_row(cols)
                    return ws, {}
                else:
                    ws = spreadsheet.worksheet(sheet_name)
                    data = ws.get_all_values()
                    df = pd.DataFrame(data[1:], columns=data[0])
                    df["unique_key"] = df["Site"].astype(str) + "_" + df["Date_Start"].astype(str) + "_" + df["Time_Start"].astype(str)
                    return ws, dict(zip(df["unique_key"], df.index))

            # Sync to Weights Sheet
            weights_ws, weights_keys = load_or_create_sheet(WEIGHTS_SHEET, sync_df.drop(columns="unique_key").columns.tolist())
            # Sync to Calculation Sheet
            calc_ws, calc_keys = load_or_create_sheet(CALC_SHEET, sync_df.drop(columns="unique_key").columns.tolist())

            def sync_to_sheet(ws, keys_dict):
                updated, added = 0, 0
                for _, row in sync_df.iterrows():
                    key = row["unique_key"]
                    row_data = row.drop(labels="unique_key").tolist()
                    if key in keys_dict:
                        ws.update(f"A{keys_dict[key] + 2}", [row_data])
                        updated += 1
                    else:
                        ws.append_row(row_data, value_input_option="USER_ENTERED")
                        added += 1
                return updated, added

            w_upd, w_add = sync_to_sheet(weights_ws, weights_keys)
            c_upd, c_add = sync_to_sheet(calc_ws, calc_keys)

            st.success(f"✅ Synced to both sheets:\n"
                       f"- Weights Sheet: {w_upd} updated, {w_add} added\n"
                       f"- PM Calc Sheet: {c_upd} updated, {c_add} added")

        except Exception as e:
            st.error(f"❌ Sync failed: {e}")

    # Optional: Show saved weights
    if st.checkbox("📖 Show Saved Weights Sheet"):
        try:
            saved_weights = spreadsheet.worksheet(WEIGHTS_SHEET).get_all_records(head=1)
            st.dataframe(pd.DataFrame(saved_weights), use_container_width=True)
        except Exception as e:
            st.warning(f"⚠ Could not load weights sheet: {e}")
