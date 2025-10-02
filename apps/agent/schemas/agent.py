from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import AIMessage, BaseMessage


class AgentState(TypedDict, total=False):

    input: str
    user_id: str
    start: str
    end: str
    goal: str

    rows: List[Dict[str, Any]]
    kpis: Dict[str, Any]

    answer: str
    __ai_msg__: Optional[AIMessage]
    messages: List[BaseMessage]
