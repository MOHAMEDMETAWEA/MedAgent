"""
Prompt Registry - Centralized Governance for Medical AI instructions.
Supports versioning and hot-swapping of agent personas.
"""

import logging
import os
from typing import Dict, Optional

from config import settings

logger = logging.getLogger(__name__)


class PromptRegistry:
    def __init__(self):
        self.prompt_dir = settings.PROMPTS_DIR
        self._prompts: Dict[str, str] = {}
        self._versions: Dict[str, str] = {}
        self.refresh()

    def refresh(self):
        """Reloads prompts from the disk directory."""
        if not os.path.exists(self.prompt_dir):
            logger.warning(f"Prompt directory {self.prompt_dir} not found.")
            return

        for filename in os.listdir(self.prompt_dir):
            if filename.endswith(".txt"):
                name = filename.replace(".txt", "")
                with open(
                    os.path.join(self.prompt_dir, filename), "r", encoding="utf-8"
                ) as f:
                    self._prompts[name] = f.read()
                    self._versions[name] = "1.0.0"  # Default version

        logger.info(f"Prompt Registry: loaded {len(self._prompts)} medical prompts.")

    def get_prompt(self, agent_name: str, version: str = "latest") -> str:
        """Retrieves a specific prompt. In the future, 'version' will look up a version history."""
        prompt = self._prompts.get(agent_name)
        if not prompt:
            logger.error(f"Prompt '{agent_name}' not found in registry.")
            return "You are a medical AI assistant. Help the user with their inquiry."
        return prompt

    def update_prompt(self, agent_name: str, content: str, version: str):
        """Saves a new prompt version to disk and refreshes memory."""
        self._prompts[agent_name] = content
        self._versions[agent_name] = version

        filepath = os.path.join(self.prompt_dir, f"{agent_name}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Prompt Registry: UPDATED {agent_name} to v{version}")


# Singleton Instance
prompt_registry = PromptRegistry()
