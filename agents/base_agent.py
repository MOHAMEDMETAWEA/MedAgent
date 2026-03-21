"""
Base Agent - Standardized Foundation for all MedAgent AI Components.
Provides consistent logging, performance tracking, and error handling.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"agents.{name.lower()}")
        self._setup_logger()

    def _setup_logger(self):
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    @abstractmethod
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Core logic to be implemented by each specialized agent."""
        pass

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper to provide timing and consistent error handling."""
        start_time = time.perf_counter()
        self.logger.info(f"--- {self.name} started ---")
        try:
            result = self.process(state)
            latency = int((time.perf_counter() - start_time) * 1000)
            self.logger.info(f"--- {self.name} completed in {latency}ms ---")

            # Record latency in state for analytics
            if "latency_log" not in result:
                result["latency_log"] = {}
            result["latency_log"][self.name] = latency

            return result
        except Exception as e:
            self.logger.error(f"Critical error in {self.name}: {str(e)}", exc_info=True)
            state["status"] = "error"
            state["final_response"] = (
                f"An internal error occurred in the {self.name}. Please try again."
            )
            return state
