import requests
import uuid
import time
import concurrent.futures

BASE_URL = "http://localhost:8000"

def test_registration_flow():
    print("\n--- Testing Registration Flow ---")
    unique_id = str(uuid.uuid4())[:8]
    payload = {
        "username": f"testuser_{unique_id}",
        "email": f"test_{unique_id}@medagent.com",
        "phone": f"555-{unique_id}",
        "password": "SecurePassword123!",
        "full_name": "Auditor Test User",
        "role": "patient",
        "age": 30,
        "gender": "Male",
        "country": "Egypt"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print(f"Register Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Registration Success")
        return payload
    else:
        print(f"❌ Registration Failed: {response.text}")
        return None

def test_login_flow(reg_data):
    if not reg_data: return
    print("\n--- Testing Login Flow ---")
    payload = {
        "login_id": reg_data["username"],
        "password": reg_data["password"]
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=payload)
    print(f"Login Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("✅ Login Success")
        print(f"Token: {data.get('access_token')[:20]}...")
        return data.get("access_token")
    else:
        print(f"❌ Login Failed: {response.text}")
        return None

def test_concurrent_logins(reg_data):
    if not reg_data: return
    print(f"\n--- Testing Concurrent Logins (5 users) ---")
    
    def login_task():
        payload = {
            "login_id": reg_data["username"],
            "password": reg_data["password"]
        }
        return requests.post(f"{BASE_URL}/auth/login", json=payload).status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda _: login_task(), range(5)))
    
    print(f"Results: {results}")
    if all(r == 200 for r in results):
        print("✅ Concurrent Login Success")
    else:
        print("❌ Concurrent Login Partial Failure")

def test_auth_protected_route(token):
    if not token: return
    print("\n--- Testing Protected Route (/auth/me) ---")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Auth Persistence Success")
    else:
        print(f"❌ Auth Persistence Failed: {response.text}")

if __name__ == "__main__":
    reg = test_registration_flow()
    token = test_login_flow(reg)
    test_auth_protected_route(token)
    test_concurrent_logins(reg)
