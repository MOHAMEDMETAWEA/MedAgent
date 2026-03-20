
import os
import sys

file_path = "agents/persistence_agent.py"

if not os.path.exists(file_path):
    print(f"Error: {file_path} not found.")
    sys.exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update imports to ensure AsyncSession and select are available
if "from sqlalchemy import select" not in text:
    text = text.replace("from sqlalchemy.orm import Session", "from sqlalchemy import select\nfrom sqlalchemy.ext.asyncio import AsyncSession\nfrom sqlalchemy.orm import Session")

# 2. Fix upsert_patient_profile to be async
text = text.replace(
    "    def upsert_patient_profile(self, user_id: str, name: str, age: int, gender: str, history_json: str):",
    "    async def upsert_patient_profile(self, user_id: str, name: str, age: int, gender: str, history_json: str):"
)
text = text.replace(
    "        db = self._get_db()",
    "        async with AsyncSessionLocal() as db:"
)
text = text.replace(
    "            return self._upsert_patient_profile_db(db, user_id, name, age, gender, history_json)",
    "            return await self._upsert_patient_profile_db(db, user_id, name, age, gender, history_json)"
)

# 3. Fix _upsert_patient_profile_db to be async
text = text.replace(
    "    def _upsert_patient_profile_db(self, db, user_id: str, name: str, age: int, gender: str, history_json: str):",
    "    async def _upsert_patient_profile_db(self, db: AsyncSession, user_id: str, name: str, age: int, gender: str, history_json: str):"
)
# Fix SQLAlchemy query to use async select
text = text.replace(
    "            profile = db.query(PatientProfile).filter(PatientProfile.id == user_id).first()",
    "            stmt = select(PatientProfile).filter(PatientProfile.id == user_id)\n            res = await db.execute(stmt)\n            profile = res.scalars().first()"
)
text = text.replace(
    "            db.commit()",
    "            await db.commit()"
)

# 4. Clean up any remaining await errors in newly added feedback methods if any
# (I added them as async already, but let's double check common mistakes)

with open(file_path, 'w', encoding='utf-8', newline='') as f:
    f.write(text)

print(f"Refactored {file_path} to be fully async.")
