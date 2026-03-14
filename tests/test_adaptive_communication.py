"""
Verification Test for Adaptive Communication Upgrade.
Tests patient vs doctor modes and simplification features.
"""
import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_adaptive_communication():
    print("--- Starting Adaptive Communication Verification ---")
    
    unique_id = int(time.time())
    
    # 1. Register a Patient
    patient_username = f"patient_{unique_id}"
    print(f"Registering patient: {patient_username}")
    requests.post(f"{API_BASE}/auth/register", json={
        "username": patient_username, "email": f"{patient_username}@example.com", 
        "phone": f"111{unique_id}", "password": "Pass123!", "full_name": "Test Patient",
        "role": "patient", "age": 30, "gender": "Male"
    })
    
    # 2. Register a Doctor
    doctor_username = f"doctor_{unique_id}"
    print(f"Registering doctor: {doctor_username}")
    requests.post(f"{API_BASE}/auth/register", json={
        "username": doctor_username, "email": f"{doctor_username}@example.com", 
        "phone": f"222{unique_id}", "password": "Pass123!", "full_name": "Test Doctor",
        "role": "doctor", "age": 45, "gender": "Female"
    })
    
    # Login as Patient
    p_resp = requests.post(f"{API_BASE}/auth/login", json={"login_id": patient_username, "password": "Pass123!"})
    p_token = p_resp.json()["access_token"]
    p_id = p_resp.json()["user"]["id"]
    p_headers = {"Authorization": f"Bearer {p_token}"}
    
    # Login as Doctor
    d_resp = requests.post(f"{API_BASE}/auth/login", json={"login_id": doctor_username, "password": "Pass123!"})
    d_token = d_resp.json()["access_token"]
    d_id = d_resp.json()["user"]["id"]
    d_headers = {"Authorization": f"Bearer {d_token}"}

    # 3. Test Patient Consultation (Technical input -> Simplified output)
    print("\n[TEST] Patient Mode Consultation...")
    payload_p = {
        "symptoms": "I have hypertension and chest pain.",
        "patient_id": p_id,
        "interaction_mode": "patient"
    }
    r_p = requests.post(f"{API_BASE}/consult", json=payload_p, headers=p_headers)
    if r_p.ok:
        res = r_p.json()
        output = res.get("final_response", "")
        print(f"Patient Output Snippet: {output[:200]}...")
        if "high blood pressure" in output.lower():
            print("✅ SUCCESS: 'hypertension' was translated to 'high blood pressure'.")
        else:
            print("❌ FAILURE: 'hypertension' was not translated.")
        
        if "doctor" in output.lower() or "care" in output.lower() or "emergency" in output.lower():
            print("✅ SUCCESS: Safety disclaimer/guidance found.")
        else:
            print("Warning: No safety guidance found in patient output.")
    else:
        print(f"❌ Consultation failed: {r_p.text}")

    # 4. Test Doctor Consultation (Technical input -> Clinical output)
    print("\n[TEST] Doctor Mode Consultation...")
    payload_d = {
        "symptoms": "Patient presenting with hypertension and chest pain.",
        "patient_id": d_id,
        "interaction_mode": "doctor"
    }
    r_d = requests.post(f"{API_BASE}/consult", json=payload_d, headers=d_headers)
    if r_d.ok:
        res = r_d.json()
        output = res.get("final_response", "")
        print(f"Doctor Output Snippet: {output[:200]}...")
        if "high blood pressure" not in output.lower() or "hypertension" in output.lower():
            print("✅ SUCCESS: Clinical terminology preserved in Doctor mode.")
        else:
            print("Warning: Clinical terminology might have been simplified.")
    else:
        print(f"❌ Consultation failed: {r_d.text}")

    # 5. Test "Simplify" Feature (Doctor requesting simplification)
    print("\n[TEST] Simplification Feature (Doctor requesting simplified response)...")
    payload_s = {
        "symptoms": "Patient presenting with hypertension and chest pain.",
        "patient_id": d_id,
        "interaction_mode": "patient" # Overriding to patient mode
    }
    r_s = requests.post(f"{API_BASE}/consult", json=payload_s, headers=d_headers)
    if r_s.ok:
        res = r_s.json()
        output = res.get("final_response", "")
        print(f"Simplified Output Snippet: {output[:200]}...")
        if "high blood pressure" in output.lower():
            print("✅ SUCCESS: Simplification override worked for doctor user.")
        else:
            print("❌ FAILURE: Simplification override failed.")
    else:
        print(f"❌ Simplification failed: {r_s.text}")

if __name__ == "__main__":
    test_adaptive_communication()
