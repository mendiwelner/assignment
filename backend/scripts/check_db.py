import sqlite3
import os

db = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'telemetry.db'))
print('DB:', db)
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print('tables =', tables)
if any('telemetry_readings' in t for t in tables):
    try:
        rows = conn.execute('SELECT COUNT(*) FROM telemetry_readings').fetchone()[0]
        print('rows =', rows)
    except Exception as e:
        print('count error:', e)
else:
    print('no telemetry_readings table')
conn.close()
