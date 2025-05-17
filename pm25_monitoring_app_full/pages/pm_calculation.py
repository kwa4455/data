import streamlit as st
import pandas as pd
from datetime import datetime
from utils import require_roles, spreadsheet
from constants import MERGED_SHEET, CALC_SHEET

# --- Page Setup ---
st.set_page_config(page_title="PM₂.₅ Calculator", page_icon="🧮")
st.title("🧮 PM₂.₅ Concentration Calculator")
st.write("Enter sample data to calculate PM₂.₅ concentrations in µg/m³ and save valid entries.")

# --- Role Check ---
require_roles("admin", "editor", "collector")

# --- Load Site Info from Merged Records Sheet ---
try:
    merged_data = spreadsheet.worksheet(MERGED_SHEET).get_all_records()
    df_merged = pd.DataFrame(merged_data)
    site_ids = df_merged["ID"].dropna().unique().tolist()
    site_names = df_merged["Site"].dropna().unique().tolist()
except Exception:
    st.error("❌ Failed to load merged records. Make sure the merged sheet exists and is accessible.")
    site_ids = []
    site_names = []
    df_merged = pd.DataFrame()

# --- Input Table Setup ---
rows = st.number_input("Number of entries", min_value=1, max_value=50, value=5)

default_data = {
    "Date": [datetime.today().date()] * rows,
    "Site ID": [""] * rows,
    "Site": [""] * rows,
    "Officer(s)": [""] * rows,
    "Elapsed Time (min)": [1200] * rows,
    "Flow Rate (L/min)": [0.05] * rows,
    "Pre Weight (mg)": [0.0] * rows,
    "Post Weight (mg)": [0.0] * rows
}
df_input = pd.DataFrame(default_data)

# --- Data Editor ---
edited_df = st.data_editor(
    df_input,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Site ID": st.column_config.SelectboxColumn("Site ID", options=site_ids),
        "Site": st.column_config.SelectboxColumn("Site", options=site_names),
        "Date": st.column_config.DateColumn("Date"),
        "Elapsed Time (min)": st.column_config.NumberColumn("Elapsed Time (min)", help="Minimum valid duration is 1200 minutes."),
        "Flow Rate (L/min)": st.column_config.NumberColumn("Flow Rate (L/min)", help="Must be > 0.05"),
        "Pre Weight (mg)": st.column_config.NumberColumn("Pre Weight (mg)", help="Mass before sampling"),
        "Post Weight (mg)": st.column_config.NumberColumn("Post Weight (mg)", help="Mass after sampling"),
    }
)

# --- PM₂.₅ Calculation Function ---
def calculate_pm(row):
    try:
        elapsed = float(row["Elapsed Time (min)"])            # in minutes
        flow = float(row["Flow Rate (L/min)"])                # in L/min
        pre = float(row["Pre Weight (mg)"])                   # in mg
        post = float(row["Post Weight (mg)"])                 # in mg
        mass = post - pre                                     # mg

        if elapsed < 1200:
            return "Elapsed < 1200"
        if flow <= 0:
            return "Invalid Flow"

        volume_m3 = (flow * elapsed) / 1000                   # L → m³
        conc = (mass * 1000) / volume_m3                      # mg → µg, µg/m³

        return round(conc, 2)
    except Exception as e:
        return f"Error: {e}"

# --- Apply Calculation to DataFrame ---
edited_df["PM₂.₅ (µg/m³)"] = edited_df.apply(calculate_pm, axis=1)

# --- Display Results Table ---
st.subheader("📋 Calculated Results")
st.dataframe(edited_df, use_container_width=True)

# --- Save to Google Sheet ---
if st.button("✅ Save Valid Entries"):
    valid_rows = []
    errors = []

    # Step 1: Get merged sheet headers
    try:
        merged_headers = df_merged.columns.tolist()
    except Exception:
        st.error("❌ Failed to get headers from merged sheet.")
        st.stop()

    # Step 2: Ensure calculated fields are added
    calc_fields = ["Pre Weight (mg)", "Post Weight (mg)", "PM₂.₅ (µg/m³)"]
    save_headers = merged_headers.copy()
    for field in calc_fields:
        if field not in save_headers:
            save_headers.append(field)

    # Step 3: Create sheet if missing with headers
    try:
        sheet_titles = [ws.title for ws in spreadsheet.worksheets()]
        if CALC_SHEET not in sheet_titles:
            calc_ws = spreadsheet.add_worksheet(title=CALC_SHEET, rows="1000", cols="50")
            calc_ws.append_row(save_headers)
        else:
            calc_ws = spreadsheet.worksheet(CALC_SHEET)
    except Exception as e:
        st.error(f"❌ Failed to prepare worksheet: {e}")
        st.stop()

    # Step 4: Build and validate rows
    for idx, row in edited_df.iterrows():
        try:
            elapsed = float(row["Elapsed Time (min)"])
            flow = float(row["Flow Rate (L/min)"])
            pre = float(row["Pre Weight (mg)"])
            post = float(row["Post Weight (mg)"])
            pm = calculate_pm(row)
            site_id = str(row["Site ID"]).strip()
            site = str(row["Site"]).strip()
            officer = str(row["Officer(s)"]).strip()
            date = row["Date"]

            # --- Validation ---
            if elapsed < 1200:
                errors.append(f"Row {idx + 1}: Elapsed Time < 1200")
                continue
            if flow <= 0.05:
                errors.append(f"Row {idx + 1}: Flow Rate must be > 0.05")
                continue
            if post < pre:
                errors.append(f"Row {idx + 1}: Post Weight < Pre Weight")
                continue
            if not all([site_id, site, officer]):
                errors.append(f"Row {idx + 1}: Missing required fields (Site ID, Site, Officer)")
                continue

            # Step 5: Build a complete row dict
            row_dict = {key: "" for key in save_headers}

            # Populate known/calculated values
            row_dict["Date"] = str(date)
            row_dict["Site ID"] = site_id
            row_dict["Site"] = site
            row_dict["Officer(s)"] = officer
            row_dict["Elapsed Time (min)"] = elapsed
            row_dict["Flow Rate (L/min)"] = flow
            row_dict["Pre Weight (mg)"] = pre
            row_dict["Post Weight (mg)"] = post
            row_dict["PM₂.₅ (µg/m³)"] = pm

            # Copy any additional fields from merged headers
            for col in merged_headers:
                if col in row and col not in row_dict:
                    row_dict[col] = row[col]

            # Assemble row in header order
            valid_rows.append([row_dict.get(h, "") for h in save_headers])

        except Exception as e:
            errors.append(f"Row {idx + 1}: Error parsing row - {e}")

    # Step 6: Save valid rows
    if valid_rows:
        try:
            calc_ws.append_rows(valid_rows)
            st.success(f"✅ Saved {len(valid_rows)} valid entries.")
        except Exception as e:
            st.error(f"❌ Failed to save data: {e}")
    else:
        st.warning("⚠ No valid rows to save.")

    # Step 7: Show validation errors
    if errors:
        st.error("Some rows were invalid:")
        for e in errors:
            st.text(f"- {e}")
