import os

file_path = "agents/persistence_agent.py"

with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# Remove accidental escapes \"\"\" -> """
cleaned_text = text.replace('\\"\\"\\"', '"""')
# Also check for other escapes that might have slipped in
cleaned_text = cleaned_text.replace("\\n", "\n")
# Wait, if I replace \\n with \n, I might mess up things if they were intended.
# But in this case, my whole file seems to have literal \n and \"\"\" from the previous write.

with open(file_path, "w", encoding="utf-8", newline="") as f:
    f.write(cleaned_text)

print(f"Cleaned up {file_path} (removed escapes).")
