import psycopg2

db = {
    "dbname": "weather_db",
    "user": "postgres",
    "password": "2118",
    "host": "127.0.0.1",
    "port": "5757",
}
try:
    c = psycopg2.connect(**db)
    cur = c.cursor()
    cur.execute("SELECT count(*) FROM weatheralert")
    print(cur.fetchone()[0])
    c.close()
except Exception as e:
    print(e)
