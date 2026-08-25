from langgraph_agent_lab.scenarios import load_scenarios
from langgraph_agent_lab.state import Route, Scenario, initial_state


def test_scenario_validation() -> None:
    scenario = Scenario(id="x", query="hello", expected_route=Route.SIMPLE)
    state = initial_state(scenario)
    assert state["thread_id"] == "thread-x"
    assert state["attempt"] == 0
    assert state["events"] == []


def test_initial_state_has_required_fields() -> None:
    """Verify initial_state includes all fields needed by the graph."""
    scenario = Scenario(id="test", query="test query", expected_route=Route.SIMPLE)
    state = initial_state(scenario)
    assert "query" in state
    assert "route" in state
    assert "attempt" in state
    assert "max_attempts" in state
    assert "messages" in state
    assert "tool_results" in state
    assert "errors" in state
    assert "events" in state


def test_load_scenarios() -> None:
    scenarios = load_scenarios("data/sample/scenarios.jsonl")
    assert len(scenarios) >= 6
    assert {item.expected_route for item in scenarios} >= {Route.SIMPLE, Route.TOOL, Route.RISKY}


def test_custom_scenarios_cover_intent_priority() -> None:
    scenarios = load_scenarios("data/sample/scenarios.jsonl")
    by_id = {scenario.id: scenario for scenario in scenarios}

    assert len(by_id) == len(scenarios)

    tool_over_error = by_id["S08_custom"]
    assert tool_over_error.expected_route is Route.TOOL
    assert tool_over_error.should_retry is False
    assert {"tool", "error", "priority"} <= set(tool_over_error.tags)

    risky_over_tool = by_id["S09_complex"]
    assert risky_over_tool.expected_route is Route.RISKY
    assert risky_over_tool.requires_approval is True
    assert {"risky", "tool", "priority"} <= set(risky_over_tool.tags)
