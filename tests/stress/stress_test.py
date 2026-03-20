import asyncio
import httpx
import time
import random

API_BASE = "http://127.0.0.1:8000"

async def simulate_user(user_id):
    async with httpx.AsyncClient(timeout=60.0) as client:
        username = f"stress_user_{user_id}_{random.randint(1000, 9999)}"
        password = "StressPassword123!"
        
        print(f"[User {user_id}] Registering as {username}...")
        reg_resp = await client.post(f"{API_BASE}/auth/register", json={
            "username": username,
            "email": f"{username}@example.com",
            "phone": f"555{random.randint(100000, 999999)}",
            "password": password,
            "full_name": f"Stress Tester {user_id}",
            "age": 30,
            "gender": "Other",
            "country": "TestWorld",
            "role": "patient"
        })
        
        if reg_resp.status_code != 200:
            print(f"[User {user_id}] Registration failed: {reg_resp.text}")
            return False
            
        print(f"[User {user_id}] Logging in...")
        login_resp = await client.post(f"{API_BASE}/auth/login", json={
            "login_id": username,
            "password": password
        })
        
        if login_resp.status_code != 200:
            print(f"[User {user_id}] Login failed: {login_resp.text}")
            return False
            
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print(f"[User {user_id}] Running consultation...")
        start = time.time()
        consult_resp = await client.post(f"{API_BASE}/consult", json={
            "symptoms": f"Concurrent stress test symptom from user {user_id}",
            "patient_id": username,
            "language": "en"
        }, headers=headers)
        duration = time.time() - start
        
        if consult_resp.status_code != 200:
            print(f"[User {user_id}] Consultation failed: {consult_resp.text}")
            return False
            
        print(f"[User {user_id}] Consultation success in {duration:.2f}s")
        
        # Verify isolation: Check if images or reports from other users show up
        print(f"[User {user_id}] Checking report isolation...")
        reports_resp = await client.get(f"{API_BASE}/reports", headers=headers)
        reports = reports_resp.json()
        if any(r.get("patient_id") != username for r in reports if "patient_id" in r):
            print(f"[User {user_id}] ERROR: Detected data leakage in reports!")
            return False
            
        return True

async def main():
    num_users = 5
    print(f"Starting stress test with {num_users} concurrent users...")
    tasks = [simulate_user(i) for i in range(num_users)]
    results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r)
    print(f"\nStress Test Summary: {success_count}/{num_users} users succeeded.")
    if success_count == num_users:
        print("RESULT: SUCCESS - System is stable under concurrent load.")
    else:
        print("RESULT: FAILURE - System encountered errors or data isolation issues.")

if __name__ == "__main__":
    asyncio.run(main())
