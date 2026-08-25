from pathlib import Path

from langgraph_agent_lab.metrics import MetricsReport, ScenarioMetric
from langgraph_agent_lab.report import render_report, write_report


def sample_report() -> MetricsReport:
    return MetricsReport(
        total_scenarios=2,
        success_rate=0.5,
        avg_nodes_visited=3.5,
        total_retries=1,
        total_interrupts=1,
        resume_success=False,
        scenario_metrics=[
            ScenarioMetric(
                scenario_id="S01_simple",
                success=True,
                expected_route="simple",
                actual_route="simple",
                nodes_visited=3,
                latency_ms=12,
            ),
            ScenarioMetric(
                scenario_id="S02_risky",
                success=False,
                expected_route="risky",
                actual_route=None,
                nodes_visited=4,
                retry_count=1,
                interrupt_count=1,
                approval_required=True,
                approval_observed=False,
                latency_ms=30,
                errors=["provider | timeout"],
            ),
        ],
    )


def test_render_report_includes_summary_results_and_analysis() -> None:
    rendered = render_report(sample_report())

    assert "| Tỷ lệ thành công | 50.00% |" in rendered
    assert "| S01_simple | simple | simple | Có |" in rendered
    assert "| S02_risky | risky | Chưa có | Không |" in rendered
    assert "provider \\| timeout" in rendered
    assert "## 3. Kiến trúc và state" in rendered
    assert "## 4. Phân tích lỗi" in rendered
    assert "## 6. Kế hoạch hoàn thiện" in rendered


def test_write_report_creates_parent_directory(tmp_path: Path) -> None:
    output = tmp_path / "nested" / "lab_report.md"

    write_report(sample_report(), output)

    assert output.read_text(encoding="utf-8") == render_report(sample_report())
