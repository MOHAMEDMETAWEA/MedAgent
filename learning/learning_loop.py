import asyncio
import logging
import time
from learning.rlhf_pipeline import rlhf_pipeline

logger = logging.getLogger(__name__)

class ContinuousLearningWorker:
    """
    Background worker that runs the RLHF learning cycle periodically.
    """
    def __init__(self, interval_seconds: int = 3600): # Default: every hour
        self.interval = interval_seconds
        self.running = False
        self._task = None

    async def start(self):
        if self.running:
            return
        self.running = True
        self._task = asyncio.create_all([self._run_loop()])
        logger.info(f"Continuous Learning Worker started with interval {self.interval}s.")

    async def _run_loop(self):
        while self.running:
            try:
                logger.info("Triggering periodic RLHF learning cycle...")
                report = await rlhf_pipeline.run_learning_cycle()
                logger.info(f"Cycle completed. New training samples found: {report.get('new_training_samples')}")
            except Exception as e:
                logger.error(f"Error in learning cycle loop: {e}")
            
            await asyncio.sleep(self.interval)

    async def stop(self):
        self.running = False
        if self._task:
            # In a real app, we'd cancel the task
            pass
        logger.info("Continuous Learning Worker stopped.")

# Instance
learning_worker = ContinuousLearningWorker()
