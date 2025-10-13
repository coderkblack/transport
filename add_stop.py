import streamlit as st

from db import get_all_routes
from db import get_stops_for_route
from db import add_stop

def add_stops_page():
    st.header("Add Stops to Route")
    
    routes_df = get_all_routes()
    
    if routes_df.empty:
        st.warning("No routes available. Please add a route first.")
        return
    
    route_options = {f"{row['route_number']} - {row['route_name']}": row['route_id'] 
                    for _, row in routes_df.iterrows()}
    
    selected_route = st.selectbox("Select Route", list(route_options.keys()))
    route_id = route_options[selected_route]
    
    # Show existing stops
    existing_stops = get_stops_for_route(route_id)
    if not existing_stops.empty:
        st.subheader("Existing Stops")
        st.dataframe(existing_stops[['stop_name', 'stop_order']].head(), use_container_width=True)
        next_order = existing_stops['stop_order'].max() + 1
    else:
        st.info("No stops added yet for this route.")
        next_order = 1
    
    # Add new stop
    st.subheader("Add New Stop")
    with st.form("add_stop_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            stop_name = st.text_input("Stop Name*", placeholder="e.g., Kencom")
            stop_order = st.number_input("Stop Order", min_value=1, value=next_order)
        
        with col2:
            latitude = st.number_input("Latitude (optional)", format="%.8f", value=0.0)
            longitude = st.number_input("Longitude (optional)", format="%.8f", value=0.0)
        
        submitted = st.form_submit_button("Add Stop")
        
        if submitted:
            if stop_name:
                lat = latitude if latitude != 0.0 else None
                lon = longitude if longitude != 0.0 else None
                if add_stop(route_id, stop_name, stop_order, lat, lon):
                    st.success(f"Stop '{stop_name}' added successfully!")
                    st.rerun()
                else:
                    st.error("Failed to add stop.")
            else:
                st.error("Please enter a stop name.")