from langgraph.graph import StateGraph, START, END
from sqlalchemy.orm import Session
from .eval_state import EvalState
from .nodes import generate_node, make_call_chatbot_node, make_judge_node, flag_for_kb_update_node, route_after_judge


def build_eval_graph(db: Session):
    graph = StateGraph(EvalState)

    graph.add_node("generate", generate_node)
    graph.add_node("call_chatbot", make_call_chatbot_node(db))
    graph.add_node("judge", make_judge_node(db))
    graph.add_node("flag_for_kb_update", flag_for_kb_update_node)

    graph.add_edge(START, "generate")
    graph.add_edge("generate", "call_chatbot")
    graph.add_edge("call_chatbot", "judge")

    graph.add_conditional_edges(
        "judge",
        route_after_judge,
        {
            "flag_for_kb_update": "flag_for_kb_update",
            "end": END,
        },
    )
    graph.add_edge("flag_for_kb_update", END)

    return graph.compile()