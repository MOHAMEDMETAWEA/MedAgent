"""
Cognitive Memory Core Test - Verifies Cases, Graph Memory, and ToT.
"""
import requests
import time

API_BASE = "http://localhost:8000"

def test_cognitive_core():
    print("--- Starting Cognitive Memory Core Test ---")
    
    unique_id = int(time.time())
    username = f"cognitive_user_{unique_id}"
    password = "StrongPass123!"
    
    # 1. Setup User
    requests.post(f"{API_BASE}/auth/register", json={
        "username": username, "email": f"{username}@test.com", "phone": f"111{unique_id}",
        "password": password, "full_name": "Cognitive Test User"
    })
    l_resp = requests.post(f"{API_BASE}/auth/login", json={"login_id": username, "password": password})
    token = l_resp.json()["access_token"]
    user_id = l_resp.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Phase 1: Start a complex case
    print("\n[1] Phase 1: Starting complex case (Respiratory)...")
    payload1 = {
        "symptoms": "I have been coughing for 3 weeks and feel very tired.",
        "patient_id": user_id
    }
    r1 = requests.post(f"{API_BASE}/consult", json=payload1, headers=headers)
    if r1.ok:
        print("✅ First interaction saved and case created.")
        case_id_1 = r1.json().get("conversation_state", {}).get("active_case_id")
        print(f"CASE ID: {case_id_1}")
    else:
        print(f"❌ Phase 1 Failed: {r1.text}")
        return

    # 3. Wait for Graph Update
    time.sleep(1)

    # 4. Phase 2: Follow-up with Memory Reference
    print("\n[2] Phase 2: Follow-up (using ToT and Graph memory)...")
    payload2 = {
        "symptoms": "The cough mentioned before is now bringing up yellow mucus.",
        "patient_id": user_id
    }
    r2 = requests.post(f"{API_BASE}/consult", json=payload2, headers=headers)
    if r2.ok:
        data = r2.json()
        print("✅ Follow-up consultation with Tree-of-Thought completed.")
        diagnosis = data.get("preliminary_diagnosis", "").lower()
        
        # Verify if ToT mentioned anything related to respiratory issues (expected outcome of branches)
        if "mucus" in diagnosis or "respiratory" in diagnosis or "cough" in diagnosis:
            print("✅ SUCCESS: Reasoning aligned with Case and Memory context.")
        else:
            print("❌ WARNING: Reasoning might be generic.")
            print(f"Diagnosis Outcome: {diagnosis[:200]}...")
            
        case_id_2 = data.get("conversation_state", {}).get("active_case_id")
        if case_id_1 == case_id_2:
            print(f"✅ SUCCESS: Consistent Case Tracking maintained ({case_id_1})")
        else:
            print("❌ ERROR: Case ID mismatch. New case started unexpectedly.")
    else:
        print(f"❌ Phase 2 Failed: {r2.text}")

    # 5. Check System Log for Tree-of-Thought status
    print("\n[3] Verifying Cognitive Status...")
    if r2.json().get("status") == "Tree-of-Thought Analysis Complete":
        print("✅ Tree-of-Thought pipeline verified.")
    else:
        print(f"❌ ToT check failed. Status: {r2.json().get('status')}")

if __name__ == "__main__":
    test_cognitive_core()
