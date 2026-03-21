from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_current_user, oauth2_scheme

router = APIRouter(prefix="/pediatric", tags=["Pediatric"])


class ExplainRequest(BaseModel):
    clinical_finding: str
    age: int = 8


@router.post("/explain")
async def pediatric_explain(req: ExplainRequest, token: str = Depends(oauth2_scheme)):
    """Translate clinical results into Theo's child-friendly explanation."""
    from agents.pediatric_agent import PediatricAgent

    agent = PediatricAgent()
    return await agent.process_explanation(req.clinical_finding, req.age)


@router.post("/visualize")
async def pediatric_visualize(prompt: str, token: str = Depends(oauth2_scheme)):
    """Generate a Theo-style visual aid for the child."""
    # Placeholder for DALL-E/StableDiffusion integration
    return {"visual_prompt": prompt, "status": "Ready for generation"}
