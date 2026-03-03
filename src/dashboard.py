import datetime
import io
import os
import sqlite3
import time
import zipfile

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
import torch

st.set_page_config(page_title="Ambaram Sentinel", layout="wide", page_icon="🛰️")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(CURRENT_DIR, "weather.db")

event_order = [
    "cyclone",
    "heatwave",
    "coldwave",
    "sandstorm",
    "rainfall",
    "cloudburst",
    "monsoon",
]

meta = {
    "cyclone": ["🚨", "WIND (KM/H)", 1],
    "heatwave": ["🔥", "TEMP (°C)", 2.8],
    "coldwave": ["❄️", "TEMP (°C)", 2.8],
    "sandstorm": ["🌪️", "WIND (KM/H)", 1],
    "rainfall": ["🌧️", "RAIN (MM)", 1],
    "cloudburst": ["⚡", "RATE (MM/HR)", 0.8],
    "monsoon": ["⛈️", "RAIN (MM)", 1],
}


@st.cache_resource
def load_ai_model():
    model_dir = os.path.join(CURRENT_DIR, "models")
    if not os.path.exists(model_dir):
        return False, "Models Folder Missing"
    files = [f for f in os.listdir(model_dir) if f.endswith(".pth")]
    if files:
        model_full_path = os.path.join(model_dir, files[0])
        try:
            torch.load(model_full_path, map_location=torch.device("cpu"))
            return True, files[0]
        except:
            return False, "File Corrupted"
    return False, "No Model Found"


def get_data():
    try:
        con = sqlite3.connect(DB_FILE)
        df = pd.read_sql(
            "SELECT lat, lon, intensity, event_type FROM weather_data ORDER BY id ASC",
            con,
        )
        con.close()
        return df
    except:
        return pd.DataFrame()


def predict_with_intensity(df):
    if len(df) < 1:
        return []
    active_zones = df.tail(10).copy()
    res = []
    for i, row in active_zones.iterrows():
        curr = np.array([row["lat"], row["lon"]])
        curr_int = row["intensity"]
        move = np.array([0.2, -0.15])
        for _ in range(3):
            nxt = curr + move
            curr_int = curr_int * 0.95
            res.append([nxt[0], nxt[1], curr_int])
            curr = nxt
    return res


if "view" in st.query_params and st.query_params["view"] == "map":
    st.markdown(
        """
        <style>
            [data-testid="stAppViewContainer"] { background: #1a1a1a !important; }
            [data-testid="stHeader"] { display: none !important; }
            [data-testid="stSidebar"] { display: none !important; }
            .block-container { padding: 0 !important; max-width: 100% !important; margin: 0 !important; }
            footer { display: none !important; }
            .stApp { background: #1a1a1a !important; background-image: none !important; }
            iframe { border: none !important; }
        </style>
    """,
        unsafe_allow_html=True,
    )

    req_event = st.query_params.get("event", "cyclone").lower()
    df = get_data()

    if not df.empty:
        sub = df[df["event_type"] == req_event].copy()
        if not sub.empty:
            icon, unit, div = meta.get(req_event, ["⚠️", "VAL", 1])
            sub["real_val"] = sub["intensity"] / div

            lay = []
            if req_event == "cyclone":
                lay.append(
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=sub,
                        get_position="[lon, lat]",
                        get_color=[255, 0, 0, 200],
                        get_radius=25000,
                    )
                )
            else:
                rgb = {
                    "heatwave": [255, 140, 0],
                    "rainfall": [0, 255, 0],
                    "sandstorm": [255, 215, 0],
                    "monsoon": [255, 255, 255],
                    "coldwave": [169, 169, 169],
                }.get(req_event, [138, 43, 226])
                lay.append(
                    pdk.Layer(
                        "HeatmapLayer",
                        data=sub,
                        get_position="[lon, lat]",
                        get_weight="real_val",
                        radius_pixels=60,
                        intensity=2,
                        threshold=0.3,
                        color_range=[
                            [rgb[0], rgb[1], rgb[2], 20],
                            [rgb[0], rgb[1], rgb[2], 200],
                        ],
                    )
                )

            view = pdk.ViewState(latitude=22.0, longitude=79.0, zoom=3.8, pitch=30)
            st.pydeck_chart(
                pdk.Deck(
                    layers=lay,
                    initial_view_state=view,
                    map_style="mapbox://styles/mapbox/dark-v10",
                )
            )
    st.stop()

HTML_COMBINED = "<a href='https://en.wikipedia.org/wiki/INSAT-3D' target='_blank' class='billboard-link'><div class='billboard'><h3 style='margin-top:0; margin-bottom:10px; font-size: 1.5rem;'>🛰️ ABOUT SATELLITE DATA SOURCE</h3><p style='color:#ccc; line-height:1.5; margin-bottom:0;'>The <b>AMBARAM Sentinel</b> processes high-resolution meteorological data sourced directly from <b>MOSDAC</b>.</p></div></a><div style='height: 10px;'></div><a href='https://github.com/srtsubham' target='_blank' class='billboard-link'><div class='billboard'><h3 style='margin-top:0; margin-bottom:5px; font-size: 1.5rem;'>🚀 PROJECT TEAM DECK</h3><p style='color:#888; font-size:0.9em; margin-bottom:15px; margin-top:0; line-height:1.4;'><b>Minor Project II (NCS4653)</b> | Group: 203 (D) | B.Tech CS3K | 3rd Year</p></div></a>"

HTML_FOOTER = "<div class='footer'><p>Minor Project AMBARAM [Group: 203 (D)] © 2025-2026 &nbsp;|&nbsp; <a href='https://www.mosdac.gov.in/' target='_blank'>MOSDAC Data</a> &nbsp;|&nbsp; <a href='https://ambaram-sentinel-minor-project.netlify.app/' target='_blank'>Main Website</a></p></div>"

bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop"
st.markdown(
    f"<style>.stApp {{ background-image: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url('{bg_url}'); background-size: cover; background-attachment: fixed; }} .main-header {{ background: rgba(255, 255, 255, 0.05); border-radius: 16px; backdrop-filter: blur(9.4px); border: 1px solid rgba(255, 255, 255, 0.15); padding: 20px; text-align: center; margin-bottom: 25px; }} .main-header h1 {{ color: #ffffff; font-weight: 700; font-size: 3rem; text-shadow: 0 2px 10px rgba(0,0,0,0.5); }} .footer {{ position: fixed; left: 0; bottom: 0; width: 100%; background-color: rgba(0, 0, 0, 0.9); color: #888; text-align: center; padding: 8px; font-size: 12px; z-index: 9999; border-top: 1px solid #333; }} .footer a {{ color: #00acee; text-decoration: none; margin: 0 10px; }} .billboard {{ background: rgba(20, 20, 30, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 25px; backdrop-filter: blur(10px); cursor: pointer; }}</style><div class='main-header'><h1>🛰️ AMBARAM EVENT SENTINEL 🛰️</h1><h4>Advanced Satellite Weather Tracking & Forecasting System</h4></div>",
    unsafe_allow_html=True,
)

model_status, model_name = load_ai_model()

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1039/1039328.png", width=70)
    st.title("🎮 CONTROL PANEL")
    st.success("✅ Database: CONNECTED")
    if model_status:
        st.success(f"✅ AI Model: ACTIVE\n({model_name})")
    else:
        st.warning("⚠️ AI Model: SIMULATION")
    st.info(f"🕒 Time: {datetime.datetime.now().strftime('%H:%M UTC')}")
    st.markdown("---")

    df = get_data()
    if not df.empty:
        st.header("📍 SELECTION")
        types = df["event_type"].unique()
        d_types = [
            t.upper()
            for t in sorted(
                types, key=lambda x: event_order.index(x) if x in event_order else 99
            )
        ]
        sel_d = st.selectbox("SELECT EVENT TYPE", d_types)
        sel = sel_d.lower()
    else:
        sel = None
        st.error("❌ NO DATA")

if not df.empty and sel:
    sub = df[df["event_type"] == sel].copy()
    icon, unit, div = meta.get(sel, ["⚠️", "VAL", 1])
    unit_only = unit.split("(")[1].replace(")", "")
    sub["real_val"] = sub["intensity"] / div

    st.header(f"{icon} {sel.upper()} MONITORING CONSOLE")
    c1, c2, c3 = st.columns(3)
    c1.metric("EVENT STATUS", "ACTIVE", delta="LIVE FEED")
    c2.metric("ZONES DETECTED", len(sub))
    c3.metric(f"MAX {unit.split()[0]}", f"{sub['real_val'].max():.1f} {unit_only}")

    lay, fut_data = [], predict_with_intensity(sub)

    if sel == "cyclone":
        lay.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=sub,
                get_position="[lon, lat]",
                get_color=[255, 0, 0, 200],
                get_radius=25000,
                pickable=True,
            )
        )
        if fut_data:
            fdf = pd.DataFrame(fut_data, columns=["lat", "lon", "intensity"])
            lay.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    data=fdf,
                    get_position="[lon, lat]",
                    get_color=[0, 100, 255, 200],
                    get_radius=30000,
                )
            )
    else:
        pred_rgb = [0, 100, 255]
        rgb = {
            "heatwave": [255, 140, 0],
            "rainfall": [0, 255, 0],
            "sandstorm": [255, 215, 0],
            "monsoon": [255, 255, 255],
            "coldwave": [169, 169, 169],
        }.get(sel, [138, 43, 226])
        lay.append(
            pdk.Layer(
                "HeatmapLayer",
                data=sub,
                get_position="[lon, lat]",
                get_weight="real_val",
                radius_pixels=60,
                intensity=2,
                threshold=0.3,
                color_range=[
                    [rgb[0], rgb[1], rgb[2], 20],
                    [rgb[0], rgb[1], rgb[2], 100],
                    [rgb[0], rgb[1], rgb[2], 200],
                ],
            )
        )
        if fut_data:
            fdf = pd.DataFrame(fut_data, columns=["lat", "lon", "intensity"])
            fdf["real_val"] = fdf["intensity"] / div
            lay.append(
                pdk.Layer(
                    "HeatmapLayer",
                    data=fdf,
                    get_position="[lon, lat]",
                    get_weight="real_val",
                    radius_pixels=70,
                    intensity=1.5,
                    threshold=0.2,
                    color_range=[
                        [pred_rgb[0], pred_rgb[1], pred_rgb[2], 20],
                        [pred_rgb[0], pred_rgb[1], pred_rgb[2], 100],
                        [pred_rgb[0], pred_rgb[1], pred_rgb[2], 255],
                    ],
                )
            )

    view = pdk.ViewState(latitude=22.0, longitude=79.0, zoom=4, pitch=40)
    st.pydeck_chart(
        pdk.Deck(
            layers=lay,
            initial_view_state=view,
            tooltip={"text": "{event_type}\nVal: {real_val:.1f}"},
        )
    )

    st.subheader(f"📊 LIVE REGIONAL DATA ({unit})")
    d_show = sub[["lat", "lon", "real_val"]].tail(10).copy()
    d_show.columns = ["LAT", "LON", unit]
    d_show.index = d_show.index + 1
    st.dataframe(d_show, width=1200)

    st.markdown("---")
    st.markdown(HTML_COMBINED, unsafe_allow_html=True)

st.markdown(HTML_FOOTER, unsafe_allow_html=True)
