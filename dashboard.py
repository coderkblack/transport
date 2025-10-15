import streamlit as st
import pandas as pd

from db import get_all_routes
from db import get_all_observations
from db import create_connection

def show_dashboard():
    # st.header("Dashboard")

    st.subheader("Welcome to the Nairobi Routes Dashboard")

    st.markdown("""
    This platform provides insights and management tools for **Nairobi Matatu Routes**.  
    Use the navigation to view, add, or analyze routes with detailed **Fare Ranges**, **Durations**, and **Distances**.
    """)

    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Get statistics
    routes_df = get_all_routes()
    observations_df = get_all_observations()
    observations_df["observation_time"] = observations_df["observation_time"].apply(lambda x: str(x).split()[-1])
    
    with col1:
        st.metric("Total Routes", len(routes_df))
    
    with col2:
        conn = create_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM stops")
            stop_count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            st.metric("Total Stops", stop_count)
    
    with col3:
        st.metric("Observations", len(observations_df))
    
    with col4:
        if not observations_df.empty:
            avg_fare = observations_df['fare_paid'].mean()
            st.metric("Avg Fare", f"KSh {avg_fare:.2f}")
    
    # Recent observations
    st.subheader("Recent Observations")
    if not observations_df.empty:
        st.dataframe(observations_df.head(), use_container_width=True)
    else:
        st.info("No observations recorded yet.")