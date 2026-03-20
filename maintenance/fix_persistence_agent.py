
import os

file_path = "agents/persistence_agent.py"

if not os.path.exists(file_path):
    print(f"Error: {file_path} not found.")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# The error is near lines 180-210.
# Let's find the corrupted block and fix it.
# Line 196 starts with "if redacted_details:" but should be inside the except or part of the next method.
# It seems lines 196 to 210 are a duplication.

new_lines = []
skip = False
for i, line in enumerate(lines):
    # Detect the redundant block start
    if i == 195 and "if redacted_details:" in lines[i+1]:
        print(f"Found duplication start at line {i+2}")
        skip = True
    
    # Redundant block end (just before save_interaction)
    if skip and "async def save_interaction" in line:
        skip = False
    
    if not skip:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8', newline='') as f:
    f.writelines(new_lines)

print("Fixed agents/persistence_agent.py (removed duplicated/misindented block).")
