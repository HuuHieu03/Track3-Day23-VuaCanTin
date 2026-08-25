# Nhật ký công việc của nhóm

Tài liệu này ghi lại phạm vi phụ trách và tiến độ của từng thành viên. Cập nhật bảng công việc khi bắt đầu, bàn giao hoặc hoàn thành một nhiệm vụ.

## Phân công

| Vai trò | Phạm vi | Tệp phụ trách chính | Trạng thái hiện tại |
|---|---|---|---|
| Role 1: Kiến trúc graph | State, routing và kết nối graph | `state.py`, `routing.py`, `graph.py` | Đã hoàn thành và tích hợp (`3265a9a`) |
| Role 2: Kỹ sư AI/LLM | Tích hợp provider và các node dùng LLM | `llm.py`, phần LLM trong `nodes.py` | Đã phân công, chưa có bản triển khai |
| Role 3: Kỹ sư workflow | Tool, đánh giá, retry và kết thúc luồng | Phần workflow trong `nodes.py` | Đã phân công, chưa có bản triển khai |
| Role 4: Kỹ sư an toàn và persistence | Approval, tác vụ rủi ro và checkpoint | Phần safety trong `nodes.py`, `persistence.py` | Đã phân công, chưa có bản triển khai |
| Role 5: QA, metrics và báo cáo | Test, scenario, metrics và báo cáo lab | `tests/`, `data/sample/`, `report.py`, `reports/` | Đang thực hiện |

## Lịch sử công việc

| Ngày | Người thực hiện | Công việc | Trạng thái | Ghi chú |
|---|---|---|---|---|
| 2026-08-25 | Role 1 | Cài đặt state, routing, graph và xuất Mermaid | Hoàn thành | Đã tích hợp commit `3265a9a`; 27 test routing, state và hồi quy của Role 5 đã pass; graph biên dịch với 11 workflow node và 19 edge; Ruff và mypy đã pass |
| 2026-08-25 | Role 5 | Cài đặt báo cáo metrics dạng Markdown và unit test | Hoàn thành | Đã thêm bảng tổng hợp, bảng kết quả, các phần phân tích và test ghi tệp |
| 2026-08-25 | Role 5 | Mở rộng test cho các trường hợp biên của metrics | Hoàn thành | Đã kiểm tra approval, kết quả clarification, số event, latency, số liệu tổng hợp và đầu vào rỗng |
| 2026-08-25 | Role 5 | Thêm scenario tùy chỉnh | Hoàn thành | Đã thêm hai trường hợp kiểm tra độ ưu tiên `tool > error` và `risky > tool`, kèm test hợp đồng dữ liệu |
| 2026-08-25 | Role 5 | Chuẩn bị báo cáo nộp bài | Đang thực hiện | Đã viết kiến trúc, state, bảng scenario, phân tích lỗi và bằng chứng hiện có; metrics khi chạy thật và bằng chứng persistence còn chờ Role 2, 3 và 4 |
