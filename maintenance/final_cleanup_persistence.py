
import os

file_path = "agents/persistence_agent.py"

with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Remove accidental escapes
# 1. Backslashes before quotes
text = text.replace('\\"', '"')
# 2. Backslashes before single quotes if any
text = text.replace("\\'", "'")
# 3. Triple quote escapes if any
text = text.replace('\\"\\"\\"', '"""')
# 4. Newline escapes if any
text = text.replace('\\n', '\n')

with open(file_path, 'w', encoding='utf-8', newline='') as f:
    f.write(text)

print(f"Cleaned up {file_path} (removed all unintended backslash escapes).")
