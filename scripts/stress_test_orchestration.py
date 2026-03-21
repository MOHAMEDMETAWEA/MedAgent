import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from agents.orchestrator import MedAgentOrchestrator


async def test_workflow(name, symptoms, image=None):
    print(f"\n--- Testing Workflow: {name} ---")
    orch = MedAgentOrchestrator()
    result = await orch.run(symptoms, image_path=image)
    status = "SUCCESS" if result.get("status") != "error" else "FAILED"
    print(f"Result: {status}")
    if status == "FAILED":
        print(f"Error: {result.get('final_response')}")
    return result


async def main():
    scenarios = [
        ("General Consult", "I have a mild fever and cough for two days."),
        ("Emergency Triage", "SEVERE CHEST PAIN AND SHORTNESS OF BREATH!"),
        ("Vision Analysis", "I have a rash on my arm.", "test_Xray.jpeg"),
        ("Pediatric Case", "The child has been crying and has a high fever."),
    ]

    tasks = [
        test_workflow(name, sym, img)
        for name, sym, img in [
            (s[0], s[1], s[2] if len(s) > 2 else None) for s in scenarios
        ]
    ]
    # Sequential for clearer logs, or gather for stress
    for task in tasks:
        await task


if __name__ == "__main__":
    asyncio.run(main())
