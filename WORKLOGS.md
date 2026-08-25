# Nhật ký công việc của nhóm

Tài liệu này ghi lại phạm vi phụ trách và tiến độ của từng thành viên. Cập nhật bảng công việc khi bắt đầu, bàn giao hoặc hoàn thành một nhiệm vụ.

## Phân công

| Vai trò | Phạm vi | Tệp phụ trách chính | Trạng thái hiện tại |
|---|---|---|---|
| Role 1: Kiến trúc graph | State, routing và kết nối graph | `state.py`, `routing.py`, `graph.py` | Đã hoàn thành và tích hợp (`3265a9a`) |
| Role 2: Kỹ sư AI/LLM | Tích hợp provider và các node dùng LLM | `llm.py`, phần LLM trong `nodes.py` | Đã hoàn thành và tích hợp (`5d3e686`) |
| Role 3: Kỹ sư workflow | Tool, đánh giá, retry và kết thúc luồng | Phần workflow trong `nodes.py` | Đã hoàn thành và tích hợp (`b30f0d7`) |
| Role 4: Kỹ sư an toàn và persistence | Approval, tác vụ rủi ro và checkpoint | Phần safety trong `nodes.py`, `persistence.py` | Đã hoàn thành và tích hợp (`7a930d8`, `f6ad8bd`) |
| Role 5: QA, metrics và báo cáo | Test, scenario, metrics và báo cáo lab | `tests/`, `data/sample/`, `report.py`, `reports/` | Đã hoàn thành |

## Lịch sử công việc

| Ngày | Người thực hiện | Công việc | Trạng thái | Ghi chú |
|---|---|---|---|---|
| 2026-08-25 | Role 1 | Cài đặt state, routing, graph và xuất Mermaid | Hoàn thành | Đã tích hợp commit `3265a9a`; 27 test routing, state và hồi quy của Role 5 đã pass; graph biên dịch với 11 workflow node và 19 edge; Ruff và mypy đã pass |
| 2026-08-25 | Role 2 | Cài đặt classify, answer, clarification và nạp `.env` | Hoàn thành | Đã tích hợp qua PR #2 tại `5d3e686`; năm query chuẩn được OpenAI phân loại đúng trong smoke test |
| 2026-08-25 | Role 3 | Cài đặt tool execution, evaluate, retry và dead-letter | Hoàn thành | Đã tích hợp vào `main` tại `b30f0d7`; test bao phủ phục hồi retry và đường đi dead-letter |
| 2026-08-25 | Role 4 | Cài đặt risky action, approval và SQLite checkpointer | Hoàn thành | Các test safety, WAL và lưu state qua nhiều checkpointer instance đã pass |
| 2026-08-25 | Role 5 | Cài đặt báo cáo metrics dạng Markdown và unit test | Hoàn thành | Đã thêm bảng tổng hợp, bảng kết quả, các phần phân tích và test ghi tệp |
| 2026-08-25 | Role 5 | Mở rộng test cho các trường hợp biên của metrics | Hoàn thành | Đã kiểm tra approval, kết quả clarification, số event, latency, số liệu tổng hợp và đầu vào rỗng |
| 2026-08-25 | Role 5 | Thêm scenario tùy chỉnh | Hoàn thành | Đã thêm hai trường hợp kiểm tra độ ưu tiên `tool > error` và `risky > tool`, kèm test hợp đồng dữ liệu |
| 2026-08-25 | Role 5 | Sửa smoke test và thêm graph topology test | Hoàn thành | Smoke test tự nạp `.env`; topology có đủ 11 workflow node và 19 edge |
| 2026-08-25 | Role 5 | Kiểm thử CLI và tệp metrics | Hoàn thành | CLI chấp nhận báo cáo từ 6 scenario và từ chối báo cáo dưới ngưỡng; tổng cộng 41 test offline pass, toàn bộ `tests/` sạch Ruff |
| 2026-08-25 | Role 5 | Dọn quality gate sau tích hợp | Hoàn thành | Chuẩn hóa type annotation cho tests, sửa lint trong CLI/scenario/persistence; `ruff check src tests` đã pass |
| 2026-08-25 | Role 5 | Hoàn tất kiểm thử tích hợp, benchmark và báo cáo | Hoàn thành | 9/9 scenario thành công, metrics hợp lệ; 58 test offline và 6 smoke test OpenAI đã pass; Ruff sạch. `resume_success` còn false vì chưa có bài kiểm thử phục hồi sau sự cố thực tế |
