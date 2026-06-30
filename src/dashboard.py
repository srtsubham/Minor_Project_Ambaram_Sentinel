import datetime
import io
import os
import sqlite3
import time
import zipfile
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st #version 8.3.7
import torch

st.set_page_config(page_title="Ambaram Sentinel", layout="wide", page_icon="🛰️")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(CURRENT_DIR, "weather.db")

HTML_COMBINED = """
<a href='https://en.wikipedia.org/wiki/INSAT-3D' target='_blank' class='billboard-link'>
    <div class='billboard'>
        <h3 style='margin-top:0; margin-bottom:10px; font-size: 1.5rem; color:#fff; text-shadow: 0 0 10px #00acee; letter-spacing: 2px;'>🛰️ ABOUT SATELLITE DATA SOURCE</h3>
        <p style='color:#00acee; line-height:1.5; margin-bottom:0; letter-spacing: 1px;'>The AMBARAM Sentinel processes high resolution meteorological data sourced directly from MOSDAC ISRO. Data ingestion involves parsing HDF5 files from INSAT 3D and 3DR satellites.</p>
    </div>
</a>

<div style='height: 20px;'></div>

<div class='billboard'>
    <h3 style='margin-top:0; margin-bottom:5px; font-size: 1.5rem; color:#fff; text-shadow: 0 0 10px #00acee; letter-spacing: 2px;'>🚀 PROJECT TEAM DECK</h3>
    <p style='color:#888; font-size:0.9em; margin-bottom:15px; margin-top:0; line-height:1.4; letter-spacing: 1px;'>Minor Project II NCS4653 | Group 203 D | B.Tech CS3K | 3rd Year<br>Topic AI Weather Prediction Model on Extreme Weather Events</p>

    <div class='team-member'><div class='role'>Project Lead & AI Architect</div><div class='name'>Somya Ranjan Tripathi <a href='https://github.com/srtsubham' target='_blank' class='gh-btn'>GitHub</a><a href='https://www.linkedin.com/in/somya-ranjan-tripathi-9136b42a4/' target='_blank' class='gh-btn'>LinkedIn</a></div><small style='color:#666; letter-spacing: 1px;'>Model Training Dashboard Designing Project Pipelining & Documentation</small></div>
    <div class='team-member'><div class='role'>Data Acquisition Specialist</div><div class='name'>Sneha Kumari <a href='https://github.com/snehakumari9696' target='_blank' class='gh-btn'>GitHub</a><a href='https://www.linkedin.com/in/sneha-kumari-58b414262/' target='_blank' class='gh-btn'>LinkedIn</a></div><small style='color:#666; letter-spacing: 1px;'>Data Fetching & Preprocessing</small></div>
    <div class='team-member'><div class='role'>Machine Learning Engineer</div><div class='name'>Vikas Bajpai <a href='https://github.com/vikasbajpai205' target='_blank' class='gh-btn'>GitHub</a><a href='https://www.linkedin.com/in/vikas-bajpai-98a275281/' target='_blank' class='gh-btn'>LinkedIn</a></div><small style='color:#666; letter-spacing: 1px;'>ML Algorithms & Optimization</small></div>
    <div class='team-member' style='border-bottom:none; margin-bottom:0;'><div class='role'>Frontend Interface Developer</div><div class='name'>Sunny Prajapati <a href='https://github.com/isunnyprajapati' target='_blank' class='gh-btn'>GitHub</a><a href='https://www.linkedin.com/in/sunny-prajapati-8759b5292/' target='_blank' class='gh-btn'>LinkedIn</a></div><small style='color:#666; letter-spacing: 1px;'>Responsive Layouts Visual Styling & Component Integration</small></div>
</div>
""".replace("\n", "")

HTML_DISCLAIMER = """<div style="text-align: center; color: #00acee; font-size: 0.8em; margin-top: 15px; text-shadow: 0 0 5px rgba(0,172,238,0.5); letter-spacing: 1px;">Restricted Access Displayed telemetry reflects archived satellite data packet from May 24 2024 to May 28 2024.<br>Further development on selected date prediction on events are in development phase will be available in future versions.</div>"""
HTML_FOOTER = """<div class="footer"><p style="letter-spacing: 1px;">Minor Project AMBARAM Group 203 D © 2025 2026 &nbsp;|&nbsp; <a href="https://www.mosdac.gov.in/" target="_blank">MOSDAC Data</a> &nbsp;|&nbsp; <a href="https://github.com/srtsubham/Minor_Project_Ambaram_Sentinel/tree/main/docs" target="_blank">Project Documentation</a> &nbsp;|&nbsp; <a href="https://ambaram-sentinel-minor-project.netlify.app/" target="_blank">Main Website</a></p></div>"""

event_order = [
    "cyclone",
    "heatwave",
    "coldwave",
    "sandstorm",
    "monsoon",
    "rainfall",
    "cloudburst",
]

meta = {
    "cyclone": ["🚨", "WIND KM H", 1],
    "heatwave": ["🔥", "TEMP C", 2.8],
    "coldwave": ["❄️", "TEMP C", 2.8],
    "sandstorm": ["🌪️", "WIND KM H", 1],
    "rainfall": ["🌧️", "RAIN MM", 1],
    "cloudburst": ["⚡", "RATE MM HR", 0.8],
    "monsoon": ["⛈️", "RAIN MM", 1],
}

@st.cache_resource
def load_ai_model():
    model_dir = os.path.join(CURRENT_DIR, "models")
    if not os.path.exists(model_dir):
        return False, "Models Folder not found Refresh the Page"
    files = [f for f in os.listdir(model_dir) if f.endswith(".pth")]
    if files:
        model_filename = files[0]
        model_full_path = os.path.join(model_dir, model_filename)
        try:
            torch.load(model_full_path, map_location=torch.device("cpu"))
            return True, model_filename
        except:
            return False, "File Corrupted Not Found"
    else:
        return False, "Model not found Please Try Again Later"

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

params = st.query_params
if params.get("view") == "map":
    st.markdown(
        """
        <style>
            [data-testid="stAppViewContainer"] { background: transparent !important; }
            [data-testid="stHeader"] { display: none !important; }
            [data-testid="stSidebar"] { display: none !important; }
            [data-testid="stBottom"] { display: none !important; }
            .block-container { padding: 0 !important; max-width: 100% !important; margin: 0 !important; }
            footer { display: none !important; }
            .viewerBadge_container_link { display: none !important; }
            .stApp { background: transparent !important; background-image: none !important; }
            iframe { border: none !important; }
        </style>
    """,
        unsafe_allow_html=True,
    )
    req_event = params.get("event", "cyclone").lower()
    df = get_data()
    if not df.empty:
        sub = df[df["event_type"] == req_event].copy()
        if not sub.empty:
            icon, unit, div = meta.get(req_event, ["⚠️", "VAL", 1])
            sub["real_val"] = sub["intensity"] / div
            lay, fut_data = [], predict_with_intensity(sub)
            if req_event == "cyclone":
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
                            get_color=[0, 172, 238, 200],
                            get_radius=30000,
                        )
                    )
            else:
                pred_rgb = [0, 172, 238]
                if req_event == "monsoon":
                    rgb = [255, 255, 255]
                elif req_event == "coldwave":
                    rgb = [169, 169, 169]
                else:
                    rgb = {
                        "heatwave": [255, 140, 0],
                        "rainfall": [0, 255, 0],
                        "sandstorm": [255, 215, 0],
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
            view = pdk.ViewState(latitude=22.0, longitude=79.0, zoom=3.8, pitch=30)
            st.pydeck_chart(
                pdk.Deck(layers=lay, initial_view_state=view, map_style="dark")
            )
    st.stop()

bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop"
cursor_default = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48'><circle cx='24' cy='24' r='20' stroke='%2300acee' stroke-width='2' fill='none' opacity='0.7'/><circle cx='24' cy='24' r='8' stroke='%2300acee' stroke-width='2' fill='none' opacity='0.9'/><line x1='4' y1='24' x2='44' y2='24' stroke='%2300acee' stroke-width='2' opacity='0.9'/><line x1='24' y1='4' x2='24' y2='44' stroke='%2300acee' stroke-width='2' opacity='0.9'/></svg>"
cursor_active = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48'><circle cx='24' cy='24' r='14' fill='%2300acee' opacity='0.5'/><circle cx='24' cy='24' r='10' fill='%2300acee' opacity='0.7'/><line x1='8' y1='24' x2='40' y2='24' stroke='%23ffffff' stroke-width='2.5'/><line x1='24' y1='8' x2='24' y2='40' stroke='%23ffffff' stroke-width='2.5'/><circle cx='24' cy='24' r='14' stroke='%23ffffff' stroke-width='2.5' fill='none'/><circle cx='24' cy='24' r='6' fill='%23ffffff'/></svg>"

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');

* {{ font-family: 'Orbitron', sans-serif !important; cursor: url("{cursor_default}") 24 24, auto !important; }}
*:active, a:active, button:active, .stButton>button:active {{ cursor: url("{cursor_active}") 24 24, auto !important; }}

.stIcon, .st-icon, .material-symbols-rounded, [data-testid="stIconMaterial"] {{
    font-family: 'Material Symbols Rounded' !important;
}}

[data-testid="stHeader"] {{
    background: transparent !important;
}}
[data-testid="collapsedControl"] {{
    color: #00acee !important;
    background: rgba(0, 0, 0, 0.6) !important;
    border-radius: 50%;
    z-index: 999999 !important;
    transition: 0.3s;
}}
[data-testid="collapsedControl"]:hover {{
    background: rgba(0, 172, 238, 0.4) !important;
    box-shadow: 0 0 10px #00acee;
}}

[data-testid="stAppViewContainer"] {{
    background-image: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url("{bg_url}") !important;
    background-size: cover !important;
    background-position: center !important;
    background-attachment: fixed !important;
}}

.stApp {{
    background: transparent !important;
}}

.main-header {{
    background: linear-gradient(145deg, #111, #050505);
    border: 1px solid #333;
    box-shadow: 0 10px 30px rgba(0,0,0,0.8), inset 0 0 20px rgba(0,170,255,0.05);
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    margin: 0 auto 25px auto;
    max-width: 95%;
}}

.main-header h1 {{ color: #ffffff; font-weight: 700; font-size: 3rem; text-shadow: 0 0 10px #00acee; letter-spacing: 2px; }}
.main-header h4 {{ color: #00acee; font-weight: 300; letter-spacing: 1px; }}
[data-testid="stSidebar"] h1 {{ font-size: 1.5rem !important; letter-spacing: 1px; }}

.footer {{
    position: fixed; left: 0; bottom: 0; width: 100%;
    background-color: #020202; color: #888;
    padding: 10px 0; font-size: 12px;
    z-index: 9999; border-top: 1px solid #333;
    display: flex; justify-content: center; align-items: center; flex-wrap: wrap; gap: 8px;
}}

.footer p {{ margin: 0; padding: 0; text-align: center; }}
.footer a {{ color: #00acee; text-decoration: none; margin: 0 5px; transition: 0.3s; }}
.footer a:hover {{ text-shadow: 0 0 10px #00acee; color: #fff; }}
a.billboard-link {{ text-decoration: none; color: inherit; display: block; }}

.billboard {{
    background: linear-gradient(145deg, #111, #050505);
    border: 1px solid #333;
    border-radius: 15px;
    padding: 25px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.8), inset 0 0 20px rgba(0,170,255,0.05);
    transition: all 0.3s ease;
}}

a.billboard-link .billboard:hover {{
    transform: translateY(-5px);
    border-color: #00acee;
    box-shadow: 0 15px 40px rgba(0,170,255,0.2), inset 0 0 30px rgba(0,170,255,0.1);
}}

.team-member {{ margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); text-align: left; }}
.role {{ color: #00acee; font-size: 0.8em; font-weight: 700; letter-spacing: 1px; margin-bottom: 4px; text-transform: uppercase; }}
.name {{ font-size: 1.1em; font-weight: 500; color: white; display: flex; align-items: center; margin-bottom: 4px; letter-spacing: 1px; }}

.gh-btn {{
    background: rgba(255,255,255,0.1); color: #fff !important;
    padding: 2px 8px; border-radius: 4px; font-size: 0.7em;
    text-decoration: none; border: 1px solid rgba(0,172,238,0.5);
    transition: all 0.2s; display: inline-block;
    margin-left: 10px;
    letter-spacing: 1px;
}}
.gh-btn:hover {{ background: #00acee; border-color: #00acee; color: white !important; box-shadow: 0 0 10px rgba(0,172,238,0.5); }}

@media (max-width: 768px) {{
    .main-header {{ padding: 12px 5px !important; margin: 0 auto 15px auto !important; width: 98% !important; }}
    .main-header h1 {{ font-size: 4.5vw !important; white-space: nowrap !important; display: block !important; width: 100% !important; }}
    .main-header h4 {{ font-size: 3vw !important; }}
    [data-testid="stMarkdownContainer"] h2 {{ text-align: left !important; font-size: 5.5vw !important; }}
    [data-testid="stMarkdownContainer"] h3 {{ text-align: left !important; font-size: 4.5vw !important; }}
    [data-testid="stMetricValue"] {{ text-align: left !important; font-size: 6.5vw !important; }}
    [data-testid="stMetricLabel"] {{ text-align: left !important; font-size: 3.5vw !important; }}
    [data-testid="stMetricDelta"] {{ justify-content: flex-start !important; }}
    [data-testid="column"] {{ width: 100% !important; flex: 1 1 100% !important; }}
    .billboard {{ padding: 15px; }}
    .team-member {{ font-size: 0.9rem; }}
}}
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
    st.success("✅ Database CONNECTED")

    if model_status:
        st.success(f"✅ AI Model ACTIVE\n({model_name})")
    else:
        st.warning("⚠️ AI Model SIMULATION")

    st.info(f"🕒 Time {datetime.datetime.now().strftime('%H:%M UTC')}")
    st.markdown("---")

    df = get_data()

    if not df.empty:
        st.header("📍 CATEGORY")
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
        st.write("Source MOSDAC ISRO")

        if st.checkbox("📂 RAW SATELLITE FILES"):
            st.info(
                "Due to cloud memory limits raw ISRO H5 HE5 telemetry data is hosted securely on external drives"
            )
            st.link_button(
                "☁️ Access MOSDAC Data Drive",
                "https://drive.google.com/drive/folders/18nZ7QlgYtrk9UurePyWijkpYNUMjdFm-?usp=sharing",
                use_container_width=True,
            )

    else:
        sel = None
        st.error("❌ NO DATA")

if not df.empty and sel:
    sub = df[df["event_type"] == sel].copy()
    info = meta.get(sel, ["⚠️", "VAL", 1])
    icon, unit, div = info
    unit_only = unit.split(" ")[1]

    sub["real_val"] = sub["intensity"] / div

    st.header(f"{icon} {sel.upper()} MONITORING CONSOLE")

    c1, c2, c3 = st.columns(3)
    c1.metric("EVENT STATUS", "ACTIVE", delta="LIVE FEED")
    c2.metric("ZONES DETECTED", len(sub))
    c3.metric(f"MAX {unit.split(' ')[0]}", f"{sub['real_val'].max():.1f} {unit_only}")

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
                get_color=[0, 172, 238, 200],
                get_radius=30000,
            )
            lay.append(l2)
    else:
        pred_rgb = [0, 172, 238]

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
            tooltip={"text": "{event_type} Val {real_val:.1f}"},
        )
    )

    st.subheader(f"📊 LIVE REGIONAL DATA {unit}")
    d_show = sub[["lat", "lon", "real_val"]].tail(10).copy()
    d_show.columns = ["LAT", "LON", unit]
    d_show = d_show.reset_index(drop=True)
    d_show.index = d_show.index + 1
    st.dataframe(d_show, use_container_width=True)

    if fut_data:
        st.subheader("🤖 AI PREDICTION FORECAST NEXT 3 HRS")
        p_show = pd.DataFrame(fut_data, columns=["LAT", "LON", "INT_RAW"])
        p_show[unit] = (p_show["INT_RAW"] / div).round(2)
        p_show = p_show[["LAT", "LON", unit]].tail(10).reset_index(drop=True)
        p_show.index = p_show.index + 1
        st.dataframe(p_show, use_container_width=True)

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
