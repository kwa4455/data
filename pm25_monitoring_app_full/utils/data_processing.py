import pandas as pd
import streamlit as st
from datetime import datetime
import time

def convert_timestamps_to_string(df):
    for col in df.select_dtypes(include=['datetime64[ns]']).columns:
        df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
    return df

def filter_dataframe(df, site_filter=None, date_range=None):
    if df.empty:
        return df
    if "Submitted At" in df.columns:
        df["Submitted At"] = pd.to_datetime(df["Submitted At"], errors="coerce")
    if site_filter and site_filter != "All":
        df = df[df["Site"] == site_filter]
    if date_range and len(date_range) == 2:
        start, end = date_range
        df = df[(df["Submitted At"].dt.date >= start) & (df["Submitted At"].dt.date <= end)]
    return df

def merge_start_stop(df):
    start_df = df[df["Entry Type"] == "START"].copy()
    stop_df = df[df["Entry Type"] == "STOP"].copy()
    merge_keys = ["ID", "Site"]
    start_df = start_df.rename(columns=lambda x: f"{x}_Start" if x not in merge_keys else x)
    stop_df = stop_df.rename(columns=lambda x: f"{x}_Stop" if x not in merge_keys else x)
    merged = pd.merge(start_df, stop_df, on=merge_keys, how="inner")

    if "Elapsed Time (min)_Start" in merged and "Elapsed Time (min)_Stop" in merged:
        merged["Elapsed Time (min)_Start"] = pd.to_numeric(merged["Elapsed Time (min)_Start"], errors="coerce")
        merged["Elapsed Time (min)_Stop"] = pd.to_numeric(merged["Elapsed Time (min)_Stop"], errors="coerce")
        merged["Elapsed Time Diff (min)"] = merged["Elapsed Time (min)_Stop"] - merged["Elapsed Time (min)_Start"]

    if "Flow Rate (L/min)_Start" in merged and "Flow Rate (L/min)_Stop" in merged:
        merged["Flow Rate (L/min)_Start"] = pd.to_numeric(merged["Flow Rate (L/min)_Start"], errors="coerce")
        merged["Flow Rate (L/min)_Stop"] = pd.to_numeric(merged["Flow Rate (L/min)_Stop"], errors="coerce")
        merged["Average Flow Rate (L/min)"] = (
            merged["Flow Rate (L/min)_Start"] + merged["Flow Rate (L/min)_Stop"]
        ) / 2

    wind_cols = [
        "Wind Speed_Start", "Wind Direction_Start",
        "Wind Speed_Stop", "Wind Direction_Stop"
    ]
    existing_wind = [col for col in wind_cols if col in merged.columns]
    front_cols = ["ID", "Site"]
    calc_cols = ["Elapsed Time Diff (min)", "Average Flow Rate (L/min)"]
    existing_calc = [col for col in calc_cols if col in merged.columns]
    other_cols = [col for col in merged.columns if col not in front_cols + existing_wind + existing_calc]

    return merged[front_cols + existing_wind + existing_calc + other_cols]