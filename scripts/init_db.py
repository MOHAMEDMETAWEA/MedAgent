import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.models import Base, init_db
from config import settings

def main():
    db_url = getattr(settings, "DATABASE_URL", "sqlite:///./medagent.db")
    print(f"Initializing database at: {db_url}")
    SessionLocal = init_db(db_url)
    print("Database initialization complete.")

if __name__ == "__main__":
    main()
