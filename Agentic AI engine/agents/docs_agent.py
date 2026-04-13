import glob
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings


class DocsAgent:
    def __init__(self):
        self.index_dir = settings.DATA_DIR / "docs_faiss_index"
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY, model=settings.EMBEDDING_MODEL
        )
        self.llm = ChatOpenAI(
            temperature=0.1,
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
        )
        self.vectorstore = None
        self._load_vectorstore_if_exists()

    def _load_vectorstore_if_exists(self):
        if self.index_dir.exists():
            try:
                self.vectorstore = FAISS.load_local(
                    str(self.index_dir),
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
            except Exception as e:
                print(f"Failed to load existing index: {e}")

    def build_index(self):
        root_dir = settings.BASE_DIR
        target_dirs = ["agents", "api", "database", "prompts", "utils", "tests"]
        all_docs = []

        for d in target_dirs:
            target_path = root_dir / d
            if not target_path.exists():
                continue

            # Recursive scan for codebase files
            for root, _, files in os.walk(target_path):
                # Skip pycache
                if "__pycache__" in root:
                    continue
                for f in files:
                    ext = Path(f).suffix
                    if ext not in [".py", ".md", ".txt", ".json", ".yaml", ".yml"]:
                        continue

                    file_path = os.path.join(root, f)
                    try:
                        with open(file_path, "r", encoding="utf-8") as file:
                            content = file.read()

                            # Embed security masks strictly
                            if ".env" not in file_path and "API_KEY" not in content:
                                rel_path = os.path.relpath(file_path, root_dir)
                                all_docs.append(
                                    Document(
                                        page_content=content,
                                        metadata={
                                            "source": rel_path.replace("\\", "/"),
                                            "filename": f,
                                        },
                                    )
                                )
                    except Exception:
                        pass  # Ignore encoding issues on binary files

        # Split documents strategically
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=250,
            separators=["\nclass ", "\ndef ", "\n\n", "\n", " ", ""],
        )

        split_docs = text_splitter.split_documents(all_docs)

        if split_docs:
            self.vectorstore = FAISS.from_documents(split_docs, self.embeddings)
            self.index_dir.mkdir(parents=True, exist_ok=True)
            self.vectorstore.save_local(str(self.index_dir))
            return {"status": "success", "indexed_chunks": len(split_docs)}
        else:
            return {"status": "error", "message": "No documents found to index"}

    # --- Core Interactive Methods ---

    def chat(self, query: str) -> dict:
        if not self.vectorstore:
            return {"error": "Index not built. Please run Data Pipeline first."}

        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 6})

        try:
            docs = retriever.invoke(query)
            context = "\n\n".join([doc.page_content for doc in docs])

            full_query = (
                f"You are the MEDAgent Interactive Developer Copilot.\n"
                f"Provide highly technical, accurate answers based exclusively on the provided codebase chunks.\n"
                f"Always structure your answer with:\n"
                f"1. Simple Explanation\n"
                f"2. Technical Explanation\n"
                f"3. Code References\n\n"
                f"Codebase Context:\n{context}\n\n"
                f"Question: {query}"
            )

            res = self.llm.invoke([HumanMessage(content=full_query)])
            answer = getattr(res, "content", str(res))

            # Extract unique sources
            sources = list(set([doc.metadata.get("source", "Unknown") for doc in docs]))

            return {"answer": answer, "sources": sources}
        except Exception as e:
            return {"error": f"LLM Generation Failed: {str(e)}"}

    def explain_file(self, file_path: str) -> dict:
        if not self.vectorstore:
            return {"error": "Index missing."}

        query = f"Provide a complete architectural explanation of the following file: {file_path}. Detail its purpose, flow, and primary dependencies."
        return self.chat(query)

    def debug_error(self, error_trace: str) -> dict:
        if not self.vectorstore:
            return {"error": "Index missing."}

        query = f"Debug this error stack trace in the context of the MEDAgent project:\n\n{error_trace}\n\nIdentify the root cause, suggest the corrected Python code, and mention any related architectural dependencies."
        return self.chat(query)
