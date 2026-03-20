
import os
import sys

file_path = "agents/persistence_agent.py"

if not os.path.exists(file_path):
    print(f"Error: {file_path} not found.")
    sys.exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_method = [
    "    async def log_system_event(self, level: str, component: str, message: str, details: dict = None, session_id: str = None):\n",
    "        \"\"\"Log a system event or error (Async).\"\"\"\n",
    "        async with AsyncSessionLocal() as db:\n",
    "            try:\n",
    "                # Optional PHI redaction of message/details\n",
    "                redacted_message = message\n",
    "                redacted_details = details or {}\n",
    "                try:\n",
    "                    from agents.safety.privacy_audit import PrivacyAuditLayer\n",
    "                    pal = PrivacyAuditLayer()\n",
    "                    redacted_message = pal.redact_phi(message) if message else message\n",
    "                    if redacted_details:\n",
    "                        redacted_details = {\"_redacted\": pal.redact_phi(str(redacted_details))}\n",
    "                except Exception:\n",
    "                    pass\n",
    "                log_entry = SystemLog(\n",
    "                    level=level,\n",
    "                    component=component,\n",
    "                    message=redacted_message,\n",
    "                    details=redacted_details,\n",
    "                    session_id=session_id\n",
    "                )\n",
    "                db.add(log_entry)\n",
    "                await db.commit()\n",
    "            except Exception as e:\n",
    "                logger.error(f\"DB Logging failed: {e}\")\n",
    "                await db.rollback()\n"
]

# Find start and end of the corrupted method
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if "async def log_system_event" in line:
        start_idx = i
    if start_idx != -1 and "async def get_user_history" in line:
        end_idx = i
        break

if start_idx == -1 or end_idx == -1:
    print(f"FAILED: Could not find method boundaries. Start: {start_idx}, End: {end_idx}")
    sys.exit(1)

# Construct new lines
final_lines = lines[:start_idx] + new_method + lines[end_idx:]

with open(file_path, 'w', encoding='utf-8', newline='') as f:
    f.writelines(final_lines)

print(f"REPLACED: log_system_event lines {start_idx+1} to {end_idx} in {file_path}")
