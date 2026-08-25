import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from langgraph_agent_lab.cli import app
from langgraph_agent_lab.metrics import (
    MetricsReport,
    ScenarioMetric,
    summarize_metrics,
    write_metrics,
)
from langgraph_agent_lab.state import AgentState, make_event


class FakeGraph:
    def invoke(self, state: AgentState, _config: object = None, **_kwargs: object) -> AgentState:
        return {
            **state,
            "route": "simple",
            "final_answer": "stubbed answer",
            "events": [make_event("finalize", "completed", "workflow finished")],
        }


def _metrics_report(total: int) -> MetricsReport:
    items = [
        ScenarioMetric(
            scenario_id=f"S{index:02d}",
            success=True,
            expected_route="simple",
            actual_route="simple",
            nodes_visited=3,
        )
        for index in range(1, total + 1)
    ]
    return summarize_metrics(items)


def test_validate_metrics_accepts_valid_report(tmp_path: Path) -> None:
    metrics_path = tmp_path / "outputs" / "metrics.json"
    write_metrics(_metrics_report(6), metrics_path)

    result = CliRunner().invoke(app, ["validate-metrics", "--metrics", str(metrics_path)])

    assert result.exit_code == 0
    assert "Metrics valid. success_rate=100.00%" in result.stdout
    assert metrics_path.exists()


def test_validate_metrics_rejects_too_few_scenarios(tmp_path: Path) -> None:
    metrics_path = tmp_path / "metrics.json"
    write_metrics(_metrics_report(5), metrics_path)

    result = CliRunner().invoke(app, ["validate-metrics", "--metrics", str(metrics_path)])

    assert result.exit_code == 2
    assert "Expected at least 6 scenarios" in result.output


def test_run_scenarios_records_end_to_end_latency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scenarios_path = tmp_path / "scenarios.jsonl"
    scenarios = [
        {
            "id": f"S{index:02d}",
            "query": f"Simple query {index}",
            "expected_route": "simple",
        }
        for index in range(1, 7)
    ]
    scenarios_path.write_text(
        "\n".join(json.dumps(scenario) for scenario in scenarios),
        encoding="utf-8",
    )
    config_path = tmp_path / "lab.json"
    config_path.write_text(
        json.dumps({"scenarios_path": str(scenarios_path), "checkpointer": "none"}),
        encoding="utf-8",
    )
    metrics_path = tmp_path / "metrics.json"
    monkeypatch.setattr("langgraph_agent_lab.cli.build_graph", lambda checkpointer: FakeGraph())

    result = CliRunner().invoke(
        app,
        [
            "run-scenarios",
            "--config",
            str(config_path),
            "--output",
            str(metrics_path),
        ],
    )
    report = MetricsReport.model_validate_json(metrics_path.read_text(encoding="utf-8"))

    assert result.exit_code == 0
    assert all(item.latency_ms >= 1 for item in report.scenario_metrics)
