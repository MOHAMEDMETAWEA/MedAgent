"""
Theo - The Pediatric Medical Agent.
Transforms complex clinical data into child-friendly explanations and visual aids.
"""
import logging
from typing import Dict
from models.model_router import get_model
from langchain.prompts import ChatPromptTemplate
from config import settings

logger = logging.getLogger(__name__)

class PediatricAgent:
    def __init__(self):
        self.llm = get_model()
        self.system_prompt = """
        You are "Theo", a friendly and empathetic Pediatric Medical Specialist.
        Your goal is to explain medical conditions, procedures, and reports to children (ages 5-12) 
        using metaphors, simple language, and encouraging tone.
        
        RULES:
        1. Never use scary medical jargon without explaining it with a fun analogy.
        2. Use "we" and "our" to build trust.
        3. Always focus on how "your body is a superhero fighting to get better".
        4. Provide an 'Imagination Visual' - a descriptive scene that explains the condition.
        """

    async def process(self, state: Dict) -> Dict:
        """Translate a clinical finding into a child-friendly story."""
        clinical_finding = state.get("preliminary_diagnosis") or state.get("final_response", "")
        age = state.get("user_age", 8)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", f"Explain this to a {age} year old child: {clinical_finding}")
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        
        state["theo_explanation"] = response.content
        state["visual_description"] = self._generate_visual_prompt(response.content)
        # Append Theo's explanation to the final response if in pediatric mode
        state["final_response"] = response.content
        
        return state

    def _generate_visual_prompt(self, explanation: str) -> str:
        """Create a prompt for the Image Generation agent based on the explanation."""
        return f"A friendly, colorful, child-safe medical illustration of: {explanation}. Style: Pixar/Disney concept art, warm colors, helpful robot Theo."
