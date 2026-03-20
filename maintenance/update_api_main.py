
import os

file_path = "api/main.py"

if not os.path.exists(file_path):
    print(f"Error: {file_path} not found.")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Add import
import_found = False
for i, line in enumerate(lines):
    if "from api.routes import auth, clinical, patient, governance, system, imaging" in line:
        lines[i] = line.replace("imaging", "imaging, feedback")
        import_found = True
        break

if not import_found:
    print("Warning: Could not find exact import line. Adding after other imports.")
    for i, line in enumerate(lines):
        if "from api.routes import" in line:
             lines[i] = line.strip() + ", feedback\n"
             import_found = True
             break

# 2. Add router inclusion
router_added = False
for i, line in enumerate(lines):
    if "app.include_router(imaging.router)" in line:
        lines.insert(i + 1, "app.include_router(feedback.router)\n")
        router_added = True
        break

if not router_added:
    print("Warning: Could not find imaging router inclusion. Adding after last router.")
    for i, line in enumerate(reversed(lines)):
        if "app.include_router" in line:
            lines.insert(len(lines) - i, "app.include_router(feedback.router)\n")
            router_added = True
            break

with open(file_path, 'w', encoding='utf-8', newline='') as f:
    f.writelines(lines)

print("api/main.py updated successfully.")
