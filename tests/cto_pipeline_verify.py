import json
import os

import requests

BASE_URL = "http://localhost:8000"


def test_consult_text_only():
    print("\n--- Testing Consult (Text Only) ---")
    payload = {
        "symptoms": "I have a severe headache and sensitivity to light.",
        "patient_id": "auditor_test_user",
        "interaction_mode": "patient",
    }
    response = requests.post(f"{BASE_URL}/consult", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Agent Path: {data.get('status')}")
        print(f"Diagnosis Snippet: {data.get('preliminary_diagnosis')[:100]}...")
    else:
        print(f"Error: {response.text}")


def test_consult_with_image():
    print("\n--- Testing Consult (With Image) ---")
    # Using existing test image in repo
    image_path = "d:/MedAgent/test_Xray.jpeg"
    if not os.path.exists(image_path):
        print(f"Skipping: {image_path} not found.")
        return

    payload = {
        "symptoms": "My arm hurts after a fall.",
        "patient_id": "auditor_test_user",
        "image_path": image_path,
        "interaction_mode": "patient",
    }
    response = requests.post(f"{BASE_URL}/consult", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(
            f"Visual Findings: {data.get('visual_findings', {}).get('status', 'not_found')}"
        )
        print(f"Diagnosis Snippet: {data.get('preliminary_diagnosis')[:100]}...")
    else:
        print(f"Error: {response.text}")


if __name__ == "__main__":
    # Ensure server is running
    try:
        test_consult_text_only()
        test_consult_with_image()
    except Exception as e:
        print(f"Connection failed: {e}")
