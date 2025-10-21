import streamlit as st
from datetime import datetime

# Import your page functions
from add_route import add_route_page
from add_stop import add_stops_page
from data_collection import data_collection_page

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

    <div class="banner">🚐 Data Entry</div>
""", unsafe_allow_html=True)


st.set_page_config(
    page_title="Nairobi Routes",
    page_icon="🚌",
    layout="wide",
)


# ---------- NAVIGATION BAR ----------
tab1, tab2, tab3 = st.tabs([
    "Data Collection",
    "Add Stops",
    "Add Route", 
    ])

# ---------- PAGE ROUTING ----------
with tab1:
    data_collection_page()

with tab2:
    add_stops_page()

with tab3:
    add_route_page()
