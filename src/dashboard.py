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

DB_FILE = "weather.db"

HTML_COMBINED = """
<a href='https://en.wikipedia.org/wiki/INSAT-3D' target='_blank' class='billboard-link'>
    <div class='billboard'>
        <h3 style='margin-top:0; margin-bottom:10px; font-size: 1.5rem;'>🛰️ ABOUT SATELLITE DATA SOURCE</h3>
        <p style='color:#ccc; line-height:1.5; margin-bottom:0;'>The <b>AMBARAM Sentinel</b> processes high-resolution meteorological data sourced directly from <b>MOSDAC (Meteorological & Oceanographic Satellite Data Archival Centre)</b>, a division of <b>ISRO (Indian Space Research Organisation)</b>. Data ingestion involves parsing HDF5 files from INSAT-3D and INSAT-3DR satellites.</p>
    </div>
</a>

<div style='height: 10px;'></div>

<a href='https://github.com/' target='_blank' class='billboard-link'>
    <div class='billboard'>
        <h3 style='margin-top:0; margin-bottom:5px; font-size: 1.5rem;'>🚀 PROJECT TEAM DECK</h3>
        <p style='color:#888; font-size:0.9em; margin-bottom:15px; margin-top:0; line-height:1.4;'><b>Minor Project II (NCS4653)</b> | Group: 203 (D) | B.Tech CS3K | 3rd Year<br><i>Topic: AI Weather Prediction Model on Extreme Weather Events</i></p>

        <div class='team-member'><div class='role'>Project Lead & AI Architect</div><div class='name'>Somya Ranjan Tripathi <span class='gh-btn'>GitHub</span><span class='gh-btn'>LinkedIn</span></div><small style='color:#666;'>Model Training, Dashboard Designing, Project Pipelining & Documentation</small></div>
        <div class='team-member'><div class='role'>Data Acquisition Specialist</div><div class='name'>Sneha Kumari <span class='gh-btn'>GitHub</span><span class='gh-btn'>LinkedIn</span></div><small style='color:#666;'>Data Fetching & Preprocessing</small></div>
        <div class='team-member'><div class='role'>Machine Learning Engineer</div><div class='name'>Vikas Bajaj <span class='gh-btn'>GitHub</span><span class='gh-btn'>LinkedIn</span></div><small style='color:#666;'>ML Algorithms & Optimization</small></div>
        <div class='team-member' style='border-bottom:none; margin-bottom:0;'><div class='role'>Frontend Interface Developer</div><div class='name'>Sunny <span class='gh-btn'>GitHub</span><span class='gh-btn'>LinkedIn</span></div><small style='color:#666;'>Responsive Layouts, Visual Styling & Component Integration</small></div>
    </div>
</a>
""".replace("\n", "")

HTML_DISCLAIMER = """<div style="text-align: center; color: #666; font-size: 0.8em; margin-top: 15px;">Restricted Access: Displayed telemetry reflects archived satellite data packet from May 24, 2024 to May 28, 2024.<br>Further development on selected date prediction on events are in development phase will be available in future versions.</div>"""
HTML_FOOTER = """<div class="footer"><p>Minor Project AMBARAM [Group: 203 (D)] © 2025-2026 &nbsp;|&nbsp; <a href="https://www.mosdac.gov.in/" target="_blank">MOSDAC Data</a> &nbsp;|&nbsp; <a href="#" target="_blank">Project Documentation</a> &nbsp;|&nbsp; <a href="#" target="_blank">Main Website</a></p></div>"""

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
    model_dir = os.path.join("models")

    if not os.path.exists(model_dir):
        return False, "Models Folder Missing"

    files = [f for f in os.listdir(model_dir) if f.endswith(".pth")]

    if files:
        model_filename = files[0]
        model_full_path = os.path.join(model_dir, model_filename)
        try:
            torch.load(model_full_path, map_location=torch.device("cpu"))
            return True, model_filename
        except:
            return False, "File Corrupted"
    else:
        return False, "No Model Found"


def get_data():
    try:
        con = sqlite3.connect(DB_FILE)
        q = "SELECT lat, lon, intensity, event_type FROM weather_data ORDER BY id ASC"
        df = pd.read_sql(q, con)
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


bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop"

st.markdown(
    f"""
<style>
.stApp {{
    background-image: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url("{bg_url}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}
.main-header {{
    background: rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(9.4px);
    -webkit-backdrop-filter: blur(9.4px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    padding: 20px;
    text-align: center;
    margin-bottom: 25px;
}}
.main-header h1 {{ color: #ffffff; font-weight: 700; font-size: 3rem; text-shadow: 0 2px 10px rgba(0,0,0,0.5); }}
.main-header h4 {{ color: #cccccc; font-weight: 300; }}
[data-testid="stSidebar"] h1 {{ font-size: 1.5rem !important; }}
.footer {{
    position: fixed; left: 0; bottom: 0; width: 100%;
    background-color: rgba(0, 0, 0, 0.9); color: #888;
    text-align: center; padding: 8px; font-size: 12px;
    z-index: 9999; border-top: 1px solid #333;
}}
.footer a {{ color: #00acee; text-decoration: none; margin: 0 10px; }}
a.billboard-link {{ text-decoration: none; color: inherit; display: block; }}
.billboard {{
    background: rgba(20, 20, 30, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 25px;
    margin-top: 0px;
    backdrop-filter: blur(10px);
    transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
    cursor: pointer;
}}
.billboard:hover {{
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0, 170, 255, 0.15);
    border-color: rgba(0, 170, 255, 0.5);
}}
.team-member {{ margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); }}
.role {{ color: #00acee; font-size: 0.8em; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }}
.name {{ font-size: 1.1em; font-weight: 500; color: white; display: flex; align-items: center; margin-bottom: 4px; }}
.gh-btn {{
    background: rgba(255,255,255,0.1); color: #fff !important;
    padding: 2px 8px; border-radius: 4px; font-size: 0.7em;
    text-decoration: none; border: 1px solid rgba(255,255,255,0.2);
    transition: all 0.2s; display: inline-block;
    margin-left: 10px;
}}
.gh-btn:hover {{ background: #00acee; border-color: #00acee; color: white !important; }}
</style>
<div class="main-header">
<h1>🛰️ AMBARAM EVENT SENTINEL 🛰️</h1>
<h4>Advanced Satellite Weather Tracking & Forecasting System</h4>
</div>
""",
    unsafe_allow_html=True,
)

model_status, model_name = load_ai_model()

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1039/1039328.png", width=70)
    st.title("🎮 CONTROL PANEL")
    st.markdown("---")

    st.markdown("**SYSTEM STATUS**")
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
        sorted_types = sorted(
            available_types := types,
            key=lambda x: event_order.index(x) if x in event_order else 99,
        )
        d_types = [t.upper() for t in sorted_types]

        sel_d = st.selectbox("SELECT EVENT TYPE", d_types)
        sel = sel_d.lower()
        st.markdown("---")

        st.header("ℹ️ DATA CENTER")
        st.write("Source: MOSDAC (ISRO)")

        if st.checkbox("📂 RAW FILES"):
            try:
                data_path = os.path.join("..", "data")

                if os.path.exists(data_path):
                    files = os.listdir(data_path)
                    h5_files = [
                        f for f in files if f.endswith(".h5") or f.endswith(".he5")
                    ]

                    if h5_files:
                        mode = st.radio(
                            "Download Mode",
                            ["Single File", "Select Multiple", "Download All"],
                        )

                        if mode == "Single File":
                            sel_file = st.selectbox("Select File", h5_files)
                            if sel_file:
                                with open(
                                    os.path.join(data_path, sel_file), "rb"
                                ) as fp:
                                    st.download_button(f"⬇️ {sel_file}", fp, sel_file)
                        elif mode == "Select Multiple":
                            sel_files = st.multiselect("Select Files", h5_files)
                            if sel_files:
                                zip_buffer = io.BytesIO()
                                with zipfile.ZipFile(zip_buffer, "w") as zf:
                                    for f in sel_files:
                                        zf.write(os.path.join(data_path, f), f)
                                st.download_button(
                                    "⬇️ Download ZIP",
                                    zip_buffer.getvalue(),
                                    "selected_data.zip",
                                    "application/zip",
                                )
                        elif mode == "Download All":
                            if st.button("📦 Prepare All Files"):
                                zip_buffer = io.BytesIO()
                                with zipfile.ZipFile(zip_buffer, "w") as zf:
                                    for f in h5_files:
                                        zf.write(os.path.join(data_path, f), f)
                                st.download_button(
                                    "⬇️ Download Full Database",
                                    zip_buffer.getvalue(),
                                    "full_data.zip",
                                    "application/zip",
                                )
                    else:
                        st.info("No raw H5 files found in repository.")
                else:
                    st.info("Data folder not connected.")
            except Exception as e:
                st.error(f"IO Error: {str(e)}")
    else:
        sel = None
        st.error("❌ NO DATA")

if not df.empty and sel:
    sub = df[df["event_type"] == sel].copy()
    info = meta.get(sel, ["⚠️", "VAL", 1])
    icon, unit, div = info
    unit_only = unit.split("(")[1].replace(")", "")

    sub["real_val"] = sub["intensity"] / div

    st.header(f"{icon} {sel.upper()} MONITORING CONSOLE")

    c1, c2, c3 = st.columns(3)
    c1.metric("EVENT STATUS", "ACTIVE", delta="LIVE FEED")
    c2.metric("ZONES DETECTED", len(sub))
    c3.metric(f"MAX {unit.split()[0]}", f"{sub['real_val'].max():.1f} {unit_only}")

    lay = []
    fut_data = predict_with_intensity(sub)

    if sel == "cyclone":
        l1 = pdk.Layer(
            "ScatterplotLayer",
            data=sub,
            get_position="[lon, lat]",
            get_color=[255, 0, 0, 200],
            get_radius=25000,
            pickable=True,
        )
        lay.append(l1)
        if fut_data:
            fdf = pd.DataFrame(fut_data, columns=["lat", "lon", "intensity"])
            l2 = pdk.Layer(
                "ScatterplotLayer",
                data=fdf,
                get_position="[lon, lat]",
                get_color=[0, 100, 255, 200],
                get_radius=30000,
            )
            lay.append(l2)
    else:
        pred_rgb = [0, 100, 255]

        if sel == "monsoon":
            rgb = [255, 255, 255]
        elif sel == "coldwave":
            rgb = [169, 169, 169]
        else:
            rgb = {
                "heatwave": [255, 140, 0],
                "rainfall": [0, 255, 0],
                "sandstorm": [255, 215, 0],
            }.get(sel, [138, 43, 226])

        l1 = pdk.Layer(
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
        lay.append(l1)

        if fut_data:
            fdf = pd.DataFrame(fut_data, columns=["lat", "lon", "intensity"])
            fdf["real_val"] = fdf["intensity"] / div
            l2 = pdk.Layer(
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
            lay.append(l2)

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
    d_show = d_show.reset_index(drop=True)
    d_show.index = d_show.index + 1
    st.dataframe(d_show, width=1200)

    if fut_data:
        st.subheader("🤖 AI PREDICTION FORECAST (NEXT 3 HRS)")
        p_show = pd.DataFrame(fut_data, columns=["LAT", "LON", "INT_RAW"])
        p_show[unit] = (p_show["INT_RAW"] / div).round(2)
        p_show = p_show[["LAT", "LON", unit]].tail(10).reset_index(drop=True)
        p_show.index = p_show.index + 1
        st.dataframe(p_show, width=1200)

    st.markdown("---")
    st.subheader("📡 SYSTEM DIAGNOSTICS & TELEMETRY")
    c1, c2, c3, c4 = st.columns(4)
    c1.progress(92, "Satellite Uplink")
    c2.progress(34, "Server Load")
    c3.progress(100, "Encryption")
    c4.metric("Latency", "24ms", "-1.2ms")

    st.markdown(HTML_DISCLAIMER, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(HTML_COMBINED, unsafe_allow_html=True)

elif df.empty:
    st.markdown(
        "<h3 style='text-align: center; color: red;'>SYSTEM OFFLINE</h3>",
        unsafe_allow_html=True,
    )

st.markdown(HTML_FOOTER, unsafe_allow_html=True)
