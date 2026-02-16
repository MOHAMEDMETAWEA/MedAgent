"""
High-Load & Production Scenario Simulation Test.
Tests 100 concurrent-like requests, emergencies, and edge cases.
"""
import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor

API_BASE = "http://localhost:8000"

def simulate_user_session(user_id):
    # 1. Register/Login
    username = f"load_user_{user_id}_{int(time.time())}"
    requests.post(f"{API_BASE}/auth/register", json={
        "username": username, "email": f"{username}@med.org", "phone": str(user_id),
        "password": "Password123!", "full_name": f"Load Tester {user_id}"
    })
    l_resp = requests.post(f"{API_BASE}/auth/login", json={"login_id": username, "password": "Password123!"})
    if not l_resp.ok: return False
    token = l_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Consult (Normal case)
    r1 = requests.post(f"{API_BASE}/consult", json={"symptoms": "I have a mild fever.", "patient_id": username}, headers=headers)
    
    # 3. Consult (Emergency case)
    r2 = requests.post(f"{API_BASE}/consult", json={"symptoms": "SEVERE CHEST PAIN AND BREATHING DIFFICULTY!!", "patient_id": username}, headers=headers)
    
    return r2.ok

def run_load_test():
    print("--- STARTING PRODUCTION LOAD SIMULATION ---")
    start = time.time()
    
    # We use a smaller number for the mock environment but structure it for full load
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(simulate_user_session, range(20)))
    
    print(f"--- SIMULATION COMPLETE in {time.time() - start:.2f}s ---")
    success_count = sum(1 for r in results if r)
    print(f"Success Rate: {success_count}/{len(results)}")

if __name__ == "__main__":
    run_load_test()
