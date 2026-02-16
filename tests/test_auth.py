"""
Auth System Test - Verifies Registration, Hash security, and Login.
"""
import requests
import time

API_BASE = "http://localhost:8000"

def test_auth_flow():
    print("--- Starting Auth System Test ---")
    
    unique_id = int(time.time())
    username = f"testuser_{unique_id}"
    email = f"test_{unique_id}@example.com"
    phone = f"+12345678{unique_id}"
    password = "StrongPass123!"
    
    # 1. Register User
    print("\n[1] Testing Registration...")
    payload = {
        "username": username,
        "email": email,
        "phone": phone,
        "password": password,
        "full_name": "Test User",
        "age": 30,
        "gender": "Male"
    }
    r = requests.post(f"{API_BASE}/auth/register", json=payload)
    if r.status_code == 200:
        print(f"✅ Registration successful for {username}")
    else:
        print(f"❌ Registration failed: {r.text}")
        return

    # 2. Duplicate Registration
    print("\n[2] Testing Duplicate Registration...")
    r = requests.post(f"{API_BASE}/auth/register", json=payload)
    if r.status_code == 400:
        print("✅ Duplicate registration correctly blocked.")
    else:
        print(f"❌ Duplicate registration was not blocked: {r.status_code}")

    # 3. Login
    print("\n[3] Testing Login (Email)...")
    login_payload = {"login_id": email, "password": password}
    r = requests.post(f"{API_BASE}/auth/login", json=login_payload)
    if r.status_code == 200:
        token = r.json()["access_token"]
        user_id = r.json()["user"]["id"]
        print(f"✅ Login successful. Token received. UserID: {user_id}")
    else:
        print(f"❌ Login failed: {r.text}")
        return

    # 4. Incorrect Password
    print("\n[4] Testing Incorrect Password...")
    r = requests.post(f"{API_BASE}/auth/login", json={"login_id": username, "password": "wrong"})
    if r.status_code == 401:
        print("✅ Incorrect password correctly rejected.")
    else:
        print("❌ Incorrect password was not rejected.")

    # 5. Access Protected Route
    print("\n[5] Testing Authenticated Route (/auth/me)...")
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{API_BASE}/auth/me", headers=headers)
    if r.status_code == 200:
        print(f"✅ /auth/me successful: {r.json()}")
    else:
        print(f"❌ /auth/me failed: {r.text}")

if __name__ == "__main__":
    test_auth_flow()
