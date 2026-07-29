# TEST_INFRA — Hướng dẫn Hạ tầng Kiểm thử E2E dự án CodeAvatar

Tài liệu này mô tả triết lý kiểm thử, cấu trúc bộ test 4-tier, danh sách tính năng và cách thức chạy bộ test E2E (End-to-End) của dự án **CodeAvatar**.

---

## 1. Triết lý Kiểm thử (Testing Philosophy)

Bộ test E2E của CodeAvatar tuân theo triết lý **Opaque-Box Testing** (Kiểm thử hộp đục):
*   **Requirements-Driven:** Kiểm thử trực tiếp dựa trên các yêu cầu chức năng (R1 đến R5) từ phía người dùng thay vì kiểm tra chi tiết triển khai nội bộ.
*   **User-Centric Interactions:** Thực thi kiểm thử bằng cách giả lập các hành vi của người dùng thông qua CLI `pipeline_cli.py` và FastAPI backend API.
*   **Deterministic Assertions:** Đảm bảo các kết quả đầu ra như video WebM trong suốt, phụ đề `.srt`, file `timeline_shifts.json` và cơ chế lưu trữ SQLite/Google Drive tuân thủ đúng định dạng và các ràng buộc bảo mật.
*   **VRAM & Resource Monitoring:** Kiểm soát rò rỉ bộ nhớ GPU VRAM và RAM hệ thống trong suốt quá trình chạy test để đáp ứng tiêu chuẩn hiệu năng thực tế.

---

## 2. Cấu trúc Thư mục Bộ Test 4-Tier

Bộ test E2E sẽ được đặt trong thư mục `/tests/e2e/` của project (cần được khởi tạo) theo cấu trúc chi tiết như sau:

```text
/home/thienvu/workspace/CodeAvatar/
  ├── tests/
  │    ├── conftest.py                   # Cấu hình pytest chung và fixtures toàn hệ thống
  │    └── e2e/
  │         ├── conftest.py              # Mocking các API ngoài (Google Drive API, Ollama server khi test offline)
  │         ├── tier1_feature_coverage/  # Tier 1: Kiểm thử các tính năng độc lập (>=5 cases/feature)
  │         │    ├── test_r1_pipeline.py
  │         │    ├── test_r2_dta.py
  │         │    ├── test_r3_outputs.py
  │         │    ├── test_r4_backend.py
  │         │    └── test_r5_web_ui.py
  │         ├── tier2_boundary_corner/   # Tier 2: Kiểm thử các trường hợp biên và xử lý lỗi (>=5 cases/feature)
  │         │    ├── test_r1_boundaries.py
  │         │    ├── test_r2_boundaries.py
  │         │    ├── test_r3_boundaries.py
  │         │    ├── test_r4_boundaries.py
  │         │    └── test_r5_boundaries.py
  │         ├── tier3_cross_feature/     # Tier 3: Kiểm thử sự tương tác giữa các cặp tính năng
  │         │    ├── test_r1_r2_integration.py
  │         │    ├── test_r2_r3_integration.py
  │         │    ├── test_r1_r4_integration.py
  │         │    ├── test_r4_r5_integration.py
  │         │    └── test_r3_r5_integration.py
  │         └── tier4_real_world/        # Tier 4: Các kịch bản tích hợp hoàn chỉnh trong môi trường thực tế
  │              ├── test_scenario_basic_flow.py
  │              ├── test_scenario_slide_freeze.py
  │              ├── test_scenario_hybrid_mode.py
  │              ├── test_scenario_resumable_upload.py
  │              └── test_scenario_adversarial_vram.py
```

---

## 3. Danh sách Tính năng & Ánh xạ Test Cases

Dưới đây là bảng ánh xạ chi tiết giữa 5 yêu cầu cốt lõi (R1 - R5) và các test cases tương ứng trong bộ test E2E:

### R1. Core AI Pipeline
*   **F1.1 Noise Suppression (DeepFilterNet):** Lọc nhiễu âm thanh đầu vào.
*   **F1.2 Speaker Diarization (pyannote-audio):** Nhận diện phân đoạn người nói.
*   **F1.3 Speech-to-Text (Whisper):** Trích xuất văn bản tiếng Việt kèm word-level timestamps.
*   **F1.4 Translation (Ollama):** Dịch thuật song ngữ kèm Glossary thuật ngữ kỹ thuật.
*   **F1.5 Text-to-Speech (Piper / Coqui XTTS-v2):** Sinh giọng nói tiếng Anh/Hàn đồng bộ.
*   **F1.6 Lip-Sync & Face Restoration (Wav2Lip + GFPGAN):** Đồng bộ khẩu hình avatar và làm nét khuôn mặt.
*   **F1.7 GPU Memory Protection:** Giải phóng bộ nhớ GPU VRAM bằng `torch.cuda.empty_cache()` và phân tách tiến trình con (multiprocessing).
*   *Test Cases tiêu biểu:*
    *   `tier1_feature_coverage/test_r1_pipeline.py::test_whisper_transcription`
    *   `tier1_feature_coverage/test_r1_pipeline.py::test_ollama_translator_with_glossary`
    *   `tier1_feature_coverage/test_r1_pipeline.py::test_vram_cleanup_after_unload`
    *   `tier2_boundary_corner/test_r1_boundaries.py::test_empty_audio_transcription`
    *   `tier2_boundary_corner/test_r1_boundaries.py::test_ollama_unresponsive_fallback`

### R2. Dynamic Time Alignment (DTA) & Composition
*   **F2.1 Audio Time-Stretching:** Tự động co giãn tốc độ nói (0.85x - 1.25x) bằng bộ lọc `atempo` giữ nguyên pitch.
*   **F2.2 Silence Padding:** Tự động chèn khoảng lặng khi bản dịch ngắn hơn video gốc.
*   **F2.3 Video Padding (Freeze Frames):** Tự động đóng băng khung hình video (freeze frame) tại vị trí hợp lệ khi bản dịch dài hơn video gốc.
*   **F2.4 VFR to CFR Transcoding:** Chuẩn hóa video sang Constant Frame Rate bằng FFMPEG.
*   *Test Cases tiêu biểu:*
    *   `tier1_feature_coverage/test_r2_dta.py::test_audio_time_stretching_within_limits`
    *   `tier1_feature_coverage/test_r2_dta.py::test_video_padding_freeze_frames`
    *   `tier2_boundary_corner/test_r2_boundaries.py::test_dta_extreme_speed_compression`
    *   `tier2_boundary_corner/test_r2_boundaries.py::test_dta_extreme_speed_expansion`

### R3. Transparent Output & Timeline JSON
*   **F3.1 Transparent WebM VP9 Layer:** Xuất video MC ảo nền trong suốt (alpha channel, `yuva420p`, `alpha_mode=1`).
*   **F3.2 Aligned SRT Subtitles:** Đồng bộ timestamps trong file `.srt` theo kết quả DTA.
*   **F3.3 Timeline Shifts JSON:** Xuất file `timeline_shifts.json` ghi nhận slide duration delta để tích hợp vào Google Vids.
*   *Test Cases tiêu biểu:*
    *   `tier1_feature_coverage/test_r3_outputs.py::test_transparent_webm_alpha_channel`
    *   `tier1_feature_coverage/test_r3_outputs.py::test_timeline_shifts_json_format`
    *   `tier2_boundary_corner/test_r3_boundaries.py::test_srt_timestamps_overlap`
    *   `tier2_boundary_corner/test_r3_boundaries.py::test_invalid_avatar_id_paths`

### R4. FastAPI Backend & Database
*   **F4.1 Job Creation Endpoint (`POST /api/jobs`):** Hỗ trợ stream disk-buffering để tránh tràn RAM khi upload file lớn.
*   **F4.2 Job Status & SSE Log Stream:** Endpoint `GET /api/jobs/{id}/logs/stream` trả về real-time log.
*   **F4.3 FIFO Queue Orchestration:** Xử lý tuần tự các job AI để tránh quá tải GPU.
*   **F4.4 SQLite WAL Mode Storage:** Lưu trữ dữ liệu job và segment bằng SQLite WAL mode.
*   **F4.5 Path Traversal Protection:** Chặn đứng các nguy cơ Path Traversal trên các endpoint download.
*   *Test Cases tiêu biểu:*
    *   `tier1_feature_coverage/test_r4_backend.py::test_create_job_endpoint`
    *   `tier1_feature_coverage/test_r4_backend.py::test_fifo_queue_sequential_execution`
    *   `tier2_boundary_corner/test_r4_boundaries.py::test_path_traversal_attack_variations`
    *   `tier2_boundary_corner/test_r4_boundaries.py::test_job_queue_crash_recovery`

### R5. Aesthetic Web UI & Drive Sync
*   **F5.1 Glassmorphic Dark Mode UI:** Giao diện điều khiển và sửa kịch bản.
*   **F5.2 Debounced Script Editor:** Lưu bản chỉnh sửa phụ đề một cách tối ưu.
*   **F5.3 Google OAuth 2.0 via HttpOnly Cookie:** Quản lý token an toàn.
*   **F5.4 Google Drive Resumable Upload:** Đẩy file lớn lên Drive với quyền tối giản `drive.file`.
*   *Test Cases tiêu biểu:*
    *   `tier1_feature_coverage/test_r5_web_ui.py::test_script_editor_debouncing`
    *   `tier1_feature_coverage/test_r5_web_ui.py::test_google_drive_resumable_upload`
    *   `tier2_boundary_corner/test_r5_boundaries.py::test_drive_resumable_upload_network_interruption`

---

## 4. Cách thức Chạy Bộ Test (Test Execution Guide)

### Môi trường Yêu cầu (Prerequisites)
*   Python 3.10+
*   Pytest (`pip install pytest pytest-asyncio pytest-cov`)
*   FFMPEG teraterm (hỗ trợ libvpx-vp9)
*   SQLite3

### Các lệnh chạy bộ test chính
Bộ test được kích hoạt bằng `pytest` từ thư mục gốc của dự án:

1.  **Chạy toàn bộ test suite (Tiers 1 - 4):**
    ```bash
    pytest tests/ -v
    ```

2.  **Chạy riêng lẻ từng Tier:**
    *   **Tier 1 (Feature Coverage):**
        ```bash
        pytest tests/e2e/tier1_feature_coverage/ -v
        ```
    *   **Tier 2 (Boundary & Corner Cases):**
        ```bash
        pytest tests/e2e/tier2_boundary_corner/ -v
        ```
    *   **Tier 3 (Cross-Feature):**
        ```bash
        pytest tests/e2e/tier3_cross_feature/ -v
        ```
    *   **Tier 4 (Real-World Scenarios):**
        ```bash
        pytest tests/e2e/tier4_real_world/ -v
        ```

3.  **Chạy kiểm thử một yêu cầu cụ thể (ví dụ: R4 - Backend):**
    ```bash
    pytest -k "r4" -v
    ```

4.  **Chạy kiểm thử và xuất báo cáo độ phủ (Coverage Report):**
    ```bash
    pytest --cov=services --cov=apps tests/ -v
    ```
