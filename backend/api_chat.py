"""
API routes for chat and recommendations.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from .recommendations import get_recommendations

router = APIRouter()


class RecsReq(BaseModel):
    region: str
    current_chi: float
    prev_chi: Optional[float] = None
    topics: Optional[list[str]] = None
    kpi: Optional[dict] = None
    time: Optional[str] = None


@router.post("/recommendations")
def recommendations(req: RecsReq):
    """
    Generate AI recommendations for an alert/incident.
    Returns GROQ-generated recommendations with fallback.
    """
    context = {
        "region": req.region,
        "current_chi": req.current_chi,
        "prev_chi": req.prev_chi,
        "topics": req.topics or [],
        "kpi": req.kpi or {},
        "time": req.time
    }
    text, source = get_recommendations(context)
    return {"recommendations": text, "source": source}

