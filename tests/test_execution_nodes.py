from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from langgraph_agent_lab import llm as llm_module
from langgraph_agent_lab.nodes import (
    ToolEvaluation,
    dead_letter_node,
    evaluate_node,
    finalize_node,
    retry_or_fallback_node,
    tool_node,
)


class FakeStructuredJudge:
    def __init__(self, verdict: str) -> None:
        self.verdict = verdict

    def invoke(self, prompt: str) -> dict[str, str]:
        assert "<tool_result>" in prompt
        return {
            "evaluation_result": self.verdict,
            "reason": f"fake judge selected {self.verdict}",
        }


class FakeLLM:
    def __init__(self, verdict: str) -> None:
        self.verdict = verdict

    def with_structured_output(self, schema: type[ToolEvaluation]) -> FakeStructuredJudge:
        assert schema is ToolEvaluation
        return FakeStructuredJudge(self.verdict)


@pytest.mark.parametrize("attempt", [0, 1])
def test_tool_node_simulates_transient_error(attempt: int) -> None:
    update = tool_node({"route": "error", "attempt": attempt, "query": "timeout"})

    assert "ERROR" in update["tool_results"][0]
    assert update["events"][0]["node"] == "tool"
    assert update["events"][0]["event_type"] == "failed"


def test_tool_node_recovers_on_second_attempt() -> None:
    update = tool_node({"route": "error", "attempt": 2, "query": "timeout"})

    assert update["tool_results"][0].startswith("SUCCESS:")
    assert "recovered on attempt 2" in update["tool_results"][0]


def test_tool_node_returns_grounded_mock_lookup_result() -> None:
    update = tool_node(
        {
            "route": "tool",
            "attempt": 0,
            "query": "lookup order 123",
            "tool_results": ["existing result"],
        }
    )

    assert len(update["tool_results"]) == 1
    assert "lookup order 123" in update["tool_results"][0]
    assert update["events"][0]["metadata"]["route"] == "tool"


def test_tool_node_uses_proposed_action_for_risky_route() -> None:
    update = tool_node(
        {
            "route": "risky",
            "attempt": 0,
            "query": "refund customer",
            "proposed_action": "Refund order 123 after approval",
        }
    )

    assert "Refund order 123 after approval" in update["tool_results"][0]


@pytest.mark.parametrize("tool_results", [[], ["ERROR: timeout"]])
def test_evaluate_node_safety_gate_requires_retry(tool_results: list[str]) -> None:
    update = evaluate_node({"tool_results": tool_results})

    assert update["evaluation_result"] == "needs_retry"
    assert update["events"][0]["metadata"]["evaluator"] == "safety_heuristic"


def test_evaluate_node_uses_structured_llm_judge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm_module, "get_llm", lambda **_: FakeLLM("needs_retry"))

    update = evaluate_node({"tool_results": ["SUCCESS: result may be incomplete"]})

    assert update["evaluation_result"] == "needs_retry"
    assert update["events"][0]["metadata"]["evaluator"] == "llm"
    assert "fake judge" in update["events"][0]["metadata"]["reason"]


def test_evaluate_node_falls_back_when_llm_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable_llm(**_: Any) -> None:
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(llm_module, "get_llm", unavailable_llm)

    update = evaluate_node({"tool_results": ["SUCCESS: usable tool evidence"]})

    metadata = update["events"][0]["metadata"]
    assert update["evaluation_result"] == "success"
    assert metadata["evaluator"] == "heuristic_fallback"
    assert metadata["fallback_error_type"] == "RuntimeError"


def test_evaluate_node_only_judges_latest_result(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm_module, "get_llm", lambda **_: FakeLLM("success"))

    update = evaluate_node(
        {"tool_results": ["ERROR: old failure", "SUCCESS: recovered result"]}
    )

    assert update["evaluation_result"] == "success"


def test_retry_node_increments_once_and_returns_append_only_updates() -> None:
    state = {
        "route": "error",
        "attempt": 1,
        "max_attempts": 3,
        "tool_results": ["ERROR: timeout"],
        "errors": ["old error"],
        "events": [],
    }
    original = deepcopy(state)

    update = retry_or_fallback_node(state)

    assert state == original
    assert update["attempt"] == 2
    assert len(update["errors"]) == 1
    assert update["events"][0]["node"] == "retry"
    assert update["events"][0]["metadata"]["attempt"] == 2


def test_retry_node_handles_initial_error_route_without_tool_result() -> None:
    update = retry_or_fallback_node(
        {"route": "error", "attempt": 0, "max_attempts": 1, "tool_results": []}
    )

    assert update["attempt"] == 1
    assert "no tool result yet" in update["errors"][0]


def test_dead_letter_sets_answer_without_changing_classified_route() -> None:
    state = {"route": "error", "attempt": 1, "max_attempts": 1, "errors": ["failure"]}
    original = deepcopy(state)

    update = dead_letter_node(state)

    assert state == original
    assert update["final_answer"]
    assert "route" not in update
    assert update["events"][0]["node"] == "dead_letter"


def test_finalize_emits_only_final_audit_event() -> None:
    update = finalize_node({"route": "error", "final_answer": "manual review"})

    assert set(update) == {"events"}
    assert update["events"][0]["node"] == "finalize"
    assert update["events"][0]["event_type"] == "completed"
