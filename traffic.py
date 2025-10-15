import streamlit as st
import plotly.express as px
import pandas as pd
import altair as alt
import seaborn as sns
import matplotlib.pyplot as plt
import pydeck as pdk
from datetime import timedelta

from db import get_all_observations, create_connection

def traffic_page():
    st.header("Traffic Analysis")

    observations_df = get_all_observations()
    observations_df["observation_time"] = observations_df["observation_time"].apply(lambda x: str(x).split()[-1])

    def render_simple_filters(observations_df, key_prefix):
        st.text("🕐 Traffic Filters")

        col1, col2 = st.columns([2, 1])

        with col1:
            routes = sorted(observations_df["route_id"].unique())
            selected_routes = st.multiselect(
                "Select route(s):",
                routes,
                default=routes[:3],
                help="Choose one or more routes to view traffic data.",
                key=f"{key_prefix}_routes"
            )

        with col2:
            selected_date = st.date_input(
                "Select date:",
                observations_df["observation_date"].max(),
                help="Pick a specific date to view observations.",
                key=f"{key_prefix}_date"
            )

        observations_df["route_id"] = observations_df["route_id"].astype(int)
        observations_df["observation_date"] = pd.to_datetime(observations_df["observation_date"])

        filtered_df = observations_df[
            (observations_df["route_id"].isin(selected_routes)) &
            (observations_df["observation_date"].dt.date == selected_date)
        ]

        return filtered_df


    # Optional — add a visual divider before analysis content
    # st.divider()
    
    analysis_type = st.selectbox("Select Analysis",
                                 ["Hourly Trends", "Route Heatmap", "Route Stop Map", "Traffic Flow"]
                                 )
    
    if analysis_type == "Hourly Trends":
        filtered_df = render_simple_filters(observations_df, key_prefix="hourly")
        st.subheader("Hourly Average Duration per Route")

        traffic_map = {"Light": 1, "Moderate": 2, "Heavy": 3, "Jam": 4}
        filtered_df["traffic_index"] = filtered_df["traffic_condition"].map(traffic_map)

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
    

    if analysis_type == "Route Heatmap":
        filtered_df = render_simple_filters(observations_df, key_prefix="heatmap")
        st.subheader("Route vs Time of Day (Traffic Condition Heatmap)")

        traffic_map = {"Light": 1, "Moderate": 2, "Heavy": 3, "Jam": 4}
        filtered_df["traffic_index"] = filtered_df["traffic_condition"].map(traffic_map)

        if "observation_time" in filtered_df.columns:
            filtered_df['hour'] = (
                filtered_df['observation_time']
                .astype(str)
                .str.extract(r"(\d+)")
                .astype(float)
                .fillna(0)
                .astype(int)
                )

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
        """Render interactive map with route stops"""
        st.subheader("🗺️ Route Stop Map")
    
        # Get selected routes
        all_routes = sorted(observations_df["route_number"].unique())
        selected_routes = st.multiselect(
            "Select route(s) to view:",
            options=all_routes,
            default=all_routes[:2],  # Default to first two
            help="Choose one or more routes to display stops on the map.",
            key="stopmap_routes"
        )

        if not selected_routes:
            st.warning("Please select at least one route to view the stop map.")
            st.stop()
    
        # Query stops data
        conn = create_connection()
        if not conn:
            st.error("Database connection failed.")
            return
    
        try:
            # Format route numbers for SQL query - handle both strings and numbers
            route_list = ','.join([f"'{str(r)}'" for r in selected_routes])
        
            stops_query = f"""
                SELECT s.stop_name, s.latitude, s.longitude, 
                       s.stop_order, r.route_number, r.route_name
                FROM stops s
                JOIN routes r ON s.route_id = r.route_id
                WHERE r.route_number IN ({route_list})
                AND s.latitude IS NOT NULL 
                AND s.longitude IS NOT NULL
                AND s.latitude != 0
                AND s.longitude != 0
                ORDER BY r.route_number, s.stop_order
            """
        
            # Debug: show query
            # with st.expander("🔍 SQL Query"):
            #     st.code(stops_query, language="sql")
        
            stops_df = pd.read_sql(stops_query, conn)
        
            conn.close()
        
            if stops_df.empty:
                st.info("📍 No geolocation data available for the selected route(s). Add GPS coordinates to stops for map visualization.")
            
                # Show routes without coordinates
                st.subheader("Routes Missing GPS Data")
                conn = create_connection()
                routes_query = f"""
                    SELECT r.route_number, r.route_name, COUNT(s.stop_id) as stop_count,
                           SUM(CASE WHEN s.latitude IS NOT NULL AND s.latitude != 0 THEN 1 ELSE 0 END) as stops_with_gps
                    FROM routes r
                    LEFT JOIN stops s ON r.route_id = s.route_id
                    WHERE r.route_number IN ({route_list})
                    GROUP BY r.route_id, r.route_number, r.route_name
                """
                routes_info = pd.read_sql(routes_query, conn)
                conn.close()
                st.dataframe(routes_info, use_container_width=True)
                return
        
            # Display map options
            map_type = st.radio("Map Style:", ["Simple", "Detailed with PyDeck"], horizontal=True)
        
            if map_type == "Simple":
                # Simple Streamlit map
                stops_df_map = stops_df.rename(columns={"latitude": "lat", "longitude": "lon"})
                st.map(stops_df_map[['lat', 'lon']], zoom=11)
            
            else:
                # PyDeck detailed map
                view_state = pdk.ViewState(
                    latitude=stops_df['latitude'].mean(),
                    longitude=stops_df['longitude'].mean(),
                    zoom=11,
                    pitch=45
                )
            
                # Create color mapping for routes
                unique_routes = stops_df['route_number'].unique()
                colors = px.colors.qualitative.Set1[:len(unique_routes)]
                color_map = {route: colors[i % len(colors)] for i, route in enumerate(unique_routes)}
            
                def hex_to_rgb(hex_color):
                    if not isinstance(hex_color, str):
                        return [255, 0, 0] # default=red
                    hex_color = hex_color.strip()
                    if hex_color.startswith('#'):
                        hex_color = hex_color.lstrip('#')
                    else:
                        return [255, 0, 0]
                    
                    if len(hex_color) != 6:
                        return [255, 0, 0]
                    
                    try:    
                        return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
                    except ValueError:
                        return [255, 0, 0]
            
                stops_df['color'] = stops_df['route_number'].map(
                    lambda x: hex_to_rgb(color_map.get(x, '#FF0000'))
                )
            
                # Scatterplot layer for stops
                layer = pdk.Layer(
                    "ScatterplotLayer",
                    stops_df,
                    get_position=['longitude', 'latitude'],
                    get_color='color',
                    get_radius=100,
                    pickable=True,
                    auto_highlight=True
                )
            
                tooltip = {
                    "html": "<b>Stop:</b> {stop_name}<br/>"
                            "<b>Route:</b> {route_number} - {route_name}<br/>"
                            "<b>Order:</b> {stop_order}",
                    "style": {"backgroundColor": "steelblue", "color": "white"}
                }
            
                deck = pdk.Deck(
                    layers=[layer],
                    initial_view_state=view_state,
                    tooltip=tooltip,
                    map_style='mapbox://styles/mapbox/light-v9'
                )
            
                st.pydeck_chart(deck)
        
            # Display stops table
            st.subheader("Stop Details")
            display_cols = ['route_number', 'stop_order', 'stop_name', 'latitude', 'longitude']
            st.dataframe(stops_df[display_cols], use_container_width=True)
        
        except Exception as e:
            st.error(f"Error loading map data: {e}")
            import traceback
            st.code(traceback.format_exc())
            if conn:
                conn.close()
        
    if analysis_type == "Traffic Flow":

        def preprocess_traffic_data(df):
            """Preprocess observation data for traffic analysis"""
            df = df.copy()
                
            # Convert data types
            df['route_id'] = df['route_id'].astype(int)
            df['observation_date'] = pd.to_datetime(df['observation_date'])
                
            # Extract hour from observation_time
            if 'observation_time' in df.columns:
                df['hour'] = pd.to_datetime(df['observation_time'].astype(str), format='%H:%M:%S', errors='coerce').dt.hour
                df['hour'] = df['hour'].fillna(0).astype(int)
            else:
                df['hour'] = 0
                
            # Map traffic conditions to numeric scale
            traffic_map = {"Light": 1, "Moderate": 2, "Heavy": 3, "Jam": 4}
            df["traffic_index"] = df["traffic_condition"].map(traffic_map)
                
            # Add day of week
            df['day_of_week'] = df['observation_date'].dt.day_name()
                
            # Add time period
            df['time_period'] = df['hour'].apply(get_time_period)
                
            return df


        def get_time_period(hour):
            """Categorize hour into time periods"""
            if 6 <= hour < 9:
                return 'Morning Peak'
            elif 9 <= hour < 12:
                return 'Mid-Morning'
            elif 12 <= hour < 15:
                return 'Afternoon'
            elif 15 <= hour < 19:
                return 'Evening Peak'
            else:
                return 'Night'


        def get_traffic_label(score):
            """Convert numeric traffic score to label"""
            if score < 1.5:
                return "🟢 Light"
            elif score < 2.5:
                return "🟡 Moderate"
            elif score < 3.5:
                return "🟠 Heavy"
            else:
                return "🔴 Jam"


        def render_filters(df):
            """Render filter controls and return filtered dataframe"""
            col1, col2, col3 = st.columns([2, 2, 1])
                
            with col1:
                # Route filter
                route_options = sorted(df["route_number"].dropna().unique())
                if len(route_options) > 0:
                    selected_routes = st.multiselect(
                        "Select route(s):",
                        route_options,
                        default=route_options[:min(3, len(route_options))],
                        help="Choose one or more routes to analyze.",
                        key="select_route"
                    )
                else:
                    st.error("No routes found in data")
                    return pd.DataFrame()
                
            with col2:
                # Date range filter
                min_date = df["observation_date"].min().date()
                max_date = df["observation_date"].max().date()
                    
                # Calculate default date range (last 7 days or all available data)
                days_diff = (max_date - min_date).days
                if days_diff >= 7:
                    default_start = max_date - timedelta(days=7)
                else:
                    default_start = min_date
                    
                # Use single date input if only one date available
                if min_date == max_date:
                    selected_date = st.date_input(
                        "Select date:",
                        value=max_date,
                        min_value=min_date,
                        max_value=max_date,
                        help="Only one date available in the data.",
                        key="select_another_date"
                    )
                    start_date = end_date = selected_date
                else:
                    date_range = st.date_input(
                        "Select date range:",
                        value=(default_start, max_date),
                        min_value=min_date,
                        max_value=max_date,
                        help="Pick a date range to view observations.",
                        key="select_date"
                    )
                        
                    # Handle single date or date range
                    if isinstance(date_range, tuple) and len(date_range) == 2:
                        start_date, end_date = date_range
                    else:
                        start_date = end_date = date_range
                
            with col3:
                # Traffic condition filter
                traffic_conditions = ["All"] + list(df["traffic_condition"].dropna().unique())
                selected_traffic = st.selectbox(
                    "Traffic Condition:",
                    traffic_conditions,
                    help="Filter by traffic condition",
                    key="select_traffic"
                )
                
            # Apply filters
            filtered_df = df[df["route_number"].isin(selected_routes)].copy()
            filtered_df = filtered_df[
                (filtered_df["observation_date"].dt.date >= start_date) &
                (filtered_df["observation_date"].dt.date <= end_date)
            ]
                
            if selected_traffic != "All":
                filtered_df = filtered_df[filtered_df["traffic_condition"] == selected_traffic]
                
            return filtered_df

        def render_traffic_flow(df):
            """Visualize traffic flow patterns"""
            st.subheader("🌊 Traffic Flow Analysis")
                
            # Day of week patterns
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            df['day_of_week'] = pd.Categorical(df['day_of_week'], categories=day_order, ordered=True)
                
            day_traffic = df.groupby('day_of_week')['traffic_index'].mean().reset_index()
                
            fig = px.bar(
                day_traffic,
                x='day_of_week',
                y='traffic_index',
                title='Average Traffic Intensity by Day of Week',
                labels={'day_of_week': 'Day', 'traffic_index': 'Average Traffic Score'},
                color='traffic_index',
                color_continuous_scale='RdYlGn_r'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

            # Data preprocessing
            # observations_df = preprocess_traffic_data(observations_df)
    
            # Filters Section
            # st.subheader("🕐 Traffic Filters")
            # filtered_df = render_filters(observations_df)
    
            if filtered_df.empty:
                st.warning("⚠️ No data available for the selected filters. Try different options.")
                return
                
            # Route comparison
            st.subheader("Route Traffic Comparison")
            route_stats = df.groupby('route_number').agg({
                'traffic_index': ['mean', 'std', 'count']
            }).reset_index()
            route_stats.columns = ['Route', 'Avg Traffic', 'Std Dev', 'Observations']
            route_stats['Traffic Level'] = route_stats['Avg Traffic'].apply(get_traffic_label)
            route_stats = route_stats.sort_values('Avg Traffic', ascending=False)
                
            st.dataframe(route_stats, use_container_width=True, hide_index=True)

        new_observations_df = get_all_observations()
    
        if new_observations_df.empty:
            st.warning("⚠️ No observation data available. Please collect some data first.")
            return
    
        # Data preprocessing
        new_observations_df = preprocess_traffic_data(new_observations_df)
    
        # Filters Section
        st.text("🕐 Traffic Filters")
        filtered_df = render_filters(new_observations_df)
    
        if filtered_df.empty:
            st.warning("⚠️ No data available for the selected filters. Try different options.")
            return
        
        render_traffic_flow(filtered_df)