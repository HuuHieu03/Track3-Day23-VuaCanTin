from __future__ import annotations

import pytest
from langgraph.graph.state import CompiledStateGraph

from langgraph_agent_lab import nodes
from langgraph_agent_lab.graph import build_graph
from langgraph_agent_lab.state import AgentState, Route, Scenario, initial_state, make_event


def classify_as_error(_: AgentState) -> dict[str, object]:
    return {
        "route": Route.ERROR.value,
        "risk_level": "low",
        "events": [make_event("classify", "completed", "stubbed error classification")],
    }


def deterministic_answer(_: AgentState) -> dict[str, object]:
    return {
        "final_answer": "The transient failure was recovered.",
        "events": [make_event("answer", "completed", "stubbed grounded answer")],
    }


@pytest.fixture
def error_graph(monkeypatch: pytest.MonkeyPatch) -> CompiledStateGraph:
    """Build the real Role 1 graph with only unfinished Role 2 nodes stubbed."""
    monkeypatch.setattr(nodes, "classify_node", classify_as_error)
    monkeypatch.setattr(nodes, "answer_node", deterministic_answer)
    return build_graph()


def test_error_route_recovers_after_two_retry_visits(
    error_graph: CompiledStateGraph,
) -> None:
    scenario = Scenario(
        id="integration-retry",
        query="Timeout failure while processing request",
        expected_route=Route.ERROR,
        max_attempts=3,
    )

    result = error_graph.invoke(initial_state(scenario))
    visited = [event["node"] for event in result["events"]]

    assert result["route"] == Route.ERROR.value
    assert result["attempt"] == 2
    assert result["evaluation_result"] == "success"
    assert result["final_answer"]
    assert visited == [
        "intake",
        "classify",
        "retry",
        "tool",
        "evaluate",
        "retry",
        "tool",
        "evaluate",
        "answer",
        "finalize",
    ]
    assert visited.count("retry") == 2
    assert "dead_letter" not in visited


def test_error_route_reaches_dead_letter_at_retry_limit(
    error_graph: CompiledStateGraph,
) -> None:
    scenario = Scenario(
        id="integration-dead-letter",
        query="System failure cannot recover after multiple attempts",
        expected_route=Route.ERROR,
        max_attempts=1,
    )

    result = error_graph.invoke(initial_state(scenario))
    visited = [event["node"] for event in result["events"]]

    assert result["route"] == Route.ERROR.value
    assert result["attempt"] == 1
    assert result["final_answer"]
    assert visited == ["intake", "classify", "retry", "dead_letter", "finalize"]
    assert "tool" not in visited
