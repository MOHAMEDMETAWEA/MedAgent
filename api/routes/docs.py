from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from agents.docs_agent import DocsAgent

router = APIRouter(prefix="/docs", tags=["AI Documentation"])

# Singleton instantiation
_docs_agent = None


def get_docs_agent():
    global _docs_agent
    if _docs_agent is None:
        _docs_agent = DocsAgent()
    return _docs_agent


class ChatRequest(BaseModel):
    query: str


class ExplainRequest(BaseModel):
    file_path: str


class DebugRequest(BaseModel):
    stack_trace: str


@router.post("/build-index")
async def trigger_index_build(background_tasks: BackgroundTasks):
    """Trigger the LangChain parsing pipeline across the codebase."""
    agent = get_docs_agent()
    result = agent.build_index()
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result


@router.post("/chat", response_model=Dict[str, Any])
async def docs_chat(req: ChatRequest):
    """Handle interactive semantic chat."""
    agent = get_docs_agent()
    res = agent.chat(req.query)
    if "error" in res:
        raise HTTPException(status_code=500, detail=res["error"])
    return res


@router.post("/explain", response_model=Dict[str, Any])
async def docs_explain(req: ExplainRequest):
    """Explain a specific referenced file visually via AI."""
    agent = get_docs_agent()
    res = agent.explain_file(req.file_path)
    if "error" in res:
        raise HTTPException(status_code=500, detail=res["error"])
    return res


@router.post("/debug", response_model=Dict[str, Any])
async def docs_debug(req: DebugRequest):
    """Diagnose and root-cause stack traces based on codebase context."""
    agent = get_docs_agent()
    res = agent.debug_error(req.stack_trace)
    if "error" in res:
        raise HTTPException(status_code=500, detail=res["error"])
    return res


@router.get("/files")
async def list_indexed_files():
    """Returns a list of all indexable files for the UI File Explorer."""
    import os

    from config import settings

    root_dir = settings.BASE_DIR
    target_dirs = ["agents", "api", "database", "prompts", "utils", "tests"]
    file_list = []

    for d in target_dirs:
        target_path = root_dir / d
        if not target_path.exists():
            continue
        for root, _, files in os.walk(target_path):
            if "__pycache__" in root:
                continue
            for f in files:
                ext = os.path.splitext(f)[1]
                if ext in [".py", ".md", ".txt", ".json", ".yaml", ".yml"]:
                    rel_path = os.path.relpath(os.path.join(root, f), root_dir)
                    file_list.append(rel_path.replace("\\", "/"))

    return {"files": sorted(file_list)}
