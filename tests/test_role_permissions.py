import pytest
from agents.feedback_safety_layer import feedback_safety

@pytest.mark.asyncio
async def test_doctor_authority_validation():
    """Test that doctor authority is correctly validated."""
    doc_user = {"sub": "doc_123", "role": "doctor"}
    pat_user = {"sub": "pat_456", "role": "patient"}
    
    # In safety_layer.py, we have:
    # is_verified = await self.verifier.verify_doctor(user.get("sub"), "SIMULATED_CREDENTIAL")
    
    # For doctors
    is_doc_valid = await feedback_safety.validate_doctor_authority(doc_user)
    assert is_doc_valid is True # VerificationAgent currently returns True for simulated
    
    # For patients
    is_pat_valid = await feedback_safety.validate_doctor_authority(pat_user)
    assert is_pat_valid is False

def test_feedback_safety_heuristics():
    """Test feedback safety heuristics (rating/length)."""
    # Valid
    assert feedback_safety.check_feedback_safety(5, "Great job") is True
    assert feedback_safety.check_feedback_safety(0, "") is True
    
    # Invalid rating
    assert feedback_safety.check_feedback_safety(6, "Bad") is False
    assert feedback_safety.check_feedback_safety(-1, "Bad") is False
    
    # Invalid length
    long_comment = "a" * 10000
    assert feedback_safety.check_feedback_safety(3, long_comment) is False
