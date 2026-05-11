import os

import requests

BASE_URL = "http://localhost:8000"


def test_directory_traversal():
    print("\n--- Testing Directory Traversal on Upload ---")
    # Attempting to upload a file with a malicious name
    # Pydantic/FastAPI UploadFile usually handles the filename, but let's check.
    files = {"file": ("../../.env", "fake content", "image/jpeg")}
    response = requests.post(f"{BASE_URL}/upload", files=files)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

    if ".env" in response.text and response.status_code == 200:
        print("❌ VULNERABILITY DETECTED: Directory Traversal!")
    else:
        print("✅ SAFE: Filename properly sanitized or ignored.")


if __name__ == "__main__":
    test_directory_traversal()
