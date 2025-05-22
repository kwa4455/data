import streamlit as st
import pandas as pd
from datetime import datetime
from resource import spreadsheet
from constants import MERGED_SHEET, CALC_SHEET
from modules.authentication import require_role

# Require authenticated role
def show():
    require_role(["admin", "editor"])
    st.subheader("📥 PM25 Calculation")

# Inject Google Fonts and custom CSS
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
    <style>
    html, body, [class*="css"]  {
        font-family: 'Poppins', sans-serif;
        text-shadow: 0 1px 2px rgba(0,0,0,0.08);
        color: #1f1f1f;
        background-color: #f4f7fa;
    }
    .main > div:first-child h1 {
        color: #0a3d62;
        font-size: 2.8rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.15);
        margin-bottom: 0.5rem;
    }
    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(14px) saturate(160%);
        -webkit-backdrop-filter: blur(14px) saturate(160%);
        border: 1px solid rgba(255, 255, 255, 0.25);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.25);
    }
    section[data-testid="stSidebar"] .st-radio > div {
        background: rgba(255, 255, 255, 0.85);
        color: #000;
        border-radius: 12px;
        padding: 0.4rem 0.6rem;
        margin-bottom: 0.5rem;
        transition: all 0.2s ease;
    }
    section[data-testid="stSidebar"] .st-radio > div:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    .stAlert {
        background-color: rgba(232, 244, 253, 0.9);
        border-left: 6px solid #1f77b4;
        border-radius: 8px;
        padding: 1rem;
    }
    .stSuccess {
        background-color: rgba(230, 255, 230, 0.9);
        border-left: 6px solid #33cc33;
        border-radius: 8px;
        padding: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- Title and Intro ---
st.markdown("""
    <div style='text-align: center;'>
        <h2> 🧶 PM₂.₅ Concentration Calculator </h2>
        <p style='color: grey;'>Enter Pre and Post Weights to calculate PM₂.₅ concentrations in µg/m³.</p>
    </div>
    <hr>
""", unsafe_allow_html=True)

# --- Load Merged Data ---
try:
    merged_data = spreadsheet.worksheet(MERGED_SHEET).get_all_records()
    df_merged = pd.DataFrame(merged_data)
    df_merged.columns = df_merged.columns.str.strip()

    required_cols = {"Elapsed Time Diff (min)", "Average Flow Rate (L/min)"}
    if not required_cols.issubset(df_merged.columns):
        st.error("❌ Required columns missing: 'Elapsed Time Diff (min)', 'Average Flow Rate (L/min)'")
        st.stop()
except Exception as e:
    st.error(f"❌ Failed to load merged sheet: {e}")
    st.stop()

# --- Site Filter ---
if "Site" in df_merged.columns:
    available_sites = sorted(df_merged["Site"].dropna().unique())
    site_options = ["All Sites"] + available_sites
    most_recent_site = df_merged["Site"].dropna().iloc[0] if not df_merged.empty else "All Sites"

    st.subheader("🗺️ Filter by Site")
    selected_site = st.selectbox("📍 Select Site", options=site_options, index=site_options.index(most_recent_site))
    filtered_df = df_merged[df_merged["Site"] == selected_site] if selected_site != "All Sites" else df_merged.copy()
else:
    st.warning("⚠ 'Site' column not found — skipping site filter.")
    filtered_df = df_merged.copy()

# --- Date Filter ---
if "Date _Start" in filtered_df.columns:
    filtered_df["Date _Start"] = pd.to_datetime(filtered_df["Date _Start"], errors="coerce")
    filtered_df.dropna(subset=["Date _Start"], inplace=True)

    min_date = filtered_df["Date _Start"].min().date()
    max_date = filtered_df["Date _Start"].max().date()

    st.subheader("📅 Filter by Start Date")
    date_range = st.date_input("Select Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df["Date _Start"].dt.date >= start_date) &
            (filtered_df["Date _Start"].dt.date <= end_date)
        ]
else:
    st.warning("⚠ 'Date_Start' column not found — skipping date filter.")

# --- Pre/Post Weight Initialization ---
if "Pre Weight (g)" not in filtered_df.columns:
    filtered_df["Pre Weight (g)"] = 0.0
if "Post Weight (g)" not in filtered_df.columns:
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
        mass_mg = (post - pre) * 1000  # g → mg

        if elapsed < 1200 or flow <= 0.05 or post < pre:
            return None

        volume_m3 = (flow * elapsed) / 1000
        return round((mass_mg * 1000) / volume_m3, 2) if volume_m3 != 0 else None
    except:
        return None

# --- Calculate and Append Column ---
edited_df["PM₂.₅ (µg/m³)"] = edited_df.apply(calculate_pm, axis=1)

# --- Display Calculated Table ---
st.subheader("📊 Calculated Results")
st.dataframe(edited_df, use_container_width=True)

# --- Export CSV ---
csv = edited_df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download Results as CSV", csv, "pm25_results.csv", "text/csv")

# --- Save to Google Sheets ---
if st.button("✅ Save Edited DataFrame"):
    try:
        safe_df = edited_df.copy()
        for col in safe_df.select_dtypes(include=["datetime64[ns]", "datetime64"]):
            safe_df[col] = safe_df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

        rows_to_save = safe_df.values.tolist()

        # Ensure worksheet exists
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

# --- Option to Show Saved Data ---
if st.checkbox("📖 Show Saved Entries in Sheet"):
    try:
        saved_data = spreadsheet.worksheet(CALC_SHEET).get_all_records(head=1)
        df_saved = pd.DataFrame(saved_data)
        st.dataframe(df_saved, use_container_width=True)
    except Exception as e:
        st.warning(f"⚠ Could not load saved entries: {e}")

# --- Footer ---
st.markdown("""
    <hr style="margin-top: 40px; margin-bottom:10px">
    <div style='text-align: center; color: grey; font-size: 0.9em;'>
        © 2025 EPA Ghana · Developed by Clement Mensah Ackaah 🦺 · Built with 😍 using Streamlit
    </div>
""", unsafe_allow_html=True)
