import streamlit as st
import pandas as pd
from datetime import datetime
from resource import (
    load_data_from_sheet,
    add_data,
    merge_start_stop,
    save_merged_data_to_sheet,
    sheet,
    spreadsheet,
    display_and_merge_data,
    show_monitoring_form
)
from constants import MERGED_SHEET,MAIN_SHEET
from modules.authentication import require_role




def show():
    require_role(["admin", "collector", "editor"])
     # Inject custom CSS
    st.markdown("""
        <style>
        body, .stApp {
            font-family: 'Poppins', sans-serif;
            transition: all 0.5s ease;
        }

        /* Light Mode */
        body.light-mode, .stApp.light-mode {
            background: linear-gradient(135deg, #f8fdfc, #d8f3dc);
            color: #1b4332;
        }

        /* Dark Mode */
        body.dark-mode, .stApp.dark-mode {
            background: linear-gradient(135deg, #0e1117, #161b22);
            color: #0000b3;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(12px);
            border-right: 2px solid #74c69d;
            transition: all 0.5s ease;
        }

        /* Buttons */
        .stButton>button, .stDownloadButton>button {
            background: linear-gradient(135deg, #40916c, #52b788);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.7em 1.5em;
            font-weight: bold;
            font-size: 1rem;
            box-shadow: 0 0 15px #52b788;
            transition: 0.3s ease;
        }

        .stButton>button:hover, .stDownloadButton>button:hover {
            background: linear-gradient(135deg, #2d6a4f, #40916c);
            box-shadow: 0 0 25px #74c69d, 0 0 35px #74c69d;
            transform: scale(1.05);
        }

        .stButton>button:active, .stDownloadButton>button:active {
            transform: scale(0.97);
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-thumb {
            background: #74c69d;
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #52b788;
        }

        /* Glowing Title */
        .glow-text {
            text-align: center;
            font-size: 3em;
            color: #52b788;
            text-shadow: 0 0 5px #52b788, 0 0 10px #52b788, 0 0 20px #52b788;
            margin-bottom: 20px;
        }

        /* Graph iframe Glass Effect */
        .element-container iframe {
            background: rgba(255, 255, 255, 0.5) !important;
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 10px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        }

        /* Smooth theme transition */
        html, body, .stApp {
            transition: background 0.5s ease, color 0.5s ease;
        }

        /* Download Button Specific */
        .stDownloadButton>button {
            background: linear-gradient(135deg, #1b4332, #2d6a4f);
            box-shadow: 0 0 10px #1b4332;
        }

        /* Glow Animation Keyframes */
        @keyframes pulse-glow {
            0% { box-shadow: 0 0 15px #74c69d, 0 0 30px #52b788; }
            50% { box-shadow: 0 0 25px #40916c, 0 0 45px #2d6a4f; }
            100% { box-shadow: 0 0 15px #74c69d, 0 0 30px #52b788; }
        }

        @keyframes pulse-glow-dark {
            0% { box-shadow: 0 0 15px #58a6ff, 0 0 30px #79c0ff; }
            50% { box-shadow: 0 0 25px #3b82f6, 0 0 45px #2563eb; }
            100% { box-shadow: 0 0 15px #58a6ff, 0 0 30px #79c0ff; }
        }

        .custom-table-wrapper {
            background: rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(12px);
            border-radius: 12px;
            padding: 1rem;
            margin-top: 1rem;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
            animation: fade-glass 0.5s ease-in-out;
            transition: all 0.3s ease-in-out;
        }

        body.dark-mode .custom-table-wrapper,
        .stApp.dark-mode .custom-table-wrapper {
            background: rgba(30, 30, 30, 0.6);
            box-shadow: 0 8px 25px rgba(255, 255, 255, 0.05);
        }

        @keyframes fade-glass {
            0% {
                opacity: 0;
                transform: translateY(10px);
            }
            100% {
                opacity: 1;
                transform: translateY(0);
            }
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style='text-align: center;'>
            <h2>🦚 Field Monitoring Data Entry</h2>
            <p style='color: grey;'> Use this page to input daily observations, instrument readings, and site information.</p>
        </div>
        <hr>
    """, unsafe_allow_html=True)
    
    
    ids = ["", '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
    site_id_map = {
        '1': 'Kaneshie First Light',
        '2': 'Tetteh Quarshie',
        '3': 'Achimota',
        '4': 'La',
        '5': 'Mallam Market',
        '6': 'Graphic Road',
        '7': 'Weija',
        '8': 'Kasoa',
        '9': 'Tantra Hill',
        '10': 'Amasaman'
    }
    officers = ['Obed Korankye', 'Clement Ackaah', 'Peter Ohene-Twum', 'Benjamin Essien', 'Mawuli Amegah']
    wind_directions = ["", "N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    weather_conditions = ["", "Sunny", "Cloudy", "Partly Cloudy", "Rainy", "Windy", "Hazy", "Stormy", "Foggy"]

    entry_type = st.selectbox("📝 Select Entry Type", ["", "START", "STOP"], key="entry_type_selectbox")

    
    if st.checkbox("📖 Show Submitted Monitoring Records", key="submitted_records_checkbox"):
        try:
            df = load_data_from_sheet(sheet)
            df_saved = display_and_merge_data(df, spreadsheet, MERGED_SHEET)
            st.markdown("<div class='custom-table-wrapper'>", unsafe_allow_html=True)
            st.dataframe(df_saved, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"⚠ Could not load Submitted Monitoring Records: {e}")

     # --- Footer ---
    st.markdown("""
        <hr style="margin-top: 40px; margin-bottom:10px">
        <div style='text-align: center; color: grey; font-size: 0.9em;'>
            © 2025 EPA Ghana · Developed by Clement Mensah Ackaah 🦺 · Built with 😍 using Streamlit | 
            <a href="mailto:clement.ackaah@epa.gov.gh">Contact Support</a>
        </div>
    """, unsafe_allow_html=True)
