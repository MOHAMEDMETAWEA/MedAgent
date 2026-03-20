import os
import json
import logging
from typing import Dict, Optional
from agents.prompts.registry import PROMPT_REGISTRY, PromptEntry

logger = logging.getLogger(__name__)

class DynamicPromptManager:
    """
    Manages dynamic overrides for clinical prompts based on RLHF learnings.
    Allows hot-swapping prompts without restarting the server.
    """
    def __init__(self, override_dir: str = "agents/prompts/overrides"):
        self.override_dir = override_dir
        self.overrides: Dict[str, str] = {}
        self._ensure_dir()
        self.load_overrides()

    def _ensure_dir(self):
        if not os.path.exists(self.override_dir):
            os.makedirs(self.override_dir)

    def load_overrides(self):
        """Load all .json overrides from the override directory."""
        self.overrides = {}
        for filename in os.listdir(self.override_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.override_dir, filename), 'r') as f:
                        data = json.load(f)
                        self.overrides.update(data)
                except Exception as e:
                    logger.error(f"Failed to load prompt override {filename}: {e}")
        logger.info(f"Loaded {len(self.overrides)} dynamic prompt overrides.")

    def get_prompt(self, prompt_id: str) -> Optional[str]:
        """Get the latest version of a prompt, preferring overrides."""
        # 1. Check for dynamic override
        if prompt_id in self.overrides:
            return self.overrides[prompt_id]
        
        # 2. Fallback to standard registry
        entry = PROMPT_REGISTRY.get(prompt_id)
        return entry.content if entry else None

    def save_override(self, prompt_id: str, new_content: str):
        """Save a new prompt version to overrides (Triggered by RLHF Pipeline)."""
        self.overrides[prompt_id] = new_content
        override_file = os.path.join(self.override_dir, "rlhf_improvements.json")
        
        # Load existing, update, and save
        data = {}
        if os.path.exists(override_file):
            with open(override_file, 'r') as f:
                data = json.load(f)
        
        data[prompt_id] = new_content
        with open(override_file, 'w') as f:
            json.dump(data, f, indent=4)
        
        logger.info(f"Saved prompt override for {prompt_id}.")

# Singleton
dynamic_prompts = DynamicPromptManager()
