import psycopg2
import os

db_url = "postgresql://uzum_user:uzum_pass2026@postgres.railway.internal:5432/uzum_db"

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Add columns if they don't exist
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS fbo_stock INTEGER DEFAULT 0;")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS fbs_stock INTEGER DEFAULT 0;")
    
    conn.commit()
    cur.close()
    conn.close()
    print("Database updated successfully!")
except Exception as e:
    print(f"Error updating database: {e}")
