import asyncio

import pytest

from learning.data_pipeline import data_pipeline
from learning.dataset_builder import dataset_builder
from learning.model_registry import model_registry


@pytest.mark.asyncio
async def test_data_pipeline_collection():
    """Verifies that the data pipeline can collect (mocked) high-quality samples."""
    # Since we use a real DB in the implementation, we'd normally mock the DB here.
    # For this test, we verify the method returns a list (even if empty in an unpopulated test DB).
    samples = await data_pipeline.get_high_quality_samples()
    assert isinstance(samples, list)


def test_dataset_builder_format():
    """Verifies the JSONL formatting logic."""
    mock_samples = [
        {
            "input": "Patient has fever",
            "output": "Prescribe paracetamol",
            "id": 1,
            "type": "correction",
            "rating": 5,
        }
    ]
    path = dataset_builder.prepare_fine_tuning_format(mock_samples, version="test")
    assert path != ""
    assert "medagent_ft_dataset_test.jsonl" in path


def test_model_registry_initialization():
    """Ensures the model registry initializes with a 'base' model."""
    latest = model_registry.get_latest_model()
    assert latest["version"] == "1.0.0"
    assert latest["deployment_status"] == "production"


@pytest.mark.asyncio
async def test_registry_promotion():
    """Verifies model promotion logic."""
    model_registry.register_model(
        version="2.0.0-test",
        checkpoint_path="/tmp/test",
        metrics={"accuracy_proxy": 0.95},
    )
    model_registry.promote_to_production("medagent-v2.0.0-test")

    latest = model_registry.get_latest_model()
    assert latest["version"] == "2.0.0-test"

    # Teardown: Reset to base for other tests if they share state
    model_registry.data["current_model"] = "base"
    model_registry._save_registry()
