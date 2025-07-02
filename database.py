
import sqlite3
import json
from datetime import datetime
import hashlib # <--- ADDED: For password hashing

DATABASE_NAME = "data_upload_query.db"

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    return conn

def init_db():
    """Initializes the database by creating necessary tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create the 'data' table to store CSV rows as JSON strings
    # This design allows for flexible CSV schemas without altering the table structure
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_filename TEXT NOT NULL,
            row_data TEXT NOT NULL, -- Stores each row as a JSON string
            upload_timestamp TEXT NOT NULL
        );
    """)

    # Create the 'logs' table to store API request logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            method TEXT NOT NULL,
            path TEXT NOT NULL,
            status_code INTEGER,
            response_time_ms REAL
        );
    """)

    # --- ADDED: Create the 'users' table for username/password authentication ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            hashed_password TEXT NOT NULL
        );
    """)
    # --- END ADDED SECTION ---

    conn.commit()
    conn.close()
    print(f"Database '{DATABASE_NAME}' initialized successfully.")

def insert_data_row(filename: str, row_data: dict):
    """Inserts a single row of CSV data into the 'data' table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO data (original_filename, row_data, upload_timestamp) VALUES (?, ?, ?)",
            (filename, json.dumps(row_data), datetime.now().isoformat())
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Database error inserting data row: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_all_data():
    """Retrieves all data rows from the 'data' table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, original_filename, row_data, upload_timestamp FROM data ORDER BY upload_timestamp DESC;")
    rows = cursor.fetchall()
    conn.close()
    # Convert row_data from JSON string back to dictionary
    return [{**dict(row), 'row_data': json.loads(row['row_data'])} for row in rows]

def get_data_by_id(item_id: int):
    """Retrieves a specific data row by its ID from the 'data' table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, original_filename, row_data, upload_timestamp FROM data WHERE id = ?;", (item_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {**dict(row), 'row_data': json.loads(row['row_data'])}
    return None

def insert_log_entry(method: str, path: str, status_code: int, response_time_ms: float):
    """Inserts an API log entry into the 'logs' table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO logs (timestamp, method, path, status_code, response_time_ms) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), method, path, status_code, response_time_ms)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error inserting log entry: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_all_logs():
    """Retrieves all log entries from the 'logs' table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, method, path, status_code, response_time_ms FROM logs ORDER BY timestamp DESC;")
    logs = cursor.fetchall()
    conn.close()
    return [dict(log) for log in logs]

# --- ADDED: NEW FUNCTIONS FOR USER MANAGEMENT ---
def hash_password(password: str) -> str:
    """Hashes a password using SHA256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_user_by_username(username: str):
    """Retrieves a user by their username."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, hashed_password FROM users WHERE username = ?;", (username,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def create_user(username: str, hashed_password: str):
    """Creates a new user in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
            (username, hashed_password)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError: # Handles UNIQUE constraint violation for username
        print(f"User '{username}' already exists.")
        return None # Username already exists
    except sqlite3.Error as e:
        print(f"Database error creating user: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()
# --- END ADDED SECTION ---

# Initialize the database when this module is imported
init_db()
