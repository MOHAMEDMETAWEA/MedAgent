import concurrent.futures
import os
import sys
import time

from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.append("d:\\MedAgent")

import tests.ai_mocks
from api.main import app


def run_request(client, i):
    payload = {
        "symptoms": f"Stress test symptoms {i}",
        "patient_id": f"stress_user_{i}",
    }
    start = time.time()
    response = client.post("/consult", json=payload)
    return response.status_code, time.time() - start


def stress_test():
    client = TestClient(app)
    num_requests = 20
    print(f"Starting stress test with {num_requests} requests...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_request, client, i) for i in range(num_requests)]

        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    success_count = sum(1 for status, dur in results if status == 200)
    avg_latency = sum(dur for status, dur in results) / num_requests

    print(f"Stress Test Complete.")
    print(f"Success Rate: {success_count}/{num_requests}")
    print(f"Average Latency: {avg_latency:.4f}s")

    if success_count == num_requests:
        print("RESULT: PASS")
    else:
        print("RESULT: FAIL")


if __name__ == "__main__":
    stress_test()
