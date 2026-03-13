import traceback
import sys
import os

print("--- DEBUG START ---")
try:
    print("Importing app from api.main...")
    from api.main import app
    print("Import SUCCESS")
except Exception:
    print("Import FAILED")
    traceback.print_exc()
print("--- DEBUG END ---")
