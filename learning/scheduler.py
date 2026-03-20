import asyncio
import logging
from datetime import datetime, timedelta
from learning.data_pipeline import data_pipeline
from learning.dataset_builder import dataset_builder
from learning.fine_tuner import fine_tuner
from learning.evaluator import model_evaluator
from learning.safety_layer import safety_validator
from learning.model_registry import model_registry
from learning.deployment import model_deployer

logger = logging.getLogger(__name__)

class LearningScheduler:
    """
    Phase 8: Continuous Learning Scheduler
    Orchestrates the repeated evolution loop:
    Collect -> Build -> Tune -> Evaluate -> Validate -> Register -> Deploy.
    """
    def __init__(self, check_interval_hours: int = 24):
        self.interval = check_interval_hours
        self.running = False

    async def start_autonomous_cycle(self):
        """Runs the complete self-improvement loop."""
        logger.info("Scheduler: Starting Autonomous Learning Cycle...")
        
        # 1. Collect Data (Doctors with high ratings/corrections)
        raw_samples = await data_pipeline.get_high_quality_samples()
        if len(raw_samples) < 5: # Threshold for training
            logger.info("Scheduler: Insufficient high-quality data. Aborting cycle.")
            return
            
        # 2. Build Dataset
        version = datetime.now().strftime("%Y%m%d_%H%M")
        dataset_path = dataset_builder.prepare_fine_tuning_format(raw_samples, version=version)
        
        # 3. Fine-Tune (Option A: LoRA)
        checkpoint = fine_tuner.train_lora_adapter(dataset_path)
        if not checkpoint:
            logger.error("Scheduler: Fine-tuning failed. Aborting.")
            return
            
        # 4. Evaluate
        current_prod = model_registry.get_latest_model()
        results = await model_evaluator.evaluate_candidate(checkpoint, current_prod.get("version"))
        
        # 5. Safety Validation
        is_safe = await safety_validator.validate_checkpoint(checkpoint, raw_samples)
        results["passed_validation"] = is_safe and results.get("passed_validation", True)
        
        # 6. Register
        model_id = f"medagent-v{version}"
        model_registry.register_model(version=version, checkpoint_path=checkpoint, metrics=results)
        
        # 7. Deploy
        deployed = await model_deployer.deploy_if_better(model_id, results)
        
        if deployed:
            logger.info(f"Scheduler: Cycle complete. Successfully evolved to {model_id}")
        else:
            logger.info("Scheduler: Cycle complete. No deployment performed.")

    async def run_forever(self):
        self.running = True
        while self.running:
            await self.start_autonomous_cycle()
            await asyncio.sleep(self.interval * 3600)

# Singleton Instance
learning_scheduler = LearningScheduler()
