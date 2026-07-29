## 2026-07-16T06:34:35Z

Bạn là E2E Test Architecture Explorer cho dự án CodeAvatar.
Working directory của bạn là: /home/thienvu/workspace/CodeAvatar/.agents/explorer_m2/
Mục tiêu của bạn:
1. Đọc file /home/thienvu/workspace/CodeAvatar/TEST_INFRA.md vừa được tạo ở thư mục gốc của project.
2. Phân tích cách triển khai 60 test cases E2E (Tier 1-4) qua CLI pipeline_cli.py và FastAPI backend.
3. Đề xuất phương án chạy kiểm thử (verification) bộ test E2E này khi chưa có code backend và CLI thực sự:
   - Hãy thiết kế phương án mock server và mock CLI cục bộ NẰM HOÀN TOÀN trong thư mục `/tests/` (ví dụ: qua fixtures trong `tests/e2e/conftest.py` hoặc các file test helper).
   - Mock server này sẽ giả lập toàn bộ hành vi của FastAPI backend (các endpoint POST /api/jobs, GET /api/jobs/{id}, SSE log stream, download file chống path traversal, v.v.).
   - Mock CLI sẽ giả lập hành vi của `pipeline_cli.py` (nhận các tham số, tạo các file output giả định, ghi nhận GPU cache giải phóng, v.v.).
   - Hãy đảm bảo phương án này không đụng chạm vào thư mục `/services/` để tránh vi phạm chính sách chống gian lận (Integrity Forensics) của Forensic Auditor khi quét mã nguồn sản phẩm.
4. Đề xuất danh sách chi tiết các file test cần viết và cấu trúc mã nguồn chi tiết cho các test case (Tier 1-4).
5. Viết báo cáo chi tiết vào file handoff.md trong thư mục làm việc của bạn (/home/thienvu/workspace/CodeAvatar/.agents/explorer_m2/handoff.md) và thông báo lại cho parent agent qua send_message.
