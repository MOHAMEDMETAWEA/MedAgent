from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_admin_user
from learning.model_registry import model_registry

router = APIRouter(prefix="/models", tags=["Model Management"])


@router.get("/analytics", response_model=Dict[str, Any])
async def get_model_analytics(current_user: Any = Depends(get_current_admin_user)):
    """
    Returns analytics and performance trends for all registered models.
    Requires Admin privileges.
    """
    try:
        registry_data = model_registry.data

        # Calculate summary stats
        total_models = len(registry_data.get("models", {}))
        current_model_id = registry_data.get("current_model")
        current_metrics = (
            registry_data["models"].get(current_model_id, {}).get("metrics", {})
        )

        return {
            "status": "success",
            "total_models": total_models,
            "current_production_model": current_model_id,
            "current_performance": current_metrics,
            "history": registry_data.get("models", {}),
            "system_status": "Self-learning system active",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve model analytics: {str(e)}"
        )


@router.get("/registry")
async def get_raw_registry(current_user: Any = Depends(get_current_admin_user)):
    return model_registry.data
