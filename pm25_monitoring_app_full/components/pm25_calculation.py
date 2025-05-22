import streamlit as st
import pandas as pd
from datetime import datetime
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
from constants import MERGED_SHEET, CALC_SHEET
from modules.authentication import require_role

def show():
    require_role(["admin", "editor"])
    st.subheader("📥 PM25 Calculation")
    st.write("This is where the data entry form would go.")


# Inject Google Fonts and custom CSS for glassmorphism and font clarity
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">

    <style>
    /* === Global Font and Text Effects === */
    html, body, [class*="css"]  {
        font-family: 'Poppins', sans-serif;
        text-shadow: 0 1px 2px rgba(0,0,0,0.08);
        color: #1f1f1f;
        background-color: #f4f7fa;
    }

    /* === App Title Styling === */
    .main > div:first-child h1 {
        color: #0a3d62;
        font-size: 2.8rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.15);
        margin-bottom: 0.5rem;
    }

    /* === Sidebar Glass Effect === */
    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(14px) saturate(160%);
        -webkit-backdrop-filter: blur(14px) saturate(160%);
        border: 1px solid rgba(255, 255, 255, 0.25);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.25);
    }

    /* === Sidebar Navigation Styling === */
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

    /* === Info box styling === */
    .stAlert {
        background-color: rgba(232, 244, 253, 0.9);
        border-left: 6px solid #1f77b4;
        border-radius: 8px;
        padding: 1rem;
    }

    /* === Success message styling === */
    .stSuccess {
        background-color: rgba(230, 255, 230, 0.9);
        border-left: 6px solid #33cc33;
        border-radius: 8px;
        padding: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- Page Title ---
st.markdown(
    """
    <div style='text-align: center;'>
        <h2> 🧶 PM₂.₅ Concentration Calculator </h2>
        <p style='color: grey;'>Enter Pre and Post Weights to calculate PM₂.₅ concentrations in µg/m³ .</p>
    </div>
    <hr>
    """,
    unsafe_allow_html=True
)

st.write("Enter Pre and Post Weights to calculate PM₂.₅ concentrations in µg/m³.")



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
if "Date _Start" in filtered_df.columns:
    try:
        filtered_df = filtered_df.copy()
        filtered_df["Date _Start"] = pd.to_datetime(filtered_df["Date _Start"], errors="coerce")
        filtered_df = filtered_df.dropna(subset=["Date _Start"])

        min_date = filtered_df["Date _Start"].min().date()
        max_date = filtered_df["Date _Start"].max().date()

        st.subheader("📅 Filter by Start Date")
        date_range = st.date_input("Select Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            mask = (filtered_df["Date _Start"].dt.date >= start_date) & (filtered_df["Date _Start"].dt.date <= end_date)
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
        mass_mg = (post - pre) * 1000  # g → mg

        if elapsed < 1200:
            return "Elapsed < 1200"
        if flow <= 0.05:
            return "Invalid Flow"
        if post < pre:
            return "Post < Pre"

        volume_m3 = (flow * elapsed) / 1000  # L → m³
        if volume_m3 == 0:
            return "Zero Volume"

        conc = (mass_mg * 1000) / volume_m3  # µg/m³
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
        # Make a copy to avoid modifying original DataFrame
        safe_df = edited_df.copy()

        # Convert only datetime columns to strings
        for col in safe_df.select_dtypes(include=["datetime64[ns]", "datetime64", "object"]):
            if pd.api.types.is_datetime64_any_dtype(safe_df[col]):
                safe_df[col] = safe_df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

        # Convert to list of lists for Google Sheets
        rows_to_save = safe_df.values.tolist()

        # Debug: Show first row
        st.write(f"First row to save: {rows_to_save[0]}")

        # Ensure worksheet exists
        sheet_titles = [ws.title for ws in spreadsheet.worksheets()]
        if CALC_SHEET not in sheet_titles:
            calc_ws = spreadsheet.add_worksheet(title=CALC_SHEET, rows="1000", cols=str(len(safe_df.columns)))
            calc_ws.append_row(safe_df.columns.tolist())  # Header
        else:
            calc_ws = spreadsheet.worksheet(CALC_SHEET)

        # Append rows
        calc_ws.append_rows(rows_to_save, value_input_option="USER_ENTERED")
        st.success(f"✅ Saved {len(rows_to_save)} rows successfully.")
    except Exception as e:
        st.error(f"❌ Error saving data: {e}")


# --- Show Saved Entries ---
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
