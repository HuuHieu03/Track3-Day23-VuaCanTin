# Phân công công việc của nhóm

Tài liệu này tổng hợp vai trò, phạm vi phụ trách và trạng thái bàn giao của từng thành viên.

## Phân công

| Vai trò | Tên-MSV | Phạm vi | Tệp phụ trách chính | Trạng thái hiện tại |
|---|---|---|---|---|
| Role 1: Kiến trúc graph | Ngô Thành Đạt-2A202601323 | State, routing và kết nối graph | `state.py`, `routing.py`, `graph.py` | Đã hoàn thành và tích hợp (`3265a9a`) |
| Role 2: Kỹ sư AI/LLM | Nguyễn Hữu Hiếu-2A202601429 | Tích hợp provider và các node dùng LLM | `llm.py`, phần LLM trong `nodes.py` | Đã hoàn thành và tích hợp (`5d3e686`) |
| Role 3: Kỹ sư workflow | Nguyễn Chí Quang-2A202601932 | Tool, đánh giá, retry và kết thúc luồng | Phần workflow trong `nodes.py` | Đã hoàn thành và tích hợp (`b30f0d7`) |
| Role 4: Kỹ sư an toàn và persistence | Nguyễn Lê Minh-2A202601045 | Approval, tác vụ rủi ro và checkpoint | Phần safety trong `nodes.py`, `persistence.py` | Đã hoàn thành và tích hợp (`7a930d8`, `f6ad8bd`) |
| Role 5: QA, metrics và báo cáo | Trần Nguyễn Anh Minh-2A202601475 | Test, scenario, metrics và báo cáo lab | `tests/`, `data/sample/`, `report.py`, `reports/` | Đã hoàn thành |
