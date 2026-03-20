import json
import logging
from typing import List, Dict
from pathlib import Path
from config import settings

logger = logging.getLogger(__name__)

class DatasetFormatter:
    """
    Phase 2: Dataset Builder
    Responsible for converting raw high-quality feedback into fine-tuning formats.
    """
    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir or settings.DATA_DIR) / "training"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def prepare_fine_tuning_format(self, raw_samples: List[Dict], version: str = "v1") -> str:
        """
        Converts raw samples into JSONL format suitable for LoRA/PEFT.
        Returns the path to the generated file.
        """
        if not raw_samples:
            logger.warning("No samples provided for dataset building.")
            return ""

        output_file = self.data_dir / f"medagent_ft_dataset_{version}.jsonl"
        
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                for sample in raw_samples:
                    # Formatting for Hugging Face Instruction tuning
                    formatted_sample = {
                        "input": sample.get("input", ""),
                        "output": sample.get("output", ""),
                        "metadata": {
                            "source_id": sample.get("id"),
                            "type": sample.get("type"),
                            "rating": sample.get("rating")
                        }
                    }
                    f.write(json.dumps(formatted_sample) + "\n")
            
            logger.info(f"Dataset Builder: Successfully created dataset at {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Dataset Builder: Failed to write JSONL: {e}")
            return ""

    def generate_prompt_examples(self, raw_samples: List[Dict]) -> List[str]:
        """
        Creates few-shot prompt examples for API-based model optimization (Option B).
        """
        examples = []
        for sample in raw_samples[:5]: # Take top 5 for few-shot
            ex = f"Symptom Input: {sample.get('input')}\nIdeal Medical Response: {sample.get('output')}\n---\n"
            examples.append(ex)
        return examples

# Singleton Instance
dataset_builder = DatasetFormatter()
