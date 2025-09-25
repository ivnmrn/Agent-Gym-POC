from __future__ import annotations

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from apps.agent.llm.factory import _make_llm
from apps.agent.llm.tools import fetch_stats, compute_kpis, compute_conclusions
from apps.agent.schemas.agent import AgentState


def node_fetch_rows(state: AgentState) -> AgentState:
    """Call to the API to fetch rows, writes them in state.

    Args:
        state (AgentState): Current state with 'user_id', 'start', and 'end
    Returns:
        AgentState: Updated state with 'rows'.
    """
    rows = fetch_stats.invoke({
        "user_id": state["user_id"],
        "start": state["start"],
        "end": state["end"],
    })
    return {"rows": rows}


def node_calc_kpis(state: AgentState) -> AgentState:
    """Calculate kpis from rows and writes in state.

    Args:
        state (AgentState): Current state with 'rows'.
    Returns:
        AgentState: Updated state with 'kpis'.
    """
    kpis = compute_kpis.invoke({"rows": state["rows"]})
    return {"kpis": kpis}


def node_conclude(state: AgentState) -> AgentState:
    """Generate conclusions based on KPIs and goal, writes answer in state.

    Args:
        state (AgentState): Current state with 'kpis' and optional 'goal'.
    Returns:
        AgentState: Updated state with 'answer'.
    """

    # Use the conclusions tool
    concl = compute_conclusions.invoke({
        "kpis": state["kpis"],
        "goal": state.get("goal", "general")
    })
    answer_text = concl.get("advice", "Sin conclusiones.")

    # Optionally, refine with LLM for better formatting
    llm = _make_llm()
    if llm is not None:
        prompt = (
            "Eres un analista de entrenamiento. Con base en estos KPIs, "
            "responde en 5 bullets claros y accionables. No inventes datos.\n\n"
            f"OBJETIVO: {state.get('goal')}\n\nKPIS:\n{state['kpis']}\n\n"
        )
        answer_text = llm.invoke(prompt).content

    return {"answer": answer_text}


def build_agent_graph():
    """Builds and compiles the agent's state graph."""
    g = StateGraph(AgentState)

    # Graph nodes
    g.add_node("fetch_rows", node_fetch_rows)
    g.add_node("calc_kpis", node_calc_kpis)
    g.add_node("conclude", node_conclude)

    g.add_edge(START, "fetch_rows")
    g.add_edge("fetch_rows", "calc_kpis")
    g.add_edge("calc_kpis", "conclude")
    g.add_edge("conclude", END)

    # Checkpointing with memory saver to retain state across executions
    memory = MemorySaver()
    return g.compile(checkpointer=memory)
