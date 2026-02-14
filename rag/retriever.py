"""
Medical RAG Retriever with Configurable Paths and Enhanced Error Handling.
"""
import os
import json
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from config import settings
import logging

logger = logging.getLogger(__name__)

class MedicalRetriever:
    """
    Enhanced Medical Retriever with Recursive Splitting and Error Handling.
    Uses configurable paths for global deployment.
    """
    def __init__(self, data_path=None, index_path=None):
        self.data_path = Path(data_path) if data_path else settings.MEDICAL_GUIDELINES_PATH
        self.index_path = Path(index_path) if index_path else settings.INDEX_DIR
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY
        )
        self.vector_db = None
        self._initialize_db()

    def _initialize_db(self):
        """Initialize the vector database with medical guidelines."""
        # Ensure index directory exists
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Check if index already exists to avoid re-embedding
        index_file = self.index_path / "index.faiss"
        if index_file.exists():
            try:
                # SECURITY: allow_dangerous_deserialization=True is required by FAISS for pickle load.
                # Only load indexes built in a trusted environment. Do not load FAISS index from
                # untrusted sources (risk of arbitrary code execution). See DEPLOYMENT.md.
                self.vector_db = FAISS.load_local(
                    str(self.index_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
                logger.info("Loaded existing FAISS index.")
                return
            except Exception as e:
                logger.warning(f"Error loading index: {e}. Rebuilding...")

        if not self.data_path.exists():
            logger.error(f"Critical Error: {self.data_path} not found. Please run data generator.")
            return

        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                guidelines = json.load(f)

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.RAG_CHUNK_SIZE,
                chunk_overlap=settings.RAG_CHUNK_OVERLAP,
                separators=["\n\n", "\n", ".", " "]
            )

            documents = []
            for item in guidelines:
                content = (
                    f"### MEDICAL PROTOCOL: {item.get('condition', 'Unknown')} ###\n"
                    f"Category: {item.get('category', 'General')}\n"
                    f"Guideline Details: {item.get('guideline', 'N/A')}\n"
                    f"Diagnostic Indicators: {item.get('indicators', 'N/A')}\n"
                    f"First-line Treatment: {item.get('treatment', 'N/A')}\n"
                )
                # Use chunks for better granularity in retrieval
                chunks = text_splitter.split_text(content)
                for chunk in chunks:
                    doc = Document(
                        page_content=chunk, 
                        metadata={
                            "source": "medical_guidelines", 
                            "condition": item.get('condition', 'Unknown')
                        }
                    )
                    documents.append(doc)

            if documents:
                self.vector_db = FAISS.from_documents(documents, self.embeddings)
                self.vector_db.save_local(str(self.index_path))
                logger.info(f"Medical RAG Database initialized with {len(documents)} document chunks.")
            else:
                logger.warning("No documents to index.")
        except Exception as e:
            logger.error(f"Error initializing vector database: {e}")

    def retrieve(self, query, k=None):
        """
        Retrieve context using Similarity Search with Relevance Scoring.
        
        Args:
            query: Search query text
            k: Number of results to retrieve (defaults to config setting)
            
        Returns:
            Retrieved medical context or error message
        """
        if not self.vector_db:
            return "No medical data available. Please ensure the medical guidelines database is initialized."
        
        if not query or len(query.strip()) == 0:
            return "No query provided."
        
        k = k or settings.RAG_TOP_K
        
        try:
            # Using similarity search with score to filter out low-quality matches
            docs_and_scores = self.vector_db.similarity_search_with_relevance_scores(query, k=k)
            
            relevant_docs = [
                doc.page_content 
                for doc, score in docs_and_scores 
                if score > settings.RAG_RELEVANCE_THRESHOLD
            ]
            
            if not relevant_docs:
                return "No matching clinical protocols found for these symptoms. Please consult a healthcare professional."
                
            return "\n\n---\n\n".join(relevant_docs)
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return "Error retrieving medical information. Please try again or consult a healthcare professional."

if __name__ == "__main__":
    pass
