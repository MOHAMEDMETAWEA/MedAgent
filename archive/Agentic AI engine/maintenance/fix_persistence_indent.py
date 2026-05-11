import os
import sys

file_path = "agents/persistence_agent.py"

if not os.path.exists(file_path):
    print(f"Error: {file_path} not found.")
    sys.exit(1)

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Fix indentation at line 269 (0-indexed 268)
# Current:
# 268:         async with AsyncSessionLocal() as db:
# 269:         try:
# 270:             return await self._upsert_patient_profile_db(db, user_id, name, age, gender, history_json)

for i in range(len(lines)):
    if (
        "async with AsyncSessionLocal() as db:" in lines[i]
        and i + 1 < len(lines)
        and lines[i + 1].strip() == "try:"
    ):
        # Indent the try block and its associated lines
        # But wait, we should just indent everything inside the with block.
        # Let's find the with block and indent its children.
        # In our case, it's lines i+1 to the next method or end of trying.

        # Looking at lines 268-272:
        # 268:         async with AsyncSessionLocal() as db:
        # 269:         try:
        # 270:             return await self._upsert_patient_profile_db(db, user_id, name, age, gender, history_json)
        # 271:         finally:
        # 272:             db.close()

        # We also want to remove 271-272 if they are inside the wrong block.
        # Actually, let's just rewrite the whole method 'upsert_patient_profile'.
        pass

# Targeted replacement of the whole method
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if "async def upsert_patient_profile(self, user_id: str" in line:
        start_idx = i
    if start_idx != -1 and "async def _upsert_patient_profile_db" in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    new_method = [
        "    async def upsert_patient_profile(self, user_id: str, name: str, age: int, gender: str, history_json: str):\n",
        '        """Create or Update patient profile securely."""\n',
        "        async with AsyncSessionLocal() as db:\n",
        "            try:\n",
        "                return await self._upsert_patient_profile_db(db, user_id, name, age, gender, history_json)\n",
        "            except Exception as e:\n",
        '                logger.error(f"Failed in upsert_patient_profile session: {e}")\n',
        "                return False\n",
        "\n",
    ]
    lines = lines[:start_idx] + new_method + lines[end_idx:]

with open(file_path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"Fixed indentation and session management in {file_path}")
