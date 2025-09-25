from typing import Any, Dict, Optional

from pydantic import BaseModel


class SummaryRequest(BaseModel):

    user_id: str
    start: str
    end: str
    goal: Optional[str] = None
    question: str = "Resumen del periodo"


class SummaryResponse(BaseModel):

    answer: str
    evidence: Optional[Dict[str, Any]] = None
    sources: Optional[list] = None
    usage: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
