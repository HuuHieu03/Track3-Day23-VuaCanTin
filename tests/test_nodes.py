"""Tests for the safety / HITL nodes: risky_action_node and approval_node.

These are pure functions (state in, partial-state-update dict out), so they're
tested directly without building the full graph.
"""

from langgraph_agent_lab.nodes import approval_node, risky_action_node


def test_risky_action_node_describes_the_proposed_action():
    state = {"query": "Refund this customer and send confirmation email", "risk_level": "high"}

    result = risky_action_node(state)

    assert "Refund this customer" in result["proposed_action"]
    assert result["events"][0]["node"] == "risky_action"
    assert result["events"][0]["event_type"] == "completed"


def test_risky_action_node_flags_high_risk_in_event_metadata():
    state = {"query": "Delete customer account after support verification", "risk_level": "high"}

    result = risky_action_node(state)

    assert result["events"][0]["metadata"]["risk_level"] == "high"


def test_approval_node_default_mock_approves(monkeypatch):
    monkeypatch.delenv("LANGGRAPH_INTERRUPT", raising=False)
    state = {"proposed_action": "Refund $50 to customer 123"}

    result = approval_node(state)

    assert result["approval"]["approved"] is True
    assert result["approval"]["reviewer"] == "mock-reviewer"
    assert result["events"][0]["node"] == "approval"


def test_approval_node_does_not_interrupt_when_flag_unset(monkeypatch):
    monkeypatch.delenv("LANGGRAPH_INTERRUPT", raising=False)

    def boom(_value):
        raise AssertionError("interrupt() must not be called when LANGGRAPH_INTERRUPT is unset")

    monkeypatch.setattr("langgraph_agent_lab.nodes.interrupt", boom)

    result = approval_node({"proposed_action": "Refund $50"})

    assert result["approval"]["approved"] is True


def test_approval_node_uses_interrupt_resume_value_when_flag_enabled(monkeypatch):
    monkeypatch.setenv("LANGGRAPH_INTERRUPT", "true")
    monkeypatch.setattr(
        "langgraph_agent_lab.nodes.interrupt",
        lambda _value: {
            "approved": False,
            "reviewer": "human-reviewer",
            "comment": "needs more info",
        },
    )

    result = approval_node({"proposed_action": "Delete account 42"})

    assert result["approval"] == {
        "approved": False,
        "reviewer": "human-reviewer",
        "comment": "needs more info",
    }
