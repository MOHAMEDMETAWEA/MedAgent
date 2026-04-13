import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from database.models import init_db


async def run_init():
    print("Initializing database...")
    await init_db()
    print("Database initialized successfully.")


if __name__ == "__main__":
    asyncio.run(run_init())
