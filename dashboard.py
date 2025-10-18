import streamlit as st
import pandas as pd
from db import get_all_routes, get_all_observations, get_stops_for_route

def show_dashboard():
    st.subheader("Welcome to the Nairobi Routes Dashboard")

    st.markdown("""
    This platform provides insights and management tools for **Nairobi Matatu Routes**.  
    Use the navigation to view, add, or analyze routes with detailed **Fare Ranges**, **Durations**, and **Distances**.
    """)

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    # --- Get data ---
    routes_df = get_all_routes()
    observations_df = get_all_observations()

    # 🧩 Handle missing or renamed time columns safely
    if not observations_df.empty:
        time_col = "observation_time"
        if "observation_time_local" in observations_df.columns:
            time_col = "observation_time_local"

        # Convert to HH:MM format safely
        observations_df["Formatted Time"] = observations_df[time_col].apply(
            lambda x: pd.to_datetime(x).strftime("%H:%M") if pd.notnull(x) else ""
        )

    # --- Stats cards ---
    with col1:
        st.metric("Total Routes", len(routes_df))

    with col2:
        # Count all stops
        stop_count = 0
        for _, route in routes_df.iterrows():
            stops = get_stops_for_route(route["route_id"])
            stop_count += len(stops)
        st.metric("Total Stops", stop_count)

    with col3:
        st.metric("Observations", len(observations_df))

    with col4:
        if not observations_df.empty and "fare_paid" in observations_df.columns:
            avg_fare = observations_df["fare_paid"].mean()
            st.metric("Avg Fare", f"KSh {avg_fare:.2f}")

    # --- Recent Observations Table ---
    st.subheader("Recent Observations")

    if not observations_df.empty:
        display_cols = [
            "route_number", "route_name", "observation_date", 
            "Formatted Time", "passenger_count", "fare_paid", "traffic_condition", "notes"
        ]
        # Only show columns that actually exist
        display_cols = [c for c in display_cols if c in observations_df.columns]

        st.dataframe(observations_df[display_cols].head(), use_container_width=True)
    else:
        st.info("No observations recorded yet.")
