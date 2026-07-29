# E2E Test Verification & Adversarial Challenge Report — Challenger 2

Tài liệu này báo cáo kết quả thực nghiệm toàn bộ test suite E2E của dự án **CodeAvatar**, đánh giá độ tin cậy và phân tích các lỗi phát sinh dưới môi trường chạy test.

---

## 1. Observation (Quan sát Thực nghiệm)

### Lệnh chạy test thực tế:
```bash
# Thiết lập môi trường ảo venv và cài đặt dependencies
python3 -m venv .venv
.venv/bin/pip install pytest pytest-asyncio fastapi httpx google-api-python-client python-multipart

# Chạy test suite chính thức với mock python path và thư viện AI giả lập
PATH=/home/thienvu/workspace/CodeAvatar/.venv/bin:$PATH PYTHONPATH=/home/thienvu/workspace/CodeAvatar/tests/mocks:/home/thienvu/workspace/CodeAvatar .venv/bin/pytest tests/e2e/ -v
```

### Kết quả chạy test:
*   **Tổng số test cases**: 60
*   **Passed**: 53 / 60 (88.3%)
*   **Failed**: 7 / 60 (11.7%)

### Chi tiết 7 test cases bị FAILED:

1.  **`tests/e2e/tier1_feature_coverage/test_r4_backend.py::test_sse_log_stream_endpoint`**
    *   *Lỗi verbatim:*
        ```text
        E       TypeError: TestClient.get() got an unexpected keyword argument 'stream'
        ```
2.  **`tests/e2e/tier2_boundary_corner/test_r4_boundaries.py::test_sse_client_disconnect_handling`**
    *   *Lỗi verbatim:*
        ```text
        E       TypeError: TestClient.get() got an unexpected keyword argument 'stream'
        ```
3.  **`tests/e2e/tier3_cross_feature/test_r1_r2_integration.py::test_alpha_webm_drive_upload_flow`**
    *   *Lỗi verbatim:*
        ```text
        E       assert 404 == 200
        E        +  where 404 = <Response [404 Not Found]>.status_code
        ```
4.  **`tests/e2e/tier4_real_world/test_scenario_basic_flow.py::test_standard_meet_recording_e2e`**
    *   *Lỗi verbatim:*
        ```text
        E       TypeError: TestClient.get() got an unexpected keyword argument 'stream'
        ```
5.  **`tests/e2e/tier4_real_world/test_scenario_basic_flow.py::test_remote_gpu_worker_audio_only_e2e`**
    *   *Lỗi verbatim:*
        ```text
        E       assert 404 == 200
        E        +  where 404 = <Response [404 Not Found]>.status_code
        ```
6.  **`tests/e2e/tier4_real_world/test_scenario_basic_flow.py::test_resumable_large_file_drive_backup_e2e`**
    *   *Lỗi verbatim:*
        ```text
        E       assert 200 == 503
        E        +  where 200 = <Response [200 OK]>.status_code
        ```
7.  **`tests/e2e/tier4_real_world/test_scenario_basic_flow.py::test_concurrent_multi_user_gpu_saturation_e2e`**
    *   *Lỗi verbatim:*
        ```text
        E       TypeError: TestClient.get() got an unexpected keyword argument 'stream'
        ```

---

## 2. Logic Chain (Chuỗi Luận cứ)

Từ các quan sát thực nghiệm trên, chúng tôi suy luận nguyên nhân gốc rễ của các lỗi như sau:

1.  **Lỗi SSE Stream (`TypeError: TestClient.get() got an unexpected keyword argument 'stream'`)**:
    *   *Lập luận*: Test suite được viết sử dụng `api_client.get(..., stream=True)` để đọc Server-Sent Events. Cú pháp này thuộc về các phiên bản cũ của `fastapi.testclient.TestClient` khi nó còn sử dụng thư viện `requests` làm backend.
    *   *Nguyên nhân*: Các phiên bản FastAPI mới hơn đã chuyển hẳn sang sử dụng `httpx` làm backend cho `TestClient`. `httpx` không hỗ trợ tham số `stream` trong phương thức `.get()`. Cú pháp đúng phải là sử dụng context manager `client.stream("GET", url)`. Do đó, bất kỳ test case nào cố kiểm tra SSE log stream đều bị crash ngay khi gửi request.
    *   *Ảnh hưởng*: Gây hỏng 4 test cases (`test_sse_log_stream_endpoint`, `test_sse_client_disconnect_handling`, `test_standard_meet_recording_e2e`, `test_concurrent_multi_user_gpu_saturation_e2e`).

2.  **Lỗi Race Condition trong Kiểm thử Bất đồng bộ (`assert 404 == 200` khi download)**:
    *   *Lập luận*: Trong các test case `test_alpha_webm_drive_upload_flow` và `test_remote_gpu_worker_audio_only_e2e`, test code đợi job hoàn thành thông qua vòng lặp thăm dò (polling loop) tối đa 50 lần, mỗi lần cách nhau 0.01 giây (tổng cộng tối đa 0.5 giây).
    *   *Nguyên nhân*: Dưới tải chạy đồng loạt toàn bộ test suite (CPU saturation), tiến trình chạy ngầm `_process_queue` xử lý job mất nhiều hơn 0.5 giây. Khi vòng lặp kết thúc, job vẫn đang ở trạng thái `processing` hoặc `pending`, các file kết quả chưa được tạo trên đĩa sandbox. Khi test code tiếp tục gọi endpoint download, backend trả về `404 Not Found` dẫn đến Assertion Error.
    *   *Bằng chứng*: Khi chạy riêng lẻ các test case này độc lập (tài nguyên CPU dồi dào, không bị nghẽn queue), test case chạy hoàn toàn thành công (**PASSED**).

3.  **Lỗi Resumable Upload Simulation (`assert 200 == 503` ở chunk 2 và 4)**:
    *   *Lập luận*: Test case `test_resumable_large_file_drive_backup_e2e` thiết lập biến môi trường `os.environ["SIMULATE_NETWORK_FAILURE"] = "true"` ngay trước request gửi chunk 2. Nó kỳ vọng backend nhận diện biến môi trường này và trả về `503`.
    *   *Nguyên nhân*: Mặc dù TestClient chạy chung tiến trình, việc truyền và so khớp trạng thái thông qua biến môi trường toàn cục `os.environ` gặp vấn đề không đồng bộ hoặc logic so khớp điều kiện `chunk_index == 2` trong mock backend không khớp (ví dụ: FastAPI parse chunk_index hoặc cách thức TestClient gửi data không kích hoạt đúng luồng exception). Kết quả là backend tiếp tục xử lý thành công và trả về `200 OK` thay vì ném lỗi `503` giả lập.

---

## 3. Caveats (Các Điểm Lưu ý & Giả định)

*   **Mock AI Libraries**: Do môi trường chạy test là offline (CODE_ONLY network mode) và việc cài đặt các thư viện AI nặng như `torch`, `whisper`, `TTS` (lên tới hàng GB) là bất khả thi, chúng tôi đã xây dựng các mock package tối giản cho `torch`, `whisper`, và `TTS` đặt trong thư mục `tests/mocks/` và cấu hình qua `PYTHONPATH` để tránh lỗi `ModuleNotFoundError`.
*   **Dummy Files**: Thêm file `dummy_path.wav` trống vào root để đáp ứng điều kiện `os.path.exists()` trong `transcriber.py` của test pipeline.
*   **Mock Leakage**: Có khả năng xuất hiện hiện tượng rò rỉ mock trạng thái khi chạy toàn bộ test suite đồng loạt (khiến `test_vram_cleanup_after_unload` đôi lúc bị fail khi chạy chung nhưng luôn pass khi chạy riêng).

---

## 4. Conclusion (Kết luận)

1.  Bộ test suite E2E hiện tại **chưa thể chạy passed 100%** (chỉ đạt **53 / 60 passed** khi chạy E2E folder chính thức).
2.  **Đánh giá độ tin cậy đối với các kịch bản đặc biệt**:
    *   **Path Traversal Blocking**: Hoạt động **ổn định và chính xác** (pass test case `test_path_traversal_attack_variations`).
    *   **Resumable Upload Network Failure Recovery**: **Không ổn định** dưới môi trường test do lỗi mô phỏng đứt mạng `200 OK` thay vì `503`.
    *   **Multi-user VRAM Queue Orchestration**: **Không hoạt động** trong môi trường test do lỗi không tương thích cú pháp SSE stream của `TestClient` với thư viện FastAPI/Starlette hiện tại.

*Khuyến nghị*:
*   Cập nhật test suite để thay thế `api_client.get(..., stream=True)` bằng `with api_client.stream("GET", ...) as response:` để tương thích với FastAPI TestClient mới.
*   Tăng thời gian timeout/số lần loop trong kiểm thử bất đồng bộ (ví dụ: tăng từ 50 lần lên 200 lần) để tránh race condition khi CPU bị nghẽn.
*   Xem xét lại cơ chế truyền tín hiệu giả lập lỗi mạng (thay vì dùng biến môi trường `os.environ` dễ bị lỗi đồng bộ, nên dùng request header hoặc parameter cụ thể).

---

## 5. Verification Method (Cách thức Xác minh Độc lập)

Người nhận báo cáo hoặc các tác nhân khác có thể chạy lại bộ test để xác minh các lỗi trên bằng các lệnh sau:

```bash
# 1. Kích hoạt môi trường ảo
source .venv/bin/activate

# 2. Chạy toàn bộ suite E2E để xác minh tỷ lệ pass/fail
PATH=/home/thienvu/workspace/CodeAvatar/.venv/bin:$PATH PYTHONPATH=/home/thienvu/workspace/CodeAvatar/tests/mocks:/home/thienvu/workspace/CodeAvatar pytest tests/e2e/ -v

# 3. Chạy riêng lẻ test case SSE để kiểm chứng lỗi stream=True
PATH=/home/thienvu/workspace/CodeAvatar/.venv/bin:$PATH PYTHONPATH=/home/thienvu/workspace/CodeAvatar/tests/mocks:/home/thienvu/workspace/CodeAvatar pytest tests/e2e/tier1_feature_coverage/test_r4_backend.py::test_sse_log_stream_endpoint -vv
```
