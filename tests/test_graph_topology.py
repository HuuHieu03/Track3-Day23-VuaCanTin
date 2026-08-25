from langgraph_agent_lab.graph import build_graph


def test_graph_contains_expected_nodes() -> None:
    graph_view = build_graph().get_graph()

    assert set(graph_view.nodes) == {
        "__start__",
        "__end__",
        "intake",
        "classify",
        "answer",
        "tool",
        "evaluate",
        "clarify",
        "risky_action",
        "approval",
        "retry",
        "dead_letter",
        "finalize",
    }


def test_graph_contains_required_edges() -> None:
    graph_view = build_graph().get_graph()
    edges = {(edge.source, edge.target) for edge in graph_view.edges}

    assert len(graph_view.edges) == 19
    assert {
        ("__start__", "intake"),
        ("intake", "classify"),
        ("classify", "answer"),
        ("classify", "tool"),
        ("classify", "clarify"),
        ("classify", "risky_action"),
        ("classify", "retry"),
        ("tool", "evaluate"),
        ("evaluate", "answer"),
        ("evaluate", "retry"),
        ("risky_action", "approval"),
        ("approval", "tool"),
        ("approval", "clarify"),
        ("retry", "tool"),
        ("retry", "dead_letter"),
        ("answer", "finalize"),
        ("clarify", "finalize"),
        ("dead_letter", "finalize"),
        ("finalize", "__end__"),
    } <= edges
