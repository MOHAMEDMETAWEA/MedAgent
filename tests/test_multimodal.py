"""
Multimodal Vision Integration Test - Verifies the image analysis pipeline.
"""
import requests
import os
import time

API_BASE = "http://localhost:8000"

def test_multimodal_flow():
    print("--- Starting Multimodal Integration Test ---")
    
    # 1. Check API Health
    try:
        r = requests.get(f"{API_BASE}/health")
        if r.status_code != 200:
            print("❌ API is not running. Start the backend first.")
            return
    except:
        print("❌ Could not connect to API.")
        return

    # 2. Simulate Image Upload (Using a dummy file if needed, or check if folder works)
    # For testing, we'll just check if the /upload endpoint exists and rejects invalid files
    print("\n[1] Testing Image Upload...")
    try:
        # Create a dummy image file for testing
        test_img = "test_rash.jpg"
        with open(test_img, "wb") as f:
            f.write(b"fake image data")
        
        with open(test_img, "rb") as f:
            files = {"file": (test_img, f, "image/jpeg")}
            u_resp = requests.post(f"{API_BASE}/upload", files=files)
            
        if u_resp.status_code == 200:
            img_path = u_resp.json().get("image_path")
            print(f"✅ Image uploaded successfully: {img_path}")
        else:
            print(f"❌ Upload failed: {u_resp.text}")
            img_path = None
            
        if os.path.exists(test_img):
            os.remove(test_img)
    except Exception as e:
        print(f"❌ Upload error: {e}")
        img_path = None

    # 3. Test Consultation with Image Path
    if img_path:
        print("\n[2] Testing Multimodal Consultation...")
        payload = {
            "symptoms": "I have a red rash on my arm. It is itchy.",
            "patient_id": "test_user_vision",
            "image_path": img_path
        }
        
        try:
            start_time = time.time()
            c_resp = requests.post(f"{API_BASE}/consult", json=payload, timeout=60)
            duration = time.time() - start_time
            
            if c_resp.status_code == 200:
                data = c_resp.json()
                print(f"✅ Consultation complete in {duration:.2f}s")
                print(f"Findings: {data.get('visual_findings', {}).get('status', 'No Status')}")
                if "visual_findings" in data:
                    print(f"Vision Confidence: {data['visual_findings'].get('confidence')}")
            else:
                print(f"❌ Consultation failed: {c_resp.text}")
        except Exception as e:
            print(f"❌ Consultation error: {e}")

    # 4. Check Capabilities API
    print("\n[3] Verifying Capabilities List...")
    try:
        cap_resp = requests.get(f"{API_BASE}/system/capabilities")
        if cap_resp.status_code == 200:
            agents = [a['name'] for a in cap_resp.json().get('agents', [])]
            if "Vision Analysis Agent / عميل تحليل الصور" in agents:
                print("✅ Vision Agent found in system capabilities.")
            else:
                print("❌ Vision Agent missing from capabilities list.")
    except Exception as e:
        print(f"❌ Capabilities error: {e}")

if __name__ == "__main__":
    test_multimodal_flow()
