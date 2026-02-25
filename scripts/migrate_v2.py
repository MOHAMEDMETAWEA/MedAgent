"""
Migration script to update medagent.db with new role-based fields.
"""
import sqlite3
import os

def migrate():
    db_path = "medagent.db"
    if not os.path.exists(db_path):
        print("Database not found. Skipping migration.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Update user_accounts table
    columns_to_add = [
        ("gender", "TEXT"),
        ("age", "INTEGER"),
        ("country", "TEXT"),
        ("interaction_mode", "TEXT DEFAULT 'patient'"),
        ("doctor_verified", "BOOLEAN DEFAULT 0"),
        ("license_number", "TEXT"),
        ("specialization", "TEXT")
    ]

    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE user_accounts ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name} to user_accounts.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column {col_name} already exists in user_accounts.")
            else:
                print(f"Error adding column {col_name}: {e}")

    # 2. Update user_sessions table
    try:
        cursor.execute("ALTER TABLE user_sessions ADD COLUMN interaction_mode TEXT DEFAULT 'patient'")
        print("Added column interaction_mode to user_sessions.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column interaction_mode already exists in user_sessions.")
        else:
            print(f"Error adding column interaction_mode: {e}")

    # 3. Update interactions table with lineage and observability fields
    interaction_columns = [
        ("prompt_version", "TEXT"),
        ("model_used", "TEXT"),
        ("confidence_score", "REAL"),
        ("risk_level", "TEXT"),
        ("audit_hash", "TEXT"),
        ("secondary_model", "TEXT"),
        ("latency_ms", "INTEGER")
    ]
    for col_name, col_type in interaction_columns:
        try:
            cursor.execute(f"ALTER TABLE interactions ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name} to interactions.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column {col_name} already exists in interactions.")
            else:
                print(f"Error adding column {col_name} to interactions: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
