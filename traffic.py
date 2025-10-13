import streamlit as st
import plotly.express as px
import pandas as pd
import altair as alt
import seaborn as sns
import matplotlib.pyplot as plt
import pydeck as pdk

from db import get_all_observations
from db import create_connection

def traffic_page():
    st.header("Traffic Analysis")

    observations_df = get_all_observations()

    st.subheader("🕐 Traffic Filters")

    # Create horizontal filter layout
    col1, col2 = st.columns([2, 1])

    with col1:
        routes = sorted(observations_df["route_id"].unique())
        selected_routes = st.multiselect(
            "Select route(s):",
            routes,
            default=routes[:3],
            help="Choose one or more routes to view traffic data."
        )

    with col2:
        selected_date = st.date_input(
            "Select date:",
            observations_df["observation_date"].max(),
            help="Pick a specific date to view observations."
        )

    # Filter logic
    observations_df['route_id'] = observations_df['route_id'].astype(int)
    observations_df['observation_date'] = pd.to_datetime(observations_df['observation_date'])

    filtered_df = observations_df[
        (observations_df["route_id"].isin(selected_routes)) &
        (observations_df["observation_date"].dt.date == selected_date)
    ]

    # filtered_df = observations_df[observations_df["route_id"] == 13]
    # st.write(filtered_df)

    if filtered_df.empty:
        st.warning("⚠️ No data available for the selected filters.")
        st.stop()
    else:
        st.write(filtered_df.head())
        # st.success(f"✅ Showing {len(filtered_df)} records for {selected_date}.")

    # Optional — add a visual divider before analysis content
    st.divider()
    
    analysis_type = st.selectbox("Select Analysis",
                                 ["Hourly Trends", "Route Heatmap", "Route Stop Map"]
                                 )
    
    # Encode traffic conditions into numeric intensity (for plotting)
    traffic_map = {"Light": 1, "Moderate": 2, "Heavy": 3, "Jam": 4}
    filtered_df["traffic_index"] = filtered_df["traffic_condition"].map(traffic_map)
    
    if analysis_type == "Hourly Trends":
        st.subheader("Hourly Average Duration per Route")

        if "observation_time" in filtered_df.columns:
            filtered_df['hour'] = (
                filtered_df['observation_time']
                .astype(str)
                .str.extract(r"(\d+)")
                .astype(float)
                .fillna(0)
                .astype(int)
                )
        else:
            st.error("'observation_time' column not found in the data")
            st.stop

        if "hour" not in filtered_df.columns:
            st.error("'hour' column missing after extraction")
            st.stop()

        chart = (
        alt.Chart(filtered_df)
        .mark_area(opacity=0.6)
        .encode(
            x=alt.X("hour:O", sort='ascending', title="Hour of Day"),
            y=alt.Y("mean(traffic_index):Q", title="Average Traffic Intensity (1-4)"),
            color="route_number:N",
            tooltip=["route_number", "hour", "mean(traffic_index)"]
        )
        .properties(
            height=400,
            title="Traffic volume Trends by Hour")
        )

        st.altair_chart(chart, use_container_width=True)

        st.caption("Traffic intensity scale: 1 = Light, 2 = Moderate, 3 = Heavy, 4 = Jam")
    
    # Route Heatmap
    # if "hour" not in filtered_df.columns:
    #     st.error("'hour' column missing after extraction")
    #     st.stop()

    if "observation_time" in filtered_df.columns:
        filtered_df['hour'] = (
            filtered_df['observation_time']
            .astype(str)
            .str.extract(r"(\d+)")
            .astype(float)
            .fillna(0)
            .astype(int)
            )

    if analysis_type == "Route Heatmap":
        st.subheader("Route vs Time of Day (Traffic Condition Heatmap)")

        heat_df = (
            filtered_df.groupby(["route_number", "hour"])["traffic_index"].mean()
            .unstack()
            .fillna(0)
        )

        fig = px.imshow(
            heat_df,
            labels=dict(x="Hour of Day", y="Route Number", color="Traffic Intensity"),
            title="Traffic Intensity Heatmap",
            color_continuous_scale="RdYlGn_r",
            aspect="auto"
        )
        fig.update_layout(height=max(400, len(heat_df) * 40))
        st.plotly_chart(fig, use_container_width=True)

    # Route Stop Map
    if analysis_type == "Route Stop Map":
        st.subheader("Route Stop Map")

        engine = create_connection()
        stops_query = f"""
            SELECT s.stop_name, s.latitude, s.longitude, r.route_number
            FROM stops s
            JOIN routes r ON s.route_id = r.route_id
            WHERE r.route_number IN ({','.join([f"'{r}'" for r in selected_routes])})
        """
        stops_df = pd.read_sql(stops_query, engine)

        if not stops_df.empty:
            st.map(stops_df.rename(columns={"latitude": "lat", "longitude": "lon"}))
        else:
            st.info("No geolocation data available for the selected route(s).")