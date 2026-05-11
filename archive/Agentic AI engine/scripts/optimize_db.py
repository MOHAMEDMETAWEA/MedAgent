import os
import sqlite3

DB_PATH = "medagent.db"


def add_indexes():
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_medical_reports_patient_id ON medical_reports (patient_id);",
        "CREATE INDEX IF NOT EXISTS idx_medical_images_patient_id ON medical_images (patient_id);",
        "CREATE INDEX IF NOT EXISTS idx_memory_nodes_user_id ON memory_nodes (user_id);",
        "CREATE INDEX IF NOT EXISTS idx_memory_edges_user_id ON memory_edges (user_id);",
        "CREATE INDEX IF NOT EXISTS idx_interactions_session_id ON interactions (session_id);",
        "CREATE INDEX IF NOT EXISTS idx_interactions_case_id ON interactions (case_id);",
    ]

    for idx_sql in indexes:
        print(f"Applying: {idx_sql}")
        cursor.execute(idx_sql)

    conn.commit()
    conn.close()
    print("Database indexing complete.")


if __name__ == "__main__":
    add_indexes()
