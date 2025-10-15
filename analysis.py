import streamlit as st
import plotly.express as px
import pandas as pd

from db import get_all_observations

def analysis_page():
    st.header("Data Analysis")
    
    observations_df = get_all_observations()
    
    
    if observations_df.empty:
        st.info("No observations available for analysis.")
        return
    
    # Analysis options
    analysis_type = st.selectbox("Select Analysis", 
                                 ["Fare Analysis", "Passenger Trends", "Route Comparison"])
    
    if analysis_type == "Fare Analysis":
        st.subheader("Fare Analysis by Route")
        fare_by_route = observations_df.groupby('route_number')['fare_paid'].agg(['mean', 'min', 'max', 'count'])
        fare_by_route.columns = ['Average Fare', 'Min Fare', 'Max Fare', 'Observations']
        st.dataframe(fare_by_route.head(), use_container_width=True)
        
        fig = px.box(observations_df, x='route_number', y='fare_paid', 
                    title='Fare Distribution by Route',
                    labels={'route_number': 'Route', 'fare_paid': 'Fare (KSh)'})
        st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "Passenger Trends":
        st.subheader("Passenger Count Analysis")
        avg_passengers = observations_df.groupby('route_number')['passenger_count'].mean().sort_values(ascending=False)
        fig = px.bar(x=avg_passengers.index, y=avg_passengers.values,
                    title='Average Passenger Count by Route',
                    labels={'x': 'Route', 'y': 'Avg Passengers'})
        st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "Route Comparison":
        st.subheader("Route Comparison")
        routes = st.multiselect("Select routes to compare", 
                               observations_df['route_number'].unique())
        
        if routes:
            filtered_df = observations_df[observations_df['route_number'].isin(routes)]
            
            metrics = st.selectbox("Metric", ['fare_paid', 'passenger_count'])
            
            fig = px.line(filtered_df, x='observation_date', y=metrics, 
                         color='route_number',
                         title=f'{metrics.replace("_", " ").title()} Over Time',
                         labels={metrics: metrics.replace("_", " ").title()})
            st.plotly_chart(fig, use_container_width=True)