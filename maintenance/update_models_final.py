
import os
import sys

# Define the relative path from the project root
rel_path = os.path.join("database", "models.py")

if not os.path.exists(rel_path):
    print(f"FAILED: Could not find {rel_path} in {os.getcwd()}")
    sys.exit(1)

with open(rel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_feedback_class = [
    "class Feedback(Base):\n",
    "    \"\"\"Enhanced clinical feedback table for RLHF.\"\"\"\n",
    "    __tablename__ = \"feedback\"\n",
    "    \n",
    "    id = Column(Integer, primary_key=True, autoincrement=True)\n",
    "    user_id = Column(String, ForeignKey(\"user_accounts.id\"), index=True)\n",
    "    role = Column(String) # doctor | patient\n",
    "    case_id = Column(String, ForeignKey(\"medical_cases.id\"), index=True, nullable=True)\n",
    "    \n",
    "    # Encrypted fields for medical privacy\n",
    "    ai_response_encrypted = Column(Text)\n",
    "    comment_encrypted = Column(Text, nullable=True)\n",
    "    corrected_response_encrypted = Column(Text, nullable=True) # doctor only\n",
    "    \n",
    "    rating = Column(Integer) # 0-5\n",
    "    timestamp = Column(DateTime, default=datetime.datetime.utcnow)\n",
    "    \n",
    "    # Relationships\n",
    "    user = relationship(\"UserAccount\")\n",
    "    case = relationship(\"MedicalCase\")\n",
    "\n"
]

# Check if already exists
if any("class Feedback(Base):" in line for line in lines):
    print("Feedback class already exists.")
    sys.exit(0)

# Find insertion point: before class AuditLog(Base):
inserted = False
for i, line in enumerate(lines):
    if "class AuditLog(Base):" in line:
        # Insert before this line
        for j, new_line in enumerate(new_feedback_class):
            lines.insert(i + j, new_line)
        inserted = True
        break

if not inserted:
    print("FAILED: Could not find insertion point 'class AuditLog(Base):'")
    sys.exit(1)

with open(rel_path, 'w', encoding='utf-8', newline='') as f:
    f.writelines(lines)

print("Feedback class added successfully.")
