import sqlite3
import json

db_path = r"c:\Users\user\Desktop\uzum Pyton\backend\uzum.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("SELECT key, value FROM system_settings WHERE key='uzum_api_token'")
    row = cursor.fetchone()
    if row:
        print(f"Token in DB: {row[1][:10]}... (length: {len(row[1])})")
    else:
        print("No token found in DB.")
except Exception as e:
    print(f"Error reading from DB: {e}")

try:
    cursor.execute("SELECT COUNT(*) FROM shops")
    print(f"Shops count: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM products")
    print(f"Products count: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM orders")
    print(f"Orders count: {cursor.fetchone()[0]}")
except Exception as e:
    print(f"Error checking counts: {e}")

conn.close()
