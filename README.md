# 🛰️ AMBARAM SENTINEL

### AI WEATHER PREDICTION MODEL FOR EXTREME WEATHER EVENTS

**Minor Project II (NCS4653) | Group: 203 (D)**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Framework](https://img.shields.io/badge/Framework-Streamlit-red)
![AI Model](https://img.shields.io/badge/AI-PyTorch-orange)
![Data](<https://img.shields.io/badge/Data-MOSDAC%20(ISRO)-green>)

---

## 📖 About The Project

**Ambaram Sentinel** is a specialized meteorological dashboard designed to track, visualize, and predict extreme weather events using high-resolution satellite telemetry.

Sourced from **MOSDAC (ISRO)**, the system parses raw HDF5/HE5 satellite data from **INSAT-3D/3DR** to monitor Cyclones, Heatwaves, Coldwaves, and Monsoons.

---

## ⚡ Key Features

- **3D Geospatial Visualization:** Interactive globes via **PyDeck**.
- **AI Forecasting:** Custom **PyTorch** Neural Network for intensity shifts.
- **Local Database:** Runs on a zero-dependency **SQLite** backend.

---

## 📄 Project Documentation

- [Project Synopsis](docs/synopsis.pdf)
- [Concept Paper](docs/concept_paper.pdf)
- [Presentation Slides](docs/presentation.pptx)

---

## 🚀 Installation

1. **Clone & Environment:**
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    ```
