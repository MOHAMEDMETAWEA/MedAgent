import sys
import time

print("Testing TriageAgent import...")
start = time.time()
try:
    import agents.triage_agent

    print(f"Import successful in {time.time() - start:.2f}s")
except Exception as e:
    print(f"Import failed: {e}")
except KeyboardInterrupt:
    print("\nImport interrupted by user.")
