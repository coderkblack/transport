import streamlit as st

from db import add_route

def add_route_page():
    st.header("Add New Route")
    
    with st.form("add_route_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            route_number = st.text_input("Route Number*", placeholder="e.g., 46, 33, 111")
            route_name = st.text_input("Route Name*", placeholder="e.g., City-Ngong Road")
            start_point = st.text_input("Start Point*", placeholder="e.g., CBD/Railways")
        
        with col2:
            end_point = st.text_input("End Point*", placeholder="e.g., Karen/Ngong")
            distance_km = st.number_input("Distance (km)", min_value=0.0, step=0.1)
            estimated_duration = st.number_input("Est. Duration (minutes)", min_value=0, step=5)
        
        fare_range = st.text_input("Fare Range", placeholder="e.g., 50-80")
        
        submitted = st.form_submit_button("Add Route")
        
        if submitted:
            if route_number and route_name and start_point and end_point:
                if add_route(route_number, route_name, start_point, end_point, 
                           distance_km if distance_km > 0 else None, 
                           estimated_duration if estimated_duration > 0 else None, 
                           fare_range if fare_range else None):
                    st.success(f"Route {route_number} added successfully!")
                else:
                    st.error("Failed to add route. Check if route number already exists.")
            else:
                st.error("Please fill in all required fields (marked with *).")