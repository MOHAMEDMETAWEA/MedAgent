"""
High-Load Stress Test for MEDAgent.
Simulates concurrent clinical consultations.
"""
import asyncio
import httpx
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000/api/v1/consult"

async def simulate_consultation(client, user_id, symptoms):
    start_time = time.time()
    try:
        response = await client.post(
            API_URL,
            json={
                "user_id": user_id,
                "symptoms": symptoms,
                "mode": "patient"
            },
            timeout=30.0
        )
        latency = time.time() - start_time
        logger.info(f"User {user_id}: Response received in {latency:.2f}s (Status: {response.status_code})")
        return latency
    except Exception as e:
        logger.error(f"User {user_id}: FAILED. Error: {e}")
        return None

async def run_stress_test(concurrency: int = 10):
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(concurrency):
            tasks.append(simulate_consultation(client, f"stress_user_{i}", "I have persistent fatigue and joint pain."))
        
        print(f"🚀 Launching {concurrency} concurrent clinical consultations...")
        latencies = await asyncio.gather(*tasks)
        
        valid_latencies = [l for l in latencies if l is not None]
        if valid_latencies:
            avg = sum(valid_latencies) / len(valid_latencies)
            print(f"\n✅ STRESS TEST COMPLETE")
            print(f"Average Latency: {avg:.2f}s")
            print(f"Success Rate: {len(valid_latencies)/concurrency * 100}%")

if __name__ == "__main__":
    asyncio.run(run_stress_test(concurrency=20))
