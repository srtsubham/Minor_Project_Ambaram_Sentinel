import os

import h5py
import numpy as np
import psycopg2

info = {
    "dbname": "weather_db",
    "user": "postgres",
    "password": "2118",
    "host": "127.0.0.1",
    "port": "5757",
}


def run_scan():
    conn = psycopg2.connect(**info)
    cur = conn.cursor()

    folder = "data"
    files = [f for f in os.listdir(folder) if f.endswith(".h5")]

    for name in files:
        path = os.path.join(folder, name)
        print(f"--- Processing {name} ---")

        try:
            with h5py.File(path, "r") as f:
                heat_flat = f["IMG_TIR1_TEMP"][()].flatten()
                indices = np.where((heat_flat < 240) & (heat_flat > 0))[0]

                cols = 1024
                rows = len(heat_flat) // cols

                lat_start, lat_end = 25.0, 5.0
                lon_start, lon_end = 70.0, 100.0

                lats_vec = np.linspace(lat_start, lat_end, rows)
                lons_vec = np.linspace(lon_start, lon_end, cols)

                saved_count = 0
                for i in range(0, len(indices), 15):
                    idx = indices[i]
                    r = idx // cols
                    c = idx % cols

                    la = float(lats_vec[r])
                    lo = float(lons_vec[c])

                    cur.execute(
                        "INSERT INTO weatheralert (lat, lon, temperature, source_file) VALUES (%s, %s, %s, %s)",
                        (la, lo, float(heat_flat[idx]), name),
                    )
                    saved_count += 1

                    conn.commit()
                print(f"✅ SUCCESS: Saved {saved_count} points for {name}")

        except Exception as e:
            print(f"❌ Error: {e}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    run_scan()
