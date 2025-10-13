import random
import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib

# Database config
DB_CONFIG = {
    'host': 'localhost',
    'database': 'matatu-routes',
    'user': 'root',
    'password': ''
}

# Connection function
def create_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        st.error(f"Database connection error: {e}")
        return None
    
# Initialize db tables
def init_database():
    conn = create_connection()
    if conn:
        cursor = conn.cursor()

        # Routes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routes (
                route_id INT AUTO_INCREMENT PRIMARY KEY,
                route_number VARCHAR(20) NOT NULL UNIQUE,
                route_name VARCHAR(255) NOT NULL,
                start_point VARCHAR(255) NOT NULL,
                end_point VARCHAR(255) NOT NULL,
                distance_km FLOAT,
                estimated_duration INT,
                fare_range VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Stops table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stops (
                stop_id INT AUTO_INCREMENT PRIMARY KEY,
                route_id INT,
                stop_name VARCHAR(255) NOT NULL,
                stop_order INT NOT NULL,
                latitude DECIMAL(10, 8),
                longitude DECIMAL(11, 8),
                FOREIGN KEY (route_id) REFERENCES routes(route_id) ON DELETE CASCADE
            )
        """)

        # Matatus table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matatus (
                matatu_id INT AUTO_INCREMENT PRIMARY KEY,
                route_id INT,
                registration_number VARCHAR(20) UNIQUE NOT NULL,
                sacco_name VARCHAR(255),
                capacity INT,
                status VARCHAR(50) DEFAULT 'Active',
                FOREIGN KEY (route_id) REFERENCES routes(route_id) ON DELETE SET NULL
            )
        """)

        # Observations table (for data collection)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                observation_id INT AUTO_INCREMENT PRIMARY KEY,
                route_id INT,
                observation_date DATE NOT NULL,
                observation_time TIME NOT NULL,
                passenger_count INT,
                fare_paid DECIMAL(10, 2),
                traffic_condition VARCHAR(50),
                notes TEXT,
                FOREIGN KEY (route_id) REFERENCES routes(route_id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()
        return True
    return False

# CRUD Operations for Routes
def add_route(route_number, route_name, start_point, end_point, distance_km, estimated_duration, fare_range):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = """INSERT INTO routes 
                      (route_number, route_name, start_point, end_point, distance_km, estimated_duration, fare_range)
                      VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(query, (route_number, route_name, start_point, end_point, distance_km, estimated_duration, fare_range))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            st.error(f"Error adding route: {e}")
            conn.close()
            return False
    return False

def get_all_routes():
    conn = create_connection()
    if conn:
        query = "SELECT * FROM routes ORDER BY route_number"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    return pd.DataFrame()

def get_route_by_id(route_id):
    conn = create_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM routes WHERE route_id = %s", (route_id,))
        route = cursor.fetchone()
        cursor.close()
        conn.close()
        return route
    return None

# CRUD Operations for Stops
def add_stop(route_id, stop_name, stop_order, latitude=None, longitude=None):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = """INSERT INTO stops (route_id, stop_name, stop_order, latitude, longitude)
                      VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(query, (route_id, stop_name, stop_order, latitude, longitude))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            st.error(f"Error adding stop: {e}")
            return False
    return False

def get_stops_for_route(route_id):
    conn = create_connection()
    if conn:
        query = "SELECT * FROM stops WHERE route_id = %s ORDER BY stop_order"
        df = pd.read_sql(query, conn, params=(route_id,))
        conn.close()
        return df
    return pd.DataFrame()

# CRUD Operations for Observations
def add_observation(route_id, obs_date, obs_time, passenger_count, fare_paid, traffic_condition, notes):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = """INSERT INTO observations 
                      (route_id, observation_date, observation_time, passenger_count, fare_paid, traffic_condition, notes)
                      VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(query, (route_id, obs_date, obs_time, passenger_count, fare_paid, traffic_condition, notes))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            st.error(f"Error adding observation: {e}")
            return False
    return False

def get_all_observations():
    conn = create_connection()
    if conn:
        query = """SELECT o.*, r.route_number, r.route_name 
                  FROM observations o 
                  JOIN routes r ON o.route_id = r.route_id 
                  ORDER BY o.observation_date DESC, o.observation_time DESC"""
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    return pd.DataFrame()

# Streamlit App
def main():
    st.set_page_config(page_title="Matatu Routes Data Collection", layout="wide")
    
    # st.title("🚌 Matatu Routes Data Collection & Analysis")
    
    # Initialize database
    if 'db_initialized' not in st.session_state:
        if init_database():
            st.session_state.db_initialized = True
        else:
            st.error("Failed to initialize database. Check your MySQL connection.")
            return

if __name__ == "__main__":
    main()