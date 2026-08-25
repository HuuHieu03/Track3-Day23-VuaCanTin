"""Render human-readable Markdown reports from scenario metrics."""

from __future__ import annotations

from pathlib import Path

from .metrics import MetricsReport


def _markdown_cell(value: object) -> str:
    """Return a value safe for use inside a Markdown table cell."""
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def render_report(metrics: MetricsReport) -> str:
    """Render a complete, deterministic Markdown report from ``metrics``."""
    resume_status = "đã chứng minh thành công" if metrics.resume_success else "chưa được chứng minh"
    lines = [
        "# Báo cáo Lab Day 08",
        "",
        "## 1. Tổng hợp metrics",
        "",
        "| Chỉ số | Giá trị |",
        "|---|---:|",
        f"| Tổng số scenario | {metrics.total_scenarios} |",
        f"| Tỷ lệ thành công | {metrics.success_rate:.2%} |",
        f"| Số node trung bình | {metrics.avg_nodes_visited:.2f} |",
        f"| Tổng số lần retry | {metrics.total_retries} |",
        f"| Tổng số lần interrupt | {metrics.total_interrupts} |",
        f"| Khôi phục thành công | {'Có' if metrics.resume_success else 'Không'} |",
        "",
        "## 2. Kết quả scenario",
        "",
        "| Scenario | Route mong đợi | Route thực tế | Thành công | Số node | Retry | "
        "Interrupt | Approval | Latency (ms) | Lỗi |",
        "|---|---|---|:---:|---:|---:|---:|:---:|---:|---|",
    ]

    for item in metrics.scenario_metrics:
        approval = (
            "Đã ghi nhận"
            if item.approval_observed
            else "Bị thiếu" if item.approval_required else "Không yêu cầu"
        )
        errors = "; ".join(item.errors) if item.errors else "Không có"
        row = [
            item.scenario_id,
            item.expected_route,
            item.actual_route or "Chưa có",
            "Có" if item.success else "Không",
            item.nodes_visited,
            item.retry_count,
            item.interrupt_count,
            approval,
            item.latency_ms,
            errors,
        ]
        lines.append("| " + " | ".join(_markdown_cell(value) for value in row) + " |")

    lines.extend(
        [
            "",
            "## 3. Kiến trúc và state",
            "",
            "StateGraph đưa yêu cầu qua `intake` và `classify`, sau đó chọn nhánh trả lời trực "
            "tiếp, gọi tool, hỏi lại, xét duyệt tác vụ rủi ro hoặc xử lý lỗi. Kết quả từ tool "
            "phải qua `evaluate`. Nếu kết quả chưa đạt, graph chỉ retry trong giới hạn; mọi nhánh "
            "kết thúc đều đi qua `finalize` trước `END`.",
            "",
            "Các trường `route`, `attempt` và `final_answer` dùng cách ghi đè. Những danh sách "
            "phục vụ audit như `messages`, `tool_results`, `errors` và `events` dùng reducer nối "
            "thêm để giữ lại lịch sử qua từng node.",
            "",
            "## 4. Phân tích lỗi",
            "",
            "1. Lỗi tạm thời từ tool hoặc provider có thể tạo ra kết quả thiếu. Graph ghi nhận "
            "lỗi và chỉ retry khi `attempt < max_attempts`; yêu cầu hết lượt sẽ đi vào "
            "`dead_letter`.",
            "2. Tác vụ rủi ro không được gọi tool trước khi có approval. Metrics về approval giúp "
            "phát hiện scenario cần xét duyệt nhưng không có bằng chứng xét duyệt.",
            "",
            "## 5. Persistence và recovery",
            "",
            f"Kết quả kiểm tra khôi phục checkpoint: {resume_status}.",
            "Mỗi scenario dùng một thread ID ổn định để có thể kiểm tra hoặc khôi phục lịch sử "
            "checkpoint.",
            "",
            "## 6. Kế hoạch hoàn thiện",
            "",
            "Các việc tiếp theo gồm đặt timeout và retry cho provider, xác thực người phê duyệt, "
            "kiểm thử khôi phục checkpoint trên ổ đĩa, đồng thời theo dõi latency và lỗi.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(metrics: MetricsReport, output_path: str | Path) -> None:
    """Write the rendered report to a file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report(metrics), encoding="utf-8")
