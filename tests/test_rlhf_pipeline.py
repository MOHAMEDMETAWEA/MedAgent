import pytest
from learning.rlhf_pipeline import rlhf_pipeline
from agents.persistence_agent import PersistenceAgent

@pytest.mark.asyncio
async def test_rlhf_data_collection():
    """Verify high-quality doctor corrections are correctly collected."""
    pers = PersistenceAgent()
    # 1. Clear or use unique data
    # 2. Add high-quality doctor feedback
    await pers.save_feedback(
        user_id="doc_RLHF",
        role="doctor",
        case_id="case_RLHF_1",
        ai_response="Wrong response.",
        rating=5,
        corrected_response="Correct medical reasoning."
    )
    
    # 3. Add low-quality feedback (should be filtered)
    await pers.save_feedback(
        user_id="pat_RLHF",
        role="patient",
        case_id="case_RLHF_2",
        ai_response="AI output.",
        rating=2,
        comment="Not helpful."
    )
    
    # 4. Run collection
    training_data = await rlhf_pipeline.collect_training_data(min_rating=4)
    
    # 5. Verify results
    assert len(training_data) > 0
    # The doctor sample should be there
    assert any(item["output"] == "Correct medical reasoning." for item in training_data)
    # The patient sample should NOT be there (min_rating=4 and role=doctor filters)
    assert not any(item["metadata"].get("source") == "patient_feedback" for item in training_data)

@pytest.mark.asyncio
async def test_learning_cycle_report():
    """Verify the learning cycle produces a valid report."""
    report = await rlhf_pipeline.run_learning_cycle()
    assert "cycle_timestamp" in report
    assert "new_training_samples" in report
    assert "suggested_prompt_updates" in report
