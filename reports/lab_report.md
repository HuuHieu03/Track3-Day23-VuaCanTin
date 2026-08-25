# Báo cáo Lab Day 08

## 1. Thông tin nhóm

- Vai trò phụ trách báo cáo: Role 5, QA, metrics và viết tài liệu kỹ thuật
- Commit nền đã tích hợp: `3265a9a` (`Role 1 Finished`)
- Ngày cập nhật: 2026-08-25
- Trạng thái: Bản nháp, còn chờ kết quả chạy sau khi tích hợp Role 2, 3 và 4

## 2. Kiến trúc

Hệ thống dùng LangGraph `StateGraph`, gồm 11 workflow node và 19 edge. Mỗi yêu cầu bắt đầu theo luồng `START -> intake -> classify`, sau đó được chuyển vào một trong năm nhánh:

```text
simple       -> answer -> finalize -> END
tool         -> tool -> evaluate -> answer/retry
missing_info -> clarify -> finalize -> END
risky        -> risky_action -> approval -> tool/clarify
error        -> retry -> tool/dead_letter
```

Node `evaluate` quyết định trả lời hay thử lại. Vòng lặp được giới hạn bằng `max_attempts`; khi hết lượt, `route_after_retry` chuyển yêu cầu sang `dead_letter`. Nhờ đó, các nhánh đều có đường kết thúc tại `finalize -> END`. Graph nhận checkpointer qua cấu hình và dùng `thread_id` ổn định cho từng scenario. Sơ đồ Mermaid nằm trong `outputs/graph.mmd`.

## 3. Cấu trúc state

| Trường | Cách cập nhật | Mục đích |
|---|---|---|
| `route`, `risk_level` | Ghi đè | Route và mức rủi ro hiện tại |
| `attempt`, `max_attempts` | Ghi đè | Kiểm soát số lần retry |
| `evaluation_result` | Ghi đè | Dữ liệu đầu vào cho nhánh sau bước đánh giá |
| `pending_question` | Ghi đè | Câu hỏi làm rõ gửi cho người dùng |
| `proposed_action`, `approval` | Ghi đè | Trạng thái xét duyệt tác vụ rủi ro |
| `final_answer` | Ghi đè | Câu trả lời cuối cùng |
| `messages` | Nối thêm | Lịch sử hội thoại |
| `tool_results` | Nối thêm | Lịch sử kết quả từ tool |
| `errors` | Nối thêm | Lịch sử lỗi và retry |
| `events` | Nối thêm | Audit trail của từng node và nguồn dữ liệu cho metrics |

Các trường ghi đè chỉ giữ quyết định mới nhất của workflow. Những trường lưu lịch sử dùng `Annotated[list, operator.add]`, vì vậy dữ liệu do node trước ghi lại không bị node sau thay thế.

## 4. Kết quả scenario

Chưa có kết quả chạy thật vì các node của Role 2, 3 và 4 chưa được tích hợp. Sau khi có `outputs/metrics.json`, bảng dưới đây phải được cập nhật từ tệp đó, không điền bằng ước lượng.

| Scenario | Route mong đợi | Route thực tế | Thành công | Retry | Interrupt |
|---|---|---|:---:|---:|---:|
| S01_simple | simple | Chờ chạy | Chờ chạy | Chờ chạy | Chờ chạy |
| S02_tool | tool | Chờ chạy | Chờ chạy | Chờ chạy | Chờ chạy |
| S03_missing | missing_info | Chờ chạy | Chờ chạy | Chờ chạy | Chờ chạy |
| S04_risky | risky | Chờ chạy | Chờ chạy | Chờ chạy | Chờ chạy |
| S05_error | error | Chờ chạy | Chờ chạy | Chờ chạy | Chờ chạy |
| S06_delete | risky | Chờ chạy | Chờ chạy | Chờ chạy | Chờ chạy |
| S07_dead_letter | error | Chờ chạy | Chờ chạy | Chờ chạy | Chờ chạy |
| S08_custom | tool | Chờ chạy | Chờ chạy | Chờ chạy | Chờ chạy |
| S09_complex | risky | Chờ chạy | Chờ chạy | Chờ chạy | Chờ chạy |

Các bằng chứng đã xác nhận:

- Sau khi tích hợp Role 1, 27 test routing, state, metrics và report đã pass.
- Graph biên dịch thành công với 11 workflow node và 19 edge.
- Ruff và mypy đã pass trên phần cài đặt của Role 1 và các thay đổi của Role 5.
- Sáu graph smoke test đã chạy tới `classify_node`, sau đó dừng vì node này chưa được Role 2 triển khai.

## 5. Phân tích lỗi

1. Lỗi tạm thời từ tool hoặc provider có thể tạo ra kết quả thiếu. Kết quả đó phải qua `evaluate`, sau đó chỉ được retry khi `attempt < max_attempts`. Yêu cầu hết lượt retry sẽ đi vào `dead_letter`, thay vì lặp vô hạn.
2. Các tác vụ như hoàn tiền, xóa dữ liệu, hủy dịch vụ hoặc gửi email không được gọi tool trước khi có approval. Test và metrics tách `approval_required` khỏi `approval_observed`, nên báo cáo sẽ chỉ ra trường hợp cần xét duyệt nhưng không có bằng chứng xét duyệt.
3. OpenAI key đã có trong `.env` và tệp này được Git bỏ qua. Tuy nhiên, tiến trình Python hiện chưa tự đọc `.env`. Role 2 cần bổ sung cách nạp cấu hình an toàn hoặc ghi rõ lệnh export biến môi trường trước khi chạy.

## 6. Bằng chứng persistence và recovery

Graph đã biên dịch thành công với memory checkpointer. Mỗi scenario cũng có `thread_id` ổn định. Phần SQLite/WAL, phát lại lịch sử state và khôi phục sau sự cố còn chờ Role 4. Trước khi có bài kiểm tra recovery, `resume_success` phải giữ giá trị `false`.

## 7. Phần mở rộng

Role 1 đã xuất sơ đồ Mermaid vào `outputs/graph.mmd`. Hai scenario `S08_custom` và `S09_complex` kiểm tra thứ tự ưu tiên intent `tool > error` và `risky > tool`. Persistence trên ổ đĩa và HITL thực tế chưa được triển khai.

## 8. Kế hoạch hoàn thiện

Sau khi tích hợp Role 2, 3 và 4, nhóm cần chạy đủ chín scenario, kiểm tra `outputs/metrics.json` rồi thay toàn bộ ô "Chờ chạy" bằng kết quả thực tế. Các việc tiếp theo gồm đặt timeout và backoff cho provider, xác thực người phê duyệt, kiểm thử khôi phục checkpoint, bổ sung tracing có cấu trúc và đo latency tại từng node.
