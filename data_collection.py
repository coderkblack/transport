import streamlit as st
from datetime import datetime

from db import get_all_routes
from db import add_observation

def data_collection_page():
    st.header("Record Observation")
    
    routes_df = get_all_routes()
    
    if routes_df.empty:
        st.warning("No routes available. Please add a route first.")
        return
    
    route_options = {f"{row['route_number']} - {row['route_name']}": row['route_id'] 
                    for _, row in routes_df.iterrows()}
    
    with st.form("observation_form"):
        selected_route = st.selectbox("Select Route*", list(route_options.keys()))
        route_id = route_options[selected_route]
        
        col1, col2 = st.columns(2)
        
        with col1:
            obs_date = st.date_input("Date*", value=datetime.now())
            obs_time = st.time_input("Time*", value=datetime.now().time())
            passenger_count = st.number_input("Passenger Count", min_value=0, max_value=100, value=0)
        
        with col2:
            fare_paid = st.number_input("Fare Paid (KSh)", min_value=0.0, step=10.0)
            traffic_condition = st.selectbox("Traffic Condition", 
                                            ["Light", "Moderate", "Heavy", "Jam"])
        
        notes = st.text_area("Notes (optional)", placeholder="Any additional observations...")
        
        submitted = st.form_submit_button("Record Observation")
        
        if submitted:
            if add_observation(route_id, obs_date, obs_time, passenger_count, 
                             fare_paid if fare_paid > 0 else None, 
                             traffic_condition, notes if notes else None):
                st.success("Observation recorded successfully!")
            else:
                st.error("Failed to record observation.")