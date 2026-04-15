"""
Builder du graphe LangGraph.

Construit le graphe avec les 6 noeuds et les aretes fixes/conditionnelles.
"""

from langgraph.graph import StateGraph, END

from models.interview_state import InterviewState
from nodes.initialization import initialization_node
from nodes.question_generation import generation_question_node
from nodes.candidate_presentation import presentation_candidate_node
from nodes.response_analysis import response_analysis_node
from nodes.decision_node import decision_node
from nodes.final_evaluation import final_evaluation_node


def build_interview_graph():
    """Construit puis compile le graphe LangGraph complet."""
    graph_builder = StateGraph(InterviewState)

    graph_builder.add_node("initialization", initialization_node)
    graph_builder.add_node("generation_question", generation_question_node)
    graph_builder.add_node("presentation_candidate", presentation_candidate_node)
    graph_builder.add_node("response_analysis", response_analysis_node)
    graph_builder.add_node("decision", decision_node)
    graph_builder.add_node("final_evaluation", final_evaluation_node)

    graph_builder.set_entry_point("initialization")

    graph_builder.add_edge("initialization", "generation_question")
    graph_builder.add_edge("generation_question", "presentation_candidate")
    graph_builder.add_edge("presentation_candidate", "response_analysis")
    graph_builder.add_edge("response_analysis", "decision")
    graph_builder.add_edge("final_evaluation", END)

    def routing_function(state: InterviewState):
        return "final_evaluation" if state["signal_arret"] else "generation_question"

    graph_builder.add_conditional_edges(
        "decision",
        routing_function,
        {
            "final_evaluation": "final_evaluation",
            "generation_question": "generation_question",
        },
    )

    graph = graph_builder.compile()
    print("Graphe LangGraph compile avec succes.")
    return graph
