import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
from zoneinfo import ZoneInfo

# ✅ Initialize Supabase client
url: str = st.secrets["supabase"]["url"]
key: str = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

# --- ROUTES CRUD ---

def add_route(route_number, route_name, start_point, end_point, distance_km, estimated_duration, fare_range):
    try:
        data = {
            "route_number": route_number,
            "route_name": route_name,
            "start_point": start_point,
            "end_point": end_point,
            "distance_km": distance_km,
            "estimated_duration": estimated_duration,
            "fare_range": fare_range,
            "created_at": datetime.now().isoformat()
        }
        supabase.table("routes").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error adding route: {e}")
        return False


def get_all_routes():
    try:
        response = supabase.table("routes").select("*").order("route_number", desc=False).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching routes: {e}")
        return pd.DataFrame()


def get_route_by_id(route_id):
    try:
        response = supabase.table("routes").select("*").eq("route_id", route_id).single().execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching route: {e}")
        return None


# --- STOPS CRUD ---

def add_stop(route_id, stop_name, stop_order, latitude=None, longitude=None):
    try:
        data = {
            "route_id": route_id,
            "stop_name": stop_name,
            "stop_order": stop_order,
            "latitude": latitude,
            "longitude": longitude
        }
        supabase.table("stops").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error adding stop: {e}")
        return False


def get_stops_for_route(route_id):
    try:
        response = supabase.table("stops").select("*").eq("route_id", route_id).order("stop_order").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching stops: {e}")
        return pd.DataFrame()


# --- OBSERVATIONS CRUD ---

def add_observation(route_id, obs_date, obs_time, passenger_count, fare_paid, traffic_condition, notes):
    try:
        # COmbine date and time into a timezone-aware datetime
        nairobi_tz = ZoneInfo("Africa/Nairobi")
        local_dt = datetime.combine(obs_date, obs_time, tzinfo=nairobi_tz)

        # Convert to UTC for storage
        utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

        data = {
            "route_id": route_id,
            "observation_date": str(obs_date),
            "observation_time": utc_dt.isoformat(),
            "passenger_count": passenger_count,
            "fare_paid": fare_paid,
            "traffic_condition": traffic_condition,
            "notes": notes
        }
        supabase.table("observations").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error adding observation: {e}")
        return False


def get_all_observations():
    try:
        response = (
            supabase.table("observations")
            .select("*, routes(route_number, route_name)")
            .order("observation_date", desc=True)
            .order("observation_time", desc=True)
            .execute()
        )
        data = []
        for row in response.data:
            row["route_number"] = row["routes"]["route_number"] if "routes" in row else None
            row["route_name"] = row["routes"]["route_name"] if "routes" in row else None
            data.append(row)
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error fetching observations: {e}")
        return pd.DataFrame()


# --- STREAMLIT ENTRY POINT (TEST UI) ---

def main():
    st.set_page_config(page_title="Matatu Routes Data (Supabase API)", layout="wide")
    st.title("🚌 Matatu Routes — Supabase API Connection")

    df_routes = get_all_routes()
    if df_routes.empty:
        st.warning("No routes found in Supabase.")
    else:
        st.dataframe(df_routes)


if __name__ == "__main__":
    main()
