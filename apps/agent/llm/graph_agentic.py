from __future__ import annotations

import json
import logging

from apps.agent.core.config import settings
from apps.agent.llm.constants import (
    CONTENT_ERROR_KPIS_REQUIRE_ROWS,
    CONTENT_ERROR_KPIS_REQUIRED,
    SYSTEM_PROMPT,
)
from apps.agent.llm.factory import _make_llm
from apps.agent.llm.prompt import retrieve_prompt
from apps.agent.llm.tools_registry import TOOLS
from apps.agent.schemas.agent import AgentState
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

logger = logging.getLogger(__name__)


def _ensure_messages(state: AgentState) -> list:
    """Ensure the state has a messages list, initializing if necessary.

    Args:
        state (AgentState): The current state of the agent.
    Returns:
        list: List of BaseMessage objects.
    """

    messages = state.get("messages") or []
    prompt = retrieve_prompt(settings.AGENT_GYM_PROMPT_NAME)
    if not prompt:
        logger.info(
            "retrieve_prompt failed for AGENT_GYM_PROMPT_NAME=%s", settings.AGENT_GYM_PROMPT_NAME
        )
        prompt = SYSTEM_PROMPT

    if not messages:
        user_text = (
            f"Pregunta: {state.get('input','')}\n"
            f"Usuario={state.get('user_id')}, "
            f"rango={state.get('start')}..{state.get('end')}, "
            f"objetivo={state.get('goal')}\n"
            f"Estado: rows={bool(state.get('rows'))}, kpis={bool(state.get('kpis'))}"
        )
        messages = [SystemMessage(content=prompt), HumanMessage(content=user_text)]
    return messages


def node_llm(state: AgentState) -> dict:
    """Node that invokes the LLM with the current messages and tools.

    Args:
        state (AgentState): The current state of the agent.
    Returns:
        dict: Updated state with new messages and possibly an answer.
    """

    messages = _ensure_messages(state)
    llm = _make_llm().bind_tools(list(TOOLS.values()))
    ai_message = llm.invoke(messages)
    out = {"messages": messages + [ai_message]}
    if not getattr(ai_message, "tool_calls", None) and ai_message.content:
        out["answer"] = ai_message.content
    return out


def node_tools(state: AgentState) -> dict:
    """Node that processes tool calls from the last AI message.

    Args:
        state (AgentState): The current state of the agent.
    Returns:
        dict: Updated state with tool results and messages.
    """

    messages = state["messages"]
    last_ai_message = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)
    if last_ai_message is None or not getattr(last_ai_message, "tool_calls", None):
        return {"messages": messages}

    tool_messages = []
    rows_update, kpis_update, answer_update = None, None, None

    for call in last_ai_message.tool_calls:
        call_id = call.get("id")

        name = call.get("name")
        if name == "compute_kpis" and not state.get("rows"):
            tool_messages.append(
                ToolMessage(content=CONTENT_ERROR_KPIS_REQUIRE_ROWS, tool_call_id=call_id)
            )
            continue
        if name == "compute_conclusions" and not state.get("kpis"):
            tool_messages.append(
                ToolMessage(content=CONTENT_ERROR_KPIS_REQUIRED, tool_call_id=call_id)
            )
            continue

        function_tool = TOOLS.get(name)
        args = call.get("args") or call.get("arguments") or {}
        try:
            result = (
                function_tool.invoke(args)
                if hasattr(function_tool, "invoke")
                else function_tool(**args)
            )
        except Exception as e:
            tool_messages.append(
                ToolMessage(content=f"ERROR: {type(e).__name__}: {e}", tool_call_id=call_id)
            )
            continue

        if name == "fetch_stats":
            rows_update = result
            obs = json.dumps({"rows_preview_count": min(5, len(result)), "count": len(result)})
        elif name == "compute_kpis":
            kpis_update = result
            obs = json.dumps({"kpis": result})
        elif name == "compute_conclusions":
            answer_update = (result or {}).get("advice", "") or "ok"
            obs = answer_update
        else:
            obs = json.dumps({"result": result})

        tool_messages.append(ToolMessage(content=obs, tool_call_id=call_id))

    out = {"messages": messages + tool_messages}
    if rows_update is not None:
        out["rows"] = rows_update
    if kpis_update is not None:
        out["kpis"] = kpis_update
    if answer_update is not None:
        out["answer"] = answer_update
    return out


def select_flow(state: AgentState) -> str:
    """Decide if we should call a tool, continue with LLM, or end the flow.

    Args:
        state (AgentState): The current state of the agent.
    Returns:
        str: "to_tools", "to_llm", or "to_end"
    """

    base_message = state.get("messages") or []
    last_ai_message = next(
        (message for message in reversed(base_message) if isinstance(message, AIMessage)), None
    )

    if last_ai_message and getattr(last_ai_message, "tool_calls", None):
        return "to_tools"
    if state.get("answer"):
        return "to_end"

    return "to_llm"


def build_agentic_graph() -> StateGraph:
    """Builds an agentic graph with LLM and tools."""

    g = StateGraph(AgentState)
    g.add_node("llm", node_llm)
    g.add_node("tools", node_tools)

    g.add_edge(START, "llm")
    g.add_conditional_edges(
        "llm",
        select_flow,
        {"to_tools": "tools", "to_llm": "llm", "to_end": END},
    )

    g.add_edge("tools", "llm")
    return g.compile(checkpointer=MemorySaver())
