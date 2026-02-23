import os
import requests
import json
import time

API_BASE = "http://127.0.0.1:8000"

def test_system_flow():
    print("--- 🔬 STARTING SYSTEM-WIDE VALIDATION TEST ---")
    
    # 1. Login/Register
    print("[TEST 1] Testing Auth Flow...")
    reg_data = {
        "username": "testuser_unique",
        "email": "test@example.com",
        "phone": "123456789",
        "password": "testpassword",
        "full_name": "Test User",
        "age": 30,
        "gender": "Male",
        "country": "Egypt",
        "role": "patient"
    }
    # Using existing user if registration fails due to duplicate
    r = requests.post(f"{API_BASE}/auth/register", json=reg_data)
    
    login_data = {"login_id": "testuser_unique", "password": "testpassword"}
    r = requests.post(f"{API_BASE}/auth/login", json=login_data)
    if not r.ok:
        print(f"FAILED: Login failed: {r.text}")
        return
    
    auth = r.json()
    token = auth["access_token"]
    user_id = auth["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Auth Flow Successful.")

    # 2. Image Upload Simulation (X-ray placeholder)
    print("\n[TEST 2] Testing Medical Image Upload & Analysis...")
    # Create a small dummy image file
    with open("test_xray.png", "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdcD\xfe\xe8\x00\x00\x00\x00IEND\xaeB`\x82")
    
    files = {"file": ("test_xray.png", open("test_xray.png", "rb"))}
    ur = requests.post(f"{API_BASE}/upload", files=files, headers=headers)
    if not ur.ok:
        print(f"FAILED: Image upload failed: {ur.text}")
        return
    
    img_path = ur.json()["image_path"]
    print(f"✅ Image Upload Successful: {img_path}")

    # 3. Consult with Image
    print("\n[TEST 3] Testing Multi-Agent Consultation (Vision + RAG + ToT)...")
    consult_data = {
        "symptoms": "I have been coughing for 2 weeks and have chest pain.",
        "image_path": img_path,
        "patient_id": user_id,
        "language": "en"
    }
    cr = requests.post(f"{API_BASE}/consult", json=consult_data, headers=headers)
    if not cr.ok:
        print(f"FAILED: Consultation failed: {cr.text}")
    else:
        res = cr.json()
        print("✅ Consultation Successful.")
        print(f"--- PRELIMINARY DIAGNOSIS ---\n{res.get('preliminary_diagnosis')[:200]}...")
        print(f"--- VISUAL FINDINGS ---\n{res.get('visual_findings', {}).get('visual_findings', 'N/A')}")
        print(f"--- REPORT ID: {res.get('report_id')} ---")

    # 4. History Retrieval
    print("\n[TEST 4] Testing History and Memory Graph Persistence...")
    hr = requests.get(f"{API_BASE}/reports", headers=headers)
    if hr.ok and len(hr.json()) > 0:
        print(f"✅ Found {len(hr.json())} reports in history.")
    else:
        print("FAILED: No reports found in history.")

    imr = requests.get(f"{API_BASE}/images", headers=headers)
    if imr.ok and len(imr.json()) > 0:
        print(f"✅ Found {len(imr.json())} image records in DB.")
    else:
        print("FAILED: No image records found in DB.")

    # 5. Admin System Check
    print("\n[TEST 5] Testing Admin Data Access...")
    admin_headers = {"X-Admin-Key": "admin-secret-dev"}
    ar = requests.get(f"{API_BASE}/system/health", headers=admin_headers)
    if ar.ok:
        print("✅ Admin System Health Access Successful.")
    else:
        print(f"FAILED: Admin access denied: {ar.text}")

    print("\n--- 🏁 SYSTEM VALIDATION COMPLETE ---")

if __name__ == "__main__":
    # Ensure background server is NOT running for this script if we want to test locally, 
    # but here we assume it IS running or we start it.
    # Since I can't easily start and stop, I'll just check if it's reachable.
    try:
        requests.get(f"{API_BASE}/health")
        test_system_flow()
    except:
        print("ERROR: Backend not reachable at http://localhost:8000. Start it first.")
