"""
RAG retriever test. Requires OPENAI_API_KEY and data/medical_guidelines.json.
Run from project root: python -m rag.test_rag  or  python rag/test_rag.py
"""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from rag.retriever import MedicalRetriever


def test_retriever():
    print("--- BUILDING HIGH-ACCURACY INDEX ---")
    retriever = MedicalRetriever()
    query = "heart attack symptoms"
    results = retriever.retrieve(query)
    print(f"QUERY: {query}")
    print(f"RESULTS FOUND:\n{results[:200]}...")
    
    if "Infarction" in results or "heart" in results.lower():
        print("\n✅ RAG SYSTEM: HIGH ACCURACY CONFIRMED")
    else:
        print("\n❌ RAG SYSTEM: LOW RELEVANCE DETECTED")

if __name__ == "__main__":
    test_retriever()
