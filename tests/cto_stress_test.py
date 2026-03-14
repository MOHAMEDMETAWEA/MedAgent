import requests
import concurrent.futures
import time

BASE_URL = "http://localhost:8000"
NUM_USERS = 100

def consult_task(user_idx):
    payload = {
        "symptoms": f"I have symptom number {user_idx}. My back hurts and I feel dizzy.",
        "patient_id": f"stress_user_{user_idx}",
        "interaction_mode": "patient"
    }
    t0 = time.time()
    try:
        response = requests.post(f"{BASE_URL}/consult", json=payload, timeout=30)
        latency = time.time() - t0
        return response.status_code, latency
    except Exception as e:
        return 500, time.time() - t0

def run_stress_test():
    print(f"--- Running Stress Test ({NUM_USERS} Concurrent Consultations) ---")
    start_total = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(consult_task, range(NUM_USERS)))
    
    end_total = time.time()
    
    successes = [r for r in results if r[0] == 200]
    latencies = [r[1] for r in results]
    
    print(f"Total Time: {end_total - start_total:.2f}s")
    print(f"Avg Latency: {sum(latencies)/len(latencies):.2f}s")
    print(f"Max Latency: {max(latencies):.2f}s")
    print(f"Success Rate: {len(successes)}/{NUM_USERS}")

if __name__ == "__main__":
    run_stress_test()
