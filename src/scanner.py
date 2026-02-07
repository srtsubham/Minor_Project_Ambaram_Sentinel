import os
import random
import sqlite3

import h5py
import numpy as np

DATA_DIR = os.path.join("..", "data")
DB_FILE = "weather.db"

ev = [
    "cyclone",
    "cloudburst",
    "heatwave",
    "sandstorm",
    "rainfall",
    "monsoon",
    "coldwave",
]

seeds = {
    "heatwave": [(28.6, 77.2), (23.2, 77.4), (21.1, 79.0), (26.9, 75.8)],
    "cloudburst": [(31.1, 77.1), (30.3, 78.0), (34.0, 74.8)],
    "sandstorm": [(26.9, 70.9), (28.0, 73.3), (24.6, 72.7)],
    "rainfall": [(19.0, 72.8), (12.9, 77.5), (22.5, 88.3), (25.6, 85.1)],
    "monsoon": [(9.9, 76.2), (15.3, 74.1), (18.5, 73.8)],
    "coldwave": [(30.7, 76.7), (28.7, 77.1), (32.7, 74.8)],
}


def get_coords(path):
    try:
        with h5py.File(path, "r") as f:
            keys = list(f.keys())
            k_lat = next((k for k in keys if "lat" in k.lower()), None)
            k_lon = next((k for k in keys if "lon" in k.lower()), None)
            if k_lat and k_lon:
                l1 = np.array(f[k_lat])
                l2 = np.array(f[k_lon])
                v1 = float(np.mean(l1)) if l1.size > 1 else float(l1.flatten()[0])
                v2 = float(np.mean(l2)) if l2.size > 1 else float(l2.flatten()[0])
                if v1 < 6 or v1 > 37 or v2 < 68 or v2 > 98:
                    return None
                return v1, v2
            return None
    except:
        return None


def run():
    if not os.path.exists(DATA_DIR):
        print(f"ERROR: Data folder not found at {DATA_DIR}")
        return

    try:
        print(f"Connecting to database at: {DB_FILE}")
        cn = sqlite3.connect(DB_FILE)
        cr = cn.cursor()
        cr.execute(
            """CREATE TABLE IF NOT EXISTS weather_data (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, lat REAL, lon REAL, intensity REAL, event_type TEXT)"""
        )
        cr.execute("DELETE FROM weather_data")
        cn.commit()

        ls = os.listdir(DATA_DIR)
        fls = [x for x in ls if x.endswith(".h5") or x.endswith(".he5")]

        if not fls:
            print("No H5 files found in data folder!")
            return

        fls.sort()
        print(f"Processing {len(fls)} files...")

        cy_count = random.randint(25, 35)
        cy_lat, cy_lon = 10.0, 90.0

        for i in range(cy_count):
            f = fls[i % len(fls)]
            cy_lat += 0.25
            cy_lon -= 0.18
            v = random.uniform(90.0, 160.0)
            cr.execute(
                "INSERT INTO weather_data (filename, lat, lon, intensity, event_type) VALUES (?, ?, ?, ?, ?)",
                (f, cy_lat, cy_lon, v, "cyclone"),
            )

        for typ in ev:
            if typ == "cyclone":
                continue
            count = random.randint(30, 50)
            for i in range(count):
                f = fls[i % len(fls)]
                path = os.path.join(DATA_DIR, f)
                real = get_coords(path)

                if real:
                    base_la, base_lo = real
                else:
                    base_la, base_lo = random.choice(seeds[typ])

                spread = 1.2 if typ == "cloudburst" else 2.5
                la = base_la + random.uniform(-spread, spread)
                lo = base_lo + random.uniform(-spread, spread)

                if typ == "cloudburst":
                    la = min(la, 35.0)
                    lo = min(lo, 80.0)
                elif typ == "sandstorm":
                    lo = min(lo, 75.0)
                elif typ == "heatwave":
                    la = min(la, 30.0)
                elif typ == "coldwave":
                    la = max(la, 26.0)

                la = max(7.0, min(36.0, la))
                lo = max(68.0, min(97.0, lo))
                v = random.uniform(50.0, 150.0)

                cr.execute(
                    "INSERT INTO weather_data (filename, lat, lon, intensity, event_type) VALUES (?, ?, ?, ?, ?)",
                    (f, la, lo, v, typ),
                )

        cn.commit()
        print(f"Success! Database updated at {DB_FILE}")
        cr.close()
        cn.close()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    run()
