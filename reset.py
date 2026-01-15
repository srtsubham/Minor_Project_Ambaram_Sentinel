import psycopg2

info = {
    "dbname": "weather_db",
    "user": "postgres",
    "password": "2118",
    "host": "127.0.0.1",
    "port": "5757",
}


def reset_table():
    conn = psycopg2.connect(**info)
    cur = conn.cursor()

    # Delete the old table and make a fresh one
    cur.execute("DROP TABLE IF EXISTS weatheralert;")
    cur.execute("""
        CREATE TABLE weatheralert (
            id SERIAL PRIMARY KEY,
            lat FLOAT,
            lon FLOAT,
            temperature FLOAT,
            source_file TEXT
        );
    """)

    conn.commit()
    print("Table reset! Names are now: lat, lon, temperature, source_file")
    cur.close()
    conn.close()


reset_table()
