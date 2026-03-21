"""
System Health, Metrics, and Admin Controls.
"""

from fastapi import APIRouter, Depends, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from agents.developer_agent import DeveloperControlAgent

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health")
async def health():
    return {"status": "ok", "version": "5.3.0"}


@router.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/admin/health")
async def admin_health():
    agent = DeveloperControlAgent()
    return agent.get_system_health()
