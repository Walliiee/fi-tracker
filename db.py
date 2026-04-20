import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'data', 'fi_tracker.db')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    conn = get_db()
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    conn.close()
