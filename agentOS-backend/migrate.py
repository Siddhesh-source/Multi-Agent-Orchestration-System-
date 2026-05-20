"""
One-time migration: add started_at column to tasks table.
Safe to run multiple times (checks if column exists first).
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "agentOS.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check existing columns
cursor.execute("PRAGMA table_info(tasks)")
columns = [row[1] for row in cursor.fetchall()]
print(f"Existing columns: {columns}")

if "started_at" not in columns:
    cursor.execute("ALTER TABLE tasks ADD COLUMN started_at DATETIME")
    conn.commit()
    print("Added 'started_at' column to tasks table.")
else:
    print("'started_at' column already exists, skipping.")

conn.close()
print("Migration complete.")
