"""START -> segregator -> (id_agent | discharge_summary_agent | itemized_bill_agent) -> aggregator -> END"""
from langgraph.graph import END, START, StateGraph

from app.nodes.aggregator import aggregator_node
from app.nodes.bill_agent import itemized_bill_agent_node
from app.nodes.discharge_agent import discharge_agent_node
from app.nodes.id_agent import id_agent_node
from app.nodes.segregator import segregator_node
from app.state import ClaimState

AGENTS = ["id_agent", "discharge_summary_agent", "itemized_bill_agent"]


def build_graph():
    g = StateGraph(ClaimState)
    g.add_node("segregator", segregator_node)
    g.add_node("id_agent", id_agent_node)
    g.add_node("discharge_summary_agent", discharge_agent_node)
    g.add_node("itemized_bill_agent", itemized_bill_agent_node)
    g.add_node("aggregator", aggregator_node)

    g.add_edge(START, "segregator")
    for agent in AGENTS:                 # fan-out: agents run in parallel
        g.add_edge("segregator", agent)
    g.add_edge(AGENTS, "aggregator")     # fan-in: aggregator waits for all three
    g.add_edge("aggregator", END)
    return g.compile()


claim_graph = build_graph()
