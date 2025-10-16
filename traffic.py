import streamlit as st
import plotly.express as px
import pandas as pd
import altair as alt
import pydeck as pdk
from datetime import timedelta
from db import supabase, get_all_observations, get_stops_for_route

def traffic_page():
    st.header("Traffic Analysis")

    observations_df = get_all_observations()
    if observations_df.empty:
        st.warning("⚠️ No observation data available.")
        return

    observations_df["observation_time"] = observations_df["observation_time"].apply(lambda x: str(x).split()[-1])

    # --- FILTERS ---
    def render_simple_filters(df, key_prefix):
        st.text("🕐 Traffic Filters")

        col1, col2 = st.columns([2, 1])

        with col1:
            routes = sorted(df["route_id"].unique())
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
                df["observation_date"].max(),
                help="Pick a specific date to view observations.",
                key=f"{key_prefix}_date"
            )

        df["route_id"] = df["route_id"].astype(int)
        df["observation_date"] = pd.to_datetime(df["observation_date"])

        filtered_df = df[
            (df["route_id"].isin(selected_routes)) &
            (df["observation_date"].dt.date == selected_date)
        ]

        return filtered_df

    # --- MAIN ANALYSIS SELECTOR ---
    analysis_type = st.selectbox(
        "Select Analysis",
        ["Hourly Trends", "Route Heatmap", "Route Stop Map", "Traffic Flow"]
    )

    # === HOURLY TRENDS ===
    if analysis_type == "Hourly Trends":
        filtered_df = render_simple_filters(observations_df, key_prefix="hourly")
        st.subheader("Hourly Average Duration per Route")

        traffic_map = {"Light": 1, "Moderate": 2, "Heavy": 3, "Jam": 4}
        filtered_df["traffic_index"] = filtered_df["traffic_condition"].map(traffic_map)

        if "observation_time" in filtered_df.columns:
            filtered_df["hour"] = (
                filtered_df["observation_time"]
                .astype(str)
                .str.extract(r"(\d+)")
                .astype(float)
                .fillna(0)
                .astype(int)
            )

        chart = (
            alt.Chart(filtered_df)
            .mark_area(opacity=0.6)
            .encode(
                x=alt.X("hour:O", sort='ascending', title="Hour of Day"),
                y=alt.Y("mean(traffic_index):Q", title="Avg Traffic Intensity (1–4)"),
                color="route_number:N",
                tooltip=["route_number", "hour", "mean(traffic_index)"]
            )
            .properties(height=400, title="Traffic Volume Trends by Hour")
        )

        st.altair_chart(chart, use_container_width=True)
        st.caption("Traffic intensity: 1=Light, 2=Moderate, 3=Heavy, 4=Jam")

    # === ROUTE HEATMAP ===
    elif analysis_type == "Route Heatmap":
        filtered_df = render_simple_filters(observations_df, key_prefix="heatmap")
        st.subheader("Route vs Time of Day (Traffic Condition Heatmap)")

        traffic_map = {"Light": 1, "Moderate": 2, "Heavy": 3, "Jam": 4}
        filtered_df["traffic_index"] = filtered_df["traffic_condition"].map(traffic_map)

        filtered_df["hour"] = (
            filtered_df["observation_time"]
            .astype(str)
            .str.extract(r"(\d+)")
            .astype(float)
            .fillna(0)
            .astype(int)
        )

        heat_df = (
            filtered_df.groupby(["route_number", "hour"])["traffic_index"]
            .mean()
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

    # === ROUTE STOP MAP ===
    elif analysis_type == "Route Stop Map":
        st.subheader("🗺️ Route Stop Map")

        # Fetch routes
        route_response = supabase.table("routes").select("route_number, route_name").execute()
        routes = pd.DataFrame(route_response.data)
        all_routes = sorted(routes["route_number"].unique())

        selected_routes = st.multiselect(
            "Select route(s) to view:",
            options=all_routes,
            default=all_routes[:2],
            help="Choose one or more routes to display stops on the map.",
            key="stopmap_routes"
        )

        if not selected_routes:
            st.warning("Please select at least one route to view the stop map.")
            return

        try:
            all_stops = []
            for route_number in selected_routes:
                route_info = routes[routes["route_number"] == route_number].iloc[0]
                route_data = supabase.table("routes").select("route_id").eq("route_number", route_number).execute()
                if not route_data.data:
                    continue
                route_id = route_data.data[0]["route_id"]

                stops_data = supabase.table("stops").select("*").eq("route_id", route_id).execute()
                stops = pd.DataFrame(stops_data.data)
                if stops.empty:
                    continue
                stops["route_number"] = route_number
                stops["route_name"] = route_info["route_name"]
                all_stops.append(stops)

            if not all_stops:
                st.info("📍 No GPS data available for selected routes.")
                return

            stops_df = pd.concat(all_stops, ignore_index=True)
            stops_df = stops_df[(stops_df["latitude"].notnull()) & (stops_df["longitude"].notnull())]

            map_type = st.radio("Map Style:", ["Simple", "Detailed with PyDeck"], horizontal=True)

            if map_type == "Simple":
                st.map(stops_df.rename(columns={"latitude": "lat", "longitude": "lon"}), zoom=11)
            else:
                view_state = pdk.ViewState(
                    latitude=stops_df["latitude"].mean(),
                    longitude=stops_df["longitude"].mean(),
                    zoom=11,
                    pitch=45
                )

                stops_df["color"] = [[255, 0, 0]] * len(stops_df)
                layer = pdk.Layer(
                    "ScatterplotLayer",
                    stops_df,
                    get_position=["longitude", "latitude"],
                    get_color="color",
                    get_radius=100,
                    pickable=True
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
                    map_style="mapbox://styles/mapbox/light-v9"
                )

                st.pydeck_chart(deck)

            st.subheader("Stop Details")
            display_cols = ["route_number", "stop_order", "stop_name", "latitude", "longitude"]
            st.dataframe(stops_df[display_cols], use_container_width=True)

        except Exception as e:
            st.error(f"Error loading map data: {e}")
            import traceback
            st.code(traceback.format_exc())

    # === TRAFFIC FLOW ===
    elif analysis_type == "Traffic Flow":

        def preprocess(df):
            df = df.copy()
            df["route_id"] = df["route_id"].astype(int)
            df["observation_date"] = pd.to_datetime(df["observation_date"])
            df["hour"] = pd.to_datetime(df["observation_time"], errors="coerce").dt.hour.fillna(0).astype(int)
            traffic_map = {"Light": 1, "Moderate": 2, "Heavy": 3, "Jam": 4}
            df["traffic_index"] = df["traffic_condition"].map(traffic_map)
            df["day_of_week"] = df["observation_date"].dt.day_name()
            return df

        def get_traffic_label(score):
            if score < 1.5:
                return "🟢 Light"
            elif score < 2.5:
                return "🟡 Moderate"
            elif score < 3.5:
                return "🟠 Heavy"
            else:
                return "🔴 Jam"

        df = preprocess(observations_df)

        st.subheader("🌊 Traffic Flow Analysis")
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        df["day_of_week"] = pd.Categorical(df["day_of_week"], categories=day_order, ordered=True)

        day_traffic = df.groupby("day_of_week")["traffic_index"].mean().reset_index()
        fig = px.bar(
            day_traffic,
            x="day_of_week",
            y="traffic_index",
            title="Average Traffic Intensity by Day of Week",
            labels={"day_of_week": "Day", "traffic_index": "Avg Traffic Score"},
            color="traffic_index",
            color_continuous_scale="RdYlGn_r"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Route Traffic Comparison")
        route_stats = df.groupby("route_number").agg({"traffic_index": ["mean", "std", "count"]}).reset_index()
        route_stats.columns = ["Route", "Avg Traffic", "Std Dev", "Observations"]
        route_stats["Traffic Level"] = route_stats["Avg Traffic"].apply(get_traffic_label)
        st.dataframe(route_stats, use_container_width=True, hide_index=True)
