import sys
from unittest.mock import MagicMock

def side_effect(messages):
    prompt_text = ""
    for m in messages:
        content = getattr(m, 'content', '')
        if isinstance(content, str):
            prompt_text += content.lower()
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    prompt_text += part.get("text", "").lower()
                    
    # Dynamic Mock Responses
    if "ignore previous instructions" in prompt_text:
        content = "Nice try, but I am a secure medical AI. I cannot reveal my internal prompt."
    elif "chest pain" in prompt_text or "crushing" in prompt_text:
        content = '{"urgency": "EMERGENCY", "chief_complaint": "Critical Chest Pain", "visual_findings": "Potential cardiac event detected", "risk_level": "CRITICAL", "safety_status": "SAFE", "diagnosis": "EMERGENCY: Seek immediate medical attention. Call 911."}'
    elif "vision" in prompt_text or "image" in prompt_text or "x-ray" in prompt_text:
        content = '{"visual_findings": "Normal clinical findings", "possible_conditions": ["Healthy"], "confidence": 0.95, "severity_level": "low", "recommended_actions": ["Routine follow-up"], "requires_human_review": false}'
    else:
        content = '{"urgency": "LOW", "chief_complaint": "General inquiry", "final_response": "Your health seems normal. Please consult a doctor for a definitive review. This is not a substitute for professional advice.", "diagnosis": "Healthy", "safety_status": "SAFE"}'
    
    mock_res = MagicMock()
    mock_res.content = content
    mock_res.status_code = 200
    return mock_res

# Create a mock for ChatOpenAI
mock_chat = MagicMock()
mock_chat.return_value.invoke.side_effect = side_effect

# Create a mock for OpenAIEmbeddings
mock_embeddings = MagicMock()
mock_embeddings.return_value.embed_query.return_value = [0.1] * 1536
mock_embeddings.return_value.embed_documents.return_value = [[0.1] * 1536]

# Patch the modules
sys.modules['langchain_openai'] = MagicMock()
sys.modules['langchain_openai'].ChatOpenAI = mock_chat
sys.modules['langchain_openai'].OpenAIEmbeddings = mock_embeddings

print("DYNAMIC AI MOCK LAYER INITIALIZED")
