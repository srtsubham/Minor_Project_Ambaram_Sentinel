import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(page_title="AKASH STORM TRACKER", layout="wide")
st.title("🛰️ Cyclone Remal Live Tracking (May 2024)")


def get_data():
    try:
        conn = psycopg2.connect(
            dbname="weather_db",
            user="postgres",
            password="2118",  # pass
            host="127.0.0.1",
            port="5757",
        )
        query = "SELECT lat, lon, temperature FROM weatheralert"
        df = pd.read_sql(query, conn)
        conn.close()

        df = df[df["lat"] != 0]
        return df
    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame()


try:
    storm_df = get_data()

    if not storm_df.empty:
        col1, col2 = st.columns(2)
        col1.metric("Storm Points Detected", len(storm_df))
        col2.metric("Min Temp Found", f"{storm_df['temperature'].min():.2f} K")

        st.subheader("Interactive Storm Map")

        st.map(storm_df, latitude="lat", longitude="lon", color="#ff4b4b")

        st.subheader("Database Preview (Top 5 rows)")
        st.table(storm_df.head(5))

    else:
        st.warning(
            "The database table 'weatheralert' is empty. Please run scanner.py again."
        )

except Exception as e:
    st.error(f"App Error: {e}")
