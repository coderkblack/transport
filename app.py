import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime
import random
import mysql.connector

# Import your page functions
from dashboard import show_dashboard
from analysis import analysis_page
from view_routes import view_routes_page
from traffic import traffic_page

# st.image("/home/jakes/Documents/notebooks/practice/matatu/assets/banner.png", use_container_width=True, width=400)
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


st.set_page_config(
    page_title="Nairobi Routes",
    page_icon="🚌",
    layout="wide",
)

# ---------- NAVIGATION BAR ----------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Dashboard",  
    "View Routes", 
    "Analysis",
    "Traffic"
    ])

# ---------- PAGE ROUTING ----------
with tab1:
    show_dashboard()

with tab2:
    view_routes_page()

with tab3:
    analysis_page()

with tab4:
    traffic_page()
