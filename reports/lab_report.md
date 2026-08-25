# Báo cáo Lab Day 08

## 1. Thông tin nhóm

- Mô hình thực hiện: nhóm 5 thành viên.
- Người tổng hợp kiểm thử, metrics và báo cáo: Role 5.

## 2. Tổng hợp metrics

| Chỉ số | Giá trị |
|---|---:|
| Tổng số scenario | 9 |
| Tỷ lệ thành công | 100.00% |
| Số node trung bình | 6.67 |
| Tổng số lần retry | 4 |
| Tổng số lần interrupt | 3 |
| Khôi phục thành công | Không |

## 3. Kết quả scenario

| Scenario | Route mong đợi | Route thực tế | Thành công | Số node | Retry | Interrupt | Approval | Latency (ms) | Lỗi |
|---|---|---|:---:|---:|---:|---:|:---:|---:|---|
| S01_simple | simple | simple | Có | 4 | 0 | 0 | Không yêu cầu | 5369 | Không có |
| S02_tool | tool | tool | Có | 6 | 0 | 0 | Không yêu cầu | 2834 | Không có |
| S03_missing | missing_info | missing_info | Có | 4 | 0 | 0 | Không yêu cầu | 1634 | Không có |
| S04_risky | risky | risky | Có | 8 | 0 | 1 | Đã ghi nhận | 2768 | Không có |
| S05_error | error | error | Có | 11 | 3 | 0 | Không yêu cầu | 2400 | Retry attempt 1 scheduled after: no tool result yet; Retry attempt 2 scheduled after: ERROR: transient tool failure on attempt 1.; Retry attempt 3 scheduled after: SUCCESS: transient tool failure recovered on attempt 2. |
| S06_delete | risky | risky | Có | 8 | 0 | 1 | Đã ghi nhận | 2800 | Không có |
| S07_dead_letter | error | error | Có | 5 | 1 | 0 | Không yêu cầu | 781 | Retry attempt 1 scheduled after: no tool result yet |
| S08_custom | tool | tool | Có | 6 | 0 | 0 | Không yêu cầu | 2777 | Không có |
| S09_complex | risky | risky | Có | 8 | 0 | 1 | Đã ghi nhận | 3076 | Không có |

## 4. Kiến trúc và state

StateGraph đưa yêu cầu qua `intake` và `classify`, sau đó chọn nhánh trả lời trực tiếp, gọi tool, hỏi lại, xét duyệt tác vụ rủi ro hoặc xử lý lỗi. Kết quả từ tool phải qua `evaluate`. Nếu kết quả chưa đạt, graph chỉ retry trong giới hạn; mọi nhánh kết thúc đều đi qua `finalize` trước `END`.

Các trường `route`, `attempt` và `final_answer` dùng cách ghi đè. Những danh sách phục vụ audit như `messages`, `tool_results`, `errors` và `events` dùng reducer nối thêm để giữ lại lịch sử qua từng node.

## 5. Phân tích lỗi

1. Lỗi tạm thời từ tool hoặc provider có thể tạo ra kết quả thiếu. Graph ghi nhận lỗi và chỉ retry khi `attempt < max_attempts`; yêu cầu hết lượt sẽ đi vào `dead_letter`.
2. Tác vụ rủi ro không được gọi tool trước khi có approval. Metrics về approval giúp phát hiện scenario cần xét duyệt nhưng không có bằng chứng xét duyệt.

Benchmark ghi nhận retry sau kết quả `SUCCESS` ở S05_error. Điều này cho thấy LLM-as-judge có thể tạo thêm vòng lặp dù workflow vẫn hoàn tất.

## 6. Persistence và recovery

SQLite đã được kiểm chứng lưu và đọc lại state qua checkpointer instance mới. Chưa có bài kiểm thử tiếp tục graph sau sự cố, nên `resume_success` vẫn là `false`.
Mỗi scenario dùng một thread ID ổn định để có thể kiểm tra hoặc khôi phục lịch sử checkpoint.

## 7. Phần mở rộng

Graph có thể xuất Mermaid tại `outputs/graph.mmd`. Bộ dữ liệu có thêm S08 và S09 để kiểm tra độ ưu tiên route. SQLite checkpointer và approval interrupt đã được tích hợp; khôi phục sau sự cố thực tế vẫn cần một bài kiểm thử resume riêng.

## 8. Kế hoạch hoàn thiện

Các việc tiếp theo gồm đặt timeout và retry cho provider, xác thực người phê duyệt, kiểm thử khôi phục checkpoint trên ổ đĩa, đồng thời theo dõi latency và lỗi.
