import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import settings
from database.models import init_db


async def main():
    print(f"Initializing database at: {settings.DATABASE_URL}")
    await init_db()
    print("Database initialization complete.")


if __name__ == "__main__":
    asyncio.run(main())
