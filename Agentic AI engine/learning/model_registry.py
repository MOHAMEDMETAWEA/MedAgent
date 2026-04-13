import datetime
import json
import logging
import os
from typing import Any, Dict, List, Optional

from config import settings

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Phase 6: Model Registry
    Responsible for tracking model versions, metrics, and deployment status.
    """

    def __init__(self):
        self.registry_path = os.path.join(settings.DATA_DIR, "models", "registry.json")
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        self._load_registry()

    def _load_registry(self):
        if os.path.exists(self.registry_path):
            with open(self.registry_path, "r") as f:
                self.data = json.load(f)
        else:
            self.data = {
                "current_model": "base",
                "models": {
                    "base": {
                        "version": "1.0.0",
                        "metrics": {"accuracy_proxy": 0.85},
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "deployment_status": "production",
                    }
                },
            }
            self._save_registry()

    def _save_registry(self):
        with open(self.registry_path, "w") as f:
            json.dump(self.data, f, indent=2)

    def register_model(
        self, version: str, checkpoint_path: str, metrics: Dict[str, Any]
    ):
        """Registers a new model version in the registry."""
        model_id = f"medagent-v{version}"
        self.data["models"][model_id] = {
            "version": version,
            "checkpoint_path": checkpoint_path,
            "metrics": metrics,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "deployment_status": "registered",
        }
        self._save_registry()
        logger.info(f"Registry: Registered new model {model_id} at {checkpoint_path}")

    def promote_to_production(self, model_id: str):
        """Swaps the current production model with a new one."""
        if model_id not in self.data["models"]:
            logger.error(f"Registry: Model {model_id} not found in registry.")
            return

        # Update old production model
        old_prod = self.data["current_model"]
        if old_prod in self.data["models"]:
            self.data["models"][old_prod]["deployment_status"] = "stale"

        self.data["current_model"] = model_id
        self.data["models"][model_id]["deployment_status"] = "production"
        self._save_registry()
        logger.info(f"Registry: PROMOTED {model_id} to production.")

    def get_latest_model(self) -> Dict[str, Any]:
        """Returns the current production model info."""
        current_id = self.data.get("current_model", "base")
        return self.data["models"].get(current_id, self.data["models"]["base"])

    def get_fallback_model(self) -> Dict[str, Any]:
        """Provides a secondary/backup model if the primary fails."""
        # Simple logic: pick the first model that isn't the current production one
        # In a real system, this would favor lower-latency or local models
        current_id = self.data.get("current_model", "base")
        for model_id, info in self.data["models"].items():
            if model_id != current_id:
                return info
        return self.data["models"]["base"]


# Singleton Instance
model_registry = ModelRegistry()
