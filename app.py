import streamlit as st
from streamlit_option_menu import option_menu
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

st.set_page_config(
    page_title="Nairobi Routes",
    page_icon="🚌",
    layout="wide",
)

# ---------- NAVIGATION BAR ----------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Dashboard", 
    "Add Route", 
    "Add Stops", 
    "Data Collection", 
    "View Routes", 
    "Analysis",
    "Traffic"
    ])

# ---------- PAGE ROUTING ----------
with tab1:
    show_dashboard()

with tab2:
    add_route_page()

with tab3:
    add_stops_page()

with tab4:
    data_collection_page()

with tab5:
    view_routes_page()

with tab6:
    analysis_page()

with tab7:
    traffic_page()
