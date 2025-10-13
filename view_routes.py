import streamlit as st

from db import get_all_routes
from db import get_route_by_id
from db import get_stops_for_route

def view_routes_page():
    st.subheader("View All Routes")
    
    routes_df = get_all_routes()
    
    if routes_df.empty:
        st.info("No routes added yet.")
        return
    
    st.dataframe(routes_df.head(), use_container_width=True)

    st.divider()
    
    # Route details
    st.subheader("Route Details")
    route_options = {f"{row['route_number']} - {row['route_name']}": row['route_id'] 
                    for _, row in routes_df.iterrows()}
    
    selected_route = st.selectbox("Select a route to view details", list(route_options.keys()))
    route_id = route_options[selected_route]
    
    route = get_route_by_id(route_id)
    if route:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Route Number:** {route['route_number']}")
            st.write(f"**Route Name:** {route['route_name']}")
            st.write(f"**Start Point:** {route['start_point']}")
            st.write(f"**End Point:** {route['end_point']}")
        
        with col2:
            st.write(f"**Distance:** {route['distance_km']} km" if route['distance_km'] else "**Distance:** N/A")
            st.write(f"**Est. Duration:** {route['estimated_duration']} min" if route['estimated_duration'] else "**Est. Duration:** N/A")
            st.write(f"**Fare Range:** KSh {route['fare_range']}" if route['fare_range'] else "**Fare Range:** N/A")
        
        # Show stops
        stops_df = get_stops_for_route(route_id)
        if not stops_df.empty:
            st.subheader("Stops")
            st.dataframe(stops_df[['stop_order', 'stop_name']], use_container_width=True)
