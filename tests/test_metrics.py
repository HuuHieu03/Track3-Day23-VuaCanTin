import pytest

from langgraph_agent_lab.metrics import metric_from_state, summarize_metrics
from langgraph_agent_lab.state import make_event


def test_metric_from_state_success() -> None:
    state = {
        "scenario_id": "S",
        "route": "simple",
        "final_answer": "ok",
        "events": [
            make_event("intake", "completed", "ok"),
            make_event("answer", "completed", "ok"),
        ],
        "errors": [],
        "approval": None,
    }
    metric = metric_from_state(state, expected_route="simple", approval_required=False)
    assert metric.success is True
    assert metric.nodes_visited == 2


def test_metric_from_state_route_mismatch() -> None:
    state = {
        "scenario_id": "S",
        "route": "tool",
        "final_answer": "ok",
        "events": [],
        "errors": [],
        "approval": None,
    }
    metric = metric_from_state(state, expected_route="simple", approval_required=False)
    assert metric.success is False


def test_metric_from_state_accepts_pending_question() -> None:
    state = {
        "scenario_id": "S_missing",
        "route": "missing_info",
        "pending_question": "Which account should be updated?",
    }

    metric = metric_from_state(state, expected_route="missing_info", approval_required=False)

    assert metric.success is True


def test_metric_from_state_requires_approval_evidence() -> None:
    state = {
        "scenario_id": "S_risky",
        "route": "risky",
        "final_answer": "Action prepared",
    }

    metric = metric_from_state(state, expected_route="risky", approval_required=True)

    assert metric.success is False
    assert metric.approval_required is True
    assert metric.approval_observed is False


def test_metric_from_state_records_approval_evidence() -> None:
    state = {
        "scenario_id": "S_risky",
        "route": "risky",
        "final_answer": "Request rejected safely",
        "approval": {"approved": False, "reviewer": "qa"},
    }

    metric = metric_from_state(state, expected_route="risky", approval_required=True)

    assert metric.success is True
    assert metric.approval_observed is True


def test_metric_from_state_counts_events_and_latency() -> None:
    state = {
        "scenario_id": "S_retry",
        "route": "error",
        "final_answer": "Recovered",
        "events": [
            make_event("retry", "completed", "retry one", latency_ms=7),
            {"node": "retry", "latency_ms": 11},
            make_event("approval", "completed", "reviewed", latency_ms=3),
        ],
        "errors": ["timeout"],
    }

    metric = metric_from_state(state, expected_route="error", approval_required=False)

    assert metric.nodes_visited == 3
    assert metric.retry_count == 2
    assert metric.interrupt_count == 1
    assert metric.latency_ms == 21
    assert metric.errors == ["timeout"]


def test_summarize_metrics() -> None:
    m1 = metric_from_state(
        {
            "scenario_id": "1",
            "route": "simple",
            "final_answer": "ok",
            "events": [make_event("answer", "completed", "ok")],
        },
        "simple",
        False,
    )
    m2 = metric_from_state(
        {
            "scenario_id": "2",
            "route": "tool",
            "final_answer": None,
            "events": [
                make_event("retry", "completed", "retry"),
                make_event("approval", "completed", "review"),
            ],
        },
        "tool",
        False,
    )
    report = summarize_metrics([m1, m2])

    assert report.total_scenarios == 2
    assert report.success_rate == 0.5
    assert report.avg_nodes_visited == 1.5
    assert report.total_retries == 1
    assert report.total_interrupts == 1


def test_summarize_metrics_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="No scenario metrics"):
        summarize_metrics([])
