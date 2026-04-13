import os
import sys

# Mocking AgentState
state = {
    "interaction_mode": "patient",
    "medical_literacy_level": "low",
    "user_age": 75,
    "final_response": "The patient has severe hypertension and tachycardia.",
    "language": "en",
}

# Test 1: Full Replacement (Low Literacy/Elderly)
print("--- Test 1: Full Replacement (Low Literacy + Elderly) ---")
from utils.medical_terms import explain_text

raw = "The patient has severe Hypertension and Tachycardia."
output = explain_text(raw, replace_only=True)
print(f"Input: {raw}")
print(f"Output: {output}")

# Test 2: Annotated (Standard)
print("\n--- Test 2: Annotated (Standard) ---")
output2 = explain_text(raw, replace_only=False)
print(f"Input: {raw}")
print(f"Output: {output2}")

# Test 3: Casing preservation
print("\n--- Test 3: Casing Preservation ---")
raw3 = "hypertension is bad, but Hypertension is worse."
output3 = explain_text(raw3, replace_only=True)
print(f"Input: {raw3}")
print(f"Output: {output3}")

# Final Log
with open("verify_results.txt", "w") as f:
    f.write(f"Test 1: {output}\n")
    f.write(f"Test 2: {output2}\n")
    f.write(f"Test 3: {output3}\n")
