import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'uzum.db')

def add_column(cursor, table, column, type):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type}")
        print(f"Column {column} added to {table} successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"Column {column} already exists in {table}.")
        else:
            print(f"Error adding column {column} to {table}: {e}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Products table
    add_column(cursor, "products", "image_url", "TEXT")
    add_column(cursor, "products", "fbo_stock", "INTEGER DEFAULT 0")
    add_column(cursor, "products", "fbs_stock", "INTEGER DEFAULT 0")
    
    # Orders table
    add_column(cursor, "orders", "sku_code", "TEXT")
    add_column(cursor, "orders", "sku_title", "TEXT")
    add_column(cursor, "orders", "sku_char_title", "TEXT")
    add_column(cursor, "orders", "sku_char_value", "TEXT")
    
    conn.commit()
    conn.close()
    print("Database migration completed.")
except Exception as e:
    print(f"Migration error: {e}")
