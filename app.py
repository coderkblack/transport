import streamlit as st
from datetime import datetime
import random
import mysql.connector

# Import your page functions
from dashboard import show_dashboard
from add_route import add_route_page
from add_stop import add_stops_page
from analysis import analysis_page
from data_collection import data_collection_page
from view_routes import view_routes_page
from traffic import traffic_page

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Nairobi Routes",
    page_icon="🚌",
    layout="wide",
)

# ---------- CUSTOM BANNER ----------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700&display=swap');

        .banner {
            position: relative;
            width: 100%;
            height: 120px;
            background: linear-gradient(90deg, #0A192F 0%, #00B4D8 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #F8F9FA;
            font-family: 'Montserrat', sans-serif;
            font-size: 38px;
            font-weight: 700;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.4);
            letter-spacing: 1px;
            border-radius: 0 0 16px 16px;
            margin-bottom: 30px;
        }
    </style>

    <div class="banner">🚐 Traffic Dashboard</div>
""", unsafe_allow_html=True)

# ---------- TAB NAVIGATION ----------
tabs = [
    "Dashboard", 
    "Add Route", 
    "Add Stops", 
    "Data Collection", 
    "View Routes", 
    "Analysis",
    "Traffic"
]

# Initialize session state for active tab
if "active_tab" not in st.session_state:
    st.session_state.active_tab = tabs[0]

# Create tabs
tab_objects = st.tabs(tabs)

# Check which tab is selected and rerun if it changes
for i, tab in enumerate(tab_objects):
    with tab:
        if st.session_state.active_tab != tabs[i]:
            st.session_state.active_tab = tabs[i]
            st.experimental_rerun()  # ✅ refresh on tab switch

        # ---------- PAGE ROUTING ----------
        if tabs[i] == "Dashboard":
            show_dashboard()
        elif tabs[i] == "Add Route":
            add_route_page()
        elif tabs[i] == "Add Stops":
            add_stops_page()
        elif tabs[i] == "Data Collection":
            data_collection_page()
        elif tabs[i] == "View Routes":
            view_routes_page()
        elif tabs[i] == "Analysis":
            analysis_page()
        elif tabs[i] == "Traffic":
            traffic_page()
