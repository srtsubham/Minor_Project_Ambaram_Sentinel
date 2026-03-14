import os

import pandas as pd
import requests


def send_telegram_message(message):
    bot_token = "#"  # Bot creation token here.
    chat_id = "#"  # Chat ID of Bot created in Telegram.
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending message: {e}")


def check_alerts():
    db_path = os.path.join(os.path.dirname(__file__), "weather.db")

    if not os.path.exists(db_path):
        return

    try:
        con = sqlite3.connect(db_path)
        q = "SELECT lat, lon, intensity, event_type FROM weather_data ORDER BY id DESC LIMIT 5"
        df = pd.read_sql(q, con)
        con.close()

        if df.empty:
            return

        for index, row in df.iterrows():
            intensity = row["intensity"]
            event_type = row["event_type"]

            thresholds = {"cyclone": 100, "heatwave": 120, "rainfall": 50}

            limit = thresholds.get(event_type.lower(), 80)

            if intensity > limit:
                msg = (
                    f"🚨 <b>EXTREME WEATHER ALERT</b> 🚨\n\n"
                    f"<b>Event:</b> {event_type.upper()}\n"
                    f"<b>Location:</b> Lat {row['lat']:.2f}, Lon {row['lon']:.2f}\n"
                    f"<b>Intensity:</b> {intensity:.1f}\n\n"
                    f"<b>Measures:</b> {intensity:.1f}\n\n"
                    f"<i>Ambaram Automated System</i>"
                )
                send_telegram_message(msg)

    except Exception as e:
        print(f"Database error: {e}")


if __name__ == "__main__":
    check_alerts()
