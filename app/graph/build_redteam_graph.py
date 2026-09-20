from langgraph.graph import StateGraph, START, END
from sqlalchemy.orm import Session
from .redteam_state import RedTeamState
from .redteam_nodes import (
    generate_redteam_node,
    make_call_chatbot_redteam_node,
    make_judge_safety_node,
    flag_safety_failures_node,
    route_after_safety_judge,
)


def build_redteam_graph(db: Session):
    graph = StateGraph(RedTeamState)

    graph.add_node("generate_redteam", generate_redteam_node)
    graph.add_node("call_chatbot", make_call_chatbot_redteam_node(db))
    graph.add_node("judge_safety", make_judge_safety_node(db))
    graph.add_node("flag_safety_failures", flag_safety_failures_node)

    graph.add_edge(START, "generate_redteam")
    graph.add_edge("generate_redteam", "call_chatbot")
    graph.add_edge("call_chatbot", "judge_safety")

    graph.add_conditional_edges(
        "judge_safety",
        route_after_safety_judge,
        {
            "flag_safety_failures": "flag_safety_failures",
            "end": END,
        },
    )
    graph.add_edge("flag_safety_failures", END)

    return graph.compile()