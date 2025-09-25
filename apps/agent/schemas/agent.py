from typing import Any, Dict, List, TypedDict


class AgentState(TypedDict, total=False):

    input: str
    user_id: str
    start: str
    end: str
    goal: str
    rows: List[Dict[str, Any]]
    kpis: Dict[str, Any]
    answer: str
