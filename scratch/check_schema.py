import sqlite3

conn = sqlite3.connect('brain.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(customers)")
columns = cursor.fetchall()
for col in columns:
    print(col)
conn.close()
