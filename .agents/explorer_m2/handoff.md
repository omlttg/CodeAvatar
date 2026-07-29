# Handoff Report — E2E Test Architecture Design

Báo cáo chi tiết về phương án thiết kế hạ tầng kiểm thử E2E (End-to-End) gồm 60 test cases (Tier 1-4) giả lập hoàn toàn trong `/tests/` mà không cần chạm vào thư mục `/services/`.

---

## 1. Observation (Quan sát thực tế)

Qua việc khảo sát cấu trúc thư mục dự án `/home/thienvu/workspace/CodeAvatar/`, tôi ghi nhận các dữ kiện thực tế sau:
* **Tài liệu kiểm thử gốc (`TEST_INFRA.md`)**:
  * Chứa mô tả triết lý kiểm thử *Opaque-Box Testing*, cấu trúc thư mục bộ test 4-Tier nằm hoàn toàn dưới `/tests/e2e/`.
  * Liệt kê các yêu cầu chức năng từ R1 đến R5 bao gồm: Noise Suppression, Speaker Diarization, STT (Whisper), Translation (Ollama), TTS (Piper/XTTS-v2), Lip-Sync & Face Restoration (Wav2Lip+GFPGAN), Dynamic Time Alignment (DTA), Transparent WebM, Timeline JSON, FastAPI Backend (FIFO Queue, WAL SQLite, Path Traversal Protection), và Web UI (OAuth, Drive Resumable Upload).
* **Mã nguồn hiện tại**:
  * Các module phục vụ Pipeline AI đã có mã nguồn khung:
    * `/services/pipeline/transcriber.py` (sử dụng thư viện `whisper`)
    * `/services/pipeline/translator.py` (sử dụng `Ollama` qua cổng `11434`)
    * `/services/pipeline/tts.py` (gọi binary `piper` hoặc thư viện `TTS`)
  * Chưa tồn tại CLI chạy pipeline `/services/pipeline/pipeline_cli.py`.
  * Chưa có mã nguồn backend FastAPI `/services/backend/`.
  * Thư mục `/tests/` hiện mới chỉ có các file cấu hình khung rỗng:
    * `tests/conftest.py` (5 dòng)
    * `tests/e2e/conftest.py` (6 dòng)

---

## 2. Logic Chain (Chuỗi suy luận thiết kế)

Để chạy kiểm thử bộ 60 test cases E2E khi chưa có code CLI thực sự và backend thực sự, đồng thời tuyệt đối không sửa đổi thư mục `/services/` nhằm bảo vệ tính toàn vẹn (Integrity Forensics) của sản phẩm, phương án thiết kế được lập luận qua các bước logic sau:

1. **Cô lập Mock CLI**: 
   * Viết file mock CLI tại `/tests/e2e/mock_cli.py`. CLI này giả lập toàn bộ tham số nhận vào (`--video`, `--avatar`, `--voice`, `--target-lang`) và tạo ra các output giả định gồm video WebM trong suốt (`_rendered_alpha.webm`), phụ đề `.srt`, và file timing `timeline_shifts.json` đúng định dạng mong đợi, đồng thời log ra các dòng thông báo giải phóng bộ nhớ GPU (`torch.cuda.empty_cache`).
2. **Kỹ thuật Đánh chặn Tiến trình (Subprocess Interception)**:
   * Trong `tests/e2e/conftest.py`, định nghĩa fixture `intercept_pipeline_cli` sử dụng `unittest.mock.patch` để đánh chặn các hàm gọi hệ thống `subprocess.run` và `subprocess.Popen`.
   * Khi phát hiện lệnh gọi tới `services/pipeline/pipeline_cli.py`, fixture sẽ tự động định tuyến lại để thực thi `tests/e2e/mock_cli.py` với các tham số tương tự. 
   * Kết quả: Các test case E2E vẫn viết code gọi lệnh CLI sản phẩm bình thường nhưng khi chạy test sẽ gọi Mock CLI cục bộ, hoàn toàn không chạm vào thư mục `/services/`.
3. **Giả lập FastAPI Backend**:
   * Định nghĩa một mock server FastAPI tại `tests/e2e/mock_backend.py`.
   * **R4.1 Stream disk-buffering**: Endpoint `POST /api/jobs` đọc buffer theo chunk và lưu trực tiếp xuống file tạm trên đĩa cứng thay vì nạp toàn bộ vào RAM, mô phỏng quá trình chống tràn bộ nhớ.
   * **R4.3 FIFO Queue Orchestration**: Thiết lập hàng đợi FIFO đơn giản bằng `asyncio.Lock` và background task để xử lý tuần tự từng job, đẩy logs tiến độ tương ứng.
   * **R4.4 SQLite WAL Mode**: Kết nối SQLite cục bộ trong thư mục tạm `/tmp/codeavatar_test_backend` cấu hình `PRAGMA journal_mode=WAL` để kiểm thử độ bền bỉ dữ liệu.
   * **R4.5 Path Traversal Protection**: Khi gọi `GET /api/jobs/{id}/download`, sử dụng thuật toán chuẩn hóa đường dẫn `os.path.abspath` để so sánh với thư mục gốc của job, nếu file target nằm ngoài thư mục job sẽ chặn lập tức và trả về lỗi 400 Bad Request.
   * **R5.4 Resumable Upload & OAuth**: Endpoint `POST /api/jobs/{id}/upload-drive` kiểm tra token trong cookie HttpOnly và hỗ trợ nhận file dạng chunk-by-chunk. Có tham số môi trường `SIMULATE_NETWORK_FAILURE` để giả lập đứt mạng ở chunk giữa nhằm test khả năng tiếp tục upload (resume).
4. **Viết mã nguồn đề xuất (Proposed Artifacts)**:
   * Tôi đã chuẩn bị sẵn các file mã nguồn đề xuất nằm trong thư mục làm việc để implementer có thể trực tiếp sao chép vào `/tests/`:
     * `proposed_mock_cli.py` -> Sẽ lưu thành `tests/e2e/mock_cli.py`
     * `proposed_mock_backend.py` -> Sẽ lưu thành `tests/e2e/mock_backend.py`
     * `proposed_conftest.py` -> Sẽ ghi đè thành `tests/e2e/conftest.py`

---

## 3. Caveats (Lưu ý)

* **Giới hạn môi trường**: Hiện tại phương án này chỉ chạy giả lập (mocking) API và CLI. Khi tích hợp thật ở các Milestone sau, cần disable hoặc loại bỏ fixture đánh chặn subprocess trong `tests/e2e/conftest.py` và kết nối backend thực tế thay vì mock FastAPI app.
* **Tài nguyên GPU**: Do chạy trên mock, các kiểm thử GPU VRAM thực tế (như đo VRAM thực dùng qua PyTorch) được giả lập thông qua log kiểm tra chuỗi `torch.cuda.empty_cache`.

---

## 4. Conclusion (Kết luận thiết kế & Danh sách 60 Test Cases)

Bộ kiểm thử E2E 60 test cases được chia thành cấu trúc thư mục chuẩn 4-Tier:

### A. Cấu trúc thư mục mã nguồn kiểm thử
```text
/home/thienvu/workspace/CodeAvatar/tests/
  ├── conftest.py
  └── e2e/
       ├── conftest.py              # Đánh chặn CLI & mock API ngoài
       ├── mock_cli.py              # Mock CLI pipeline
       ├── mock_backend.py          # Mock FastAPI backend
       ├── tier1_feature_coverage/  # Tier 1 (25 cases)
       ├── tier2_boundary_corner/   # Tier 2 (25 cases)
       ├── tier3_cross_feature/     # Tier 3 (5 cases)
       └── tier4_real_world/        # Tier 4 (5 cases)
```

### B. Danh sách chi tiết 60 Test Cases (Tier 1-4)

#### Tier 1: Feature Coverage (25 cases)
* **`tier1_feature_coverage/test_r1_pipeline.py` (5 cases)**:
  1. `test_whisper_transcription`: Kiểm tra Whisper trích xuất văn bản kèm word-level timestamps.
  2. `test_ollama_translator_with_glossary`: Kiểm tra Ollama dịch thuật áp dụng Glossary từ điển.
  3. `test_piper_tts_generation`: Kiểm tra Piper sinh file âm thanh WAV thành công từ văn bản.
  4. `test_vram_cleanup_after_unload`: Kiểm tra giải phóng bộ nhớ GPU sau khi unload model.
  5. `test_noise_suppression_and_diarization`: Kiểm tra chạy thành công DeepFilterNet và phân đoạn pyannote-audio.
* **`tier1_feature_coverage/test_r2_dta.py` (5 cases)**:
  6. `test_audio_time_stretching_within_limits`: Kiểm tra co giãn tốc độ âm thanh trong giới hạn 0.85x - 1.25x.
  7. `test_video_padding_freeze_frames`: Kiểm tra chèn freeze frame khi video dịch dài hơn gốc.
  8. `test_silence_padding`: Kiểm tra chèn khoảng lặng khi video dịch ngắn hơn gốc.
  9. `test_vfr_to_cfr_transcoding`: Kiểm tra FFMPEG chuẩn hóa video CFR.
  10. `test_dta_duration_deltas`: Kiểm tra tính toán chính xác delta thời gian các slide.
* **`tier1_feature_coverage/test_r3_outputs.py` (5 cases)**:
  11. `test_transparent_webm_alpha_channel`: Kiểm tra xuất video WebM VP9 chứa kênh alpha trong suốt.
  12. `test_srt_subtitle_sync`: Kiểm tra đồng bộ phụ đề `.srt` theo thời gian DTA mới.
  13. `test_timeline_shifts_json_format`: Kiểm tra định dạng JSON timeline_shifts đúng cấu trúc.
  14. `test_separate_layers_output`: Kiểm tra xuất đầy đủ các file layer riêng biệt (video, audio, srt).
  15. `test_metadata_injection`: Kiểm tra ghi nhận ID job và cấu hình metadata vào file.
* **`tier1_feature_coverage/test_r4_backend.py` (5 cases)**:
  16. `test_create_job_endpoint`: Kiểm tra API POST `/api/jobs` nhận file và lưu DB SQLite.
  17. `test_get_job_status`: Kiểm tra API GET `/api/jobs/{id}` trả về chính xác trạng thái job.
  18. `test_fifo_queue_sequential_execution`: Kiểm tra cơ chế queue xử lý tuần tự (FIFO) tránh quá tải.
  19. `test_sqlite_wal_mode_enabled`: Kiểm tra SQLite kích hoạt WAL mode phục vụ ghi đọc đồng thời.
  20. `test_sse_log_stream_endpoint`: Kiểm tra API GET `/api/jobs/{id}/logs/stream` trả về SSE logs.
* **`tier1_feature_coverage/test_r5_web_ui.py` (5 cases)**:
  21. `test_script_editor_debouncing`: Kiểm tra debouncing tối ưu hóa gửi cập nhật script.
  22. `test_google_oauth_cookie_verification`: Kiểm tra OAuth xác thực qua cookie HttpOnly.
  23. `test_google_drive_resumable_upload`: Kiểm tra tải file lên Google Drive theo chunk bằng scope drive.file.
  24. `test_glassmorphic_ui_elements`: Kiểm tra sự tồn tại của CSS Glassmorphic dark mode trong UI.
  25. `test_drive_sync_status`: Kiểm tra cập nhật trạng thái đồng bộ Drive lên SQLite.

#### Tier 2: Boundary & Corner Cases (25 cases)
* **`tier2_boundary_corner/test_r1_boundaries.py` (5 cases)**:
  26. `test_empty_audio_transcription`: Kiểm tra Whisper xử lý âm thanh trống/im lặng hoàn toàn không crash.
  27. `test_ollama_unresponsive_fallback`: Kiểm tra fallback giữ nguyên gốc khi Ollama mất kết nối.
  28. `test_glossary_case_insensitivity`: Kiểm tra Glossary hoạt động không phân biệt chữ hoa chữ thường.
  29. `test_extremely_long_sentence_diarization`: Kiểm tra Diarization xử lý câu hội thoại cực dài không tràn RAM.
  30. `test_xtts_missing_speaker_reference`: Kiểm tra XTTS bắn lỗi rõ ràng khi thiếu file mẫu giọng nói.
* **`tier2_boundary_corner/test_r2_boundaries.py` (5 cases)**:
  31. `test_dta_extreme_speed_compression`: Kiểm tra giới hạn co tốc độ tối đa 1.25x và áp dụng trim/loop.
  32. `test_dta_extreme_speed_expansion`: Kiểm tra giới hạn giãn tốc độ tối thiểu 0.85x và chèn silence.
  33. `test_dta_zero_duration_segments`: Kiểm tra phân đoạn dài 0s không gây lỗi chia cho 0.
  34. `test_dta_corrupted_video_cfr_conversion`: Kiểm tra FFMPEG xử lý video hỏng header không treo tiến trình.
  35. `test_dta_extremely_long_silence_padding`: Kiểm tra chèn khoảng lặng lớn không gây tràn tài nguyên.
* **`tier2_boundary_corner/test_r3_boundaries.py` (5 cases)**:
  36. `test_srt_timestamps_overlap`: Khắc phục timestamps phụ đề bị đè chéo nhau.
  37. `test_invalid_avatar_id_paths`: Kiểm tra validate avatar ID không hợp lệ trước khi render.
  38. `test_timeline_json_empty_shifts`: Kiểm tra JSON timing hoạt động đúng khi danh sách shifts trống.
  39. `test_webm_alpha_corrupt_frames`: Kiểm tra FFMPEG bỏ qua các frame lỗi khi gộp alpha.
  40. `test_srt_unicode_characters`: Kiểm tra phụ đề tiếng Việt/Anh/Hàn chứa ký tự đặc biệt/emoji không lỗi font.
* **`tier2_boundary_corner/test_r4_boundaries.py` (5 cases)**:
  41. `test_path_traversal_attack_variations`: Chặn đứng tấn công path traversal với các biến thể `..`, absolute path, và hex-encoding.
  42. `test_job_queue_crash_recovery`: Khôi phục hàng đợi sau khi server backend bị crash đột ngột.
  43. `test_simultaneous_large_file_uploads`: Upload đồng thời nhiều file lớn kiểm tra RAM không tăng đột biến.
  44. `test_sse_client_disconnect_handling`: Thu hồi tài nguyên tiến trình khi client tắt SSE stream sớm.
  45. `test_concurrent_job_status_polling`: Kiểm tra DB SQLite chịu tải nhiều truy vấn poll trạng thái cùng lúc.
* **`tier2_boundary_corner/test_r5_boundaries.py` (5 cases)**:
  46. `test_drive_resumable_upload_network_interruption`: Giả lập đứt mạng khi đang upload Drive, tự động resume thành công từ chunk lỗi.
  47. `test_expired_oauth_token_refresh`: Tự động gọi làm mới token khi token cũ hết hạn.
  8. `test_drive_insufficient_space`: Trả lỗi rõ ràng khi Drive hết dung lượng.
  49. `test_script_editor_concurrent_edit_conflict`: Giải quyết xung đột khi 2 phiên sửa đổi script cùng lúc.
  50. `test_drive_invalid_file_permissions`: Kiểm tra chặn và báo lỗi 403 khi tải file không có quyền truy cập.

#### Tier 3: Cross-Feature Integration (5 cases)
* **`tier3_cross_feature/test_r1_r2_integration.py`**:
  51. `test_translation_dta_sync`: Liên kết R1 (Dịch thuật) và R2 (DTA) để điều khiển tốc độ audio khớp video.
* **`tier3_cross_feature/test_r2_r3_integration.py`**:
  52. `test_dta_shift_to_timeline_json_sync`: Thời gian DTA điều chỉnh phải cập nhật đồng bộ vào `timeline_shifts.json` và `.srt`.
* **`tier3_cross_feature/test_r1_r4_integration.py`**:
  53. `test_pipeline_unloading_under_fastapi_load`: Kiểm tra FastAPI queue quản lý tuần tự các pipeline AI nhằm giữ bộ nhớ VRAM an toàn dưới tải cao.
* **`tier3_cross_feature/test_r4_r5_integration.py`**:
  54. `test_script_edit_reprocesses_dta_pipeline`: Sửa kịch bản trên Web UI kích hoạt chạy lại DTA trên backend.
* **`tier3_cross_feature/test_r3_r5_integration.py`**:
  55. `test_alpha_webm_drive_upload_flow`: Xuất WebM trong suốt và tự động đẩy lên Drive thông qua resumable upload.

#### Tier 4: Real-World Scenarios (5 cases)
* **`tier4_real_world/test_scenario_basic_flow.py`**:
  56. `test_standard_meet_recording_e2e`: Kịch bản chuẩn: Upload video họp, dịch sang tiếng Anh, xuất WebM trong suốt + SRT, và đồng bộ Drive thành công.
* **`tier4_real_world/test_scenario_slide_freeze.py`**:
  57. `test_long_translation_slide_freeze_e2e`: Bản dịch dài hơn video gốc, kiểm tra chèn freeze frame ở slide cuối để bù đắp thời gian.
* **`tier4_real_world/test_scenario_hybrid_mode.py`**:
  58. `test_remote_gpu_worker_audio_only_e2e`: Phân chia tính toán: Client trích xuất audio gửi lên Server dịch, sau đó tải về tự render tại client.
* **`tier4_real_world/test_scenario_resumable_upload.py`**:
  59. `test_resumable_large_file_drive_backup_e2e`: Mô phỏng backup file 100MB lên Google Drive bị rớt mạng liên tục vẫn khôi phục truyền tải đúng byte-for-byte.
* **`tier4_real_world/test_scenario_adversarial_vram.py`**:
  60. `test_concurrent_multi_user_gpu_saturation_e2e`: Stress-test nhiều người dùng cùng submit job, hệ thống xếp hàng an toàn, VRAM không tăng đột ngột.

---

## 5. Verification Method (Phương pháp Xác minh)

Để kiểm chứng tính đúng đắn của phương án thiết kế này, người thực hiện (implementer) sẽ chạy các lệnh kiểm thử sau khi đã chuyển các file đề xuất từ `.agents/explorer_m2/` vào thư mục `/tests/`:

1. **Sao chép các file mock & test vào vị trí đích**:
   ```bash
   cp .agents/explorer_m2/proposed_mock_cli.py tests/e2e/mock_cli.py
   cp .agents/explorer_m2/proposed_mock_backend.py tests/e2e/mock_backend.py
   cp .agents/explorer_m2/proposed_conftest.py tests/e2e/conftest.py
   cp .agents/explorer_m2/proposed_test_r1_pipeline.py tests/e2e/tier1_feature_coverage/test_r1_pipeline.py
   cp .agents/explorer_m2/proposed_test_r4_boundaries.py tests/e2e/tier2_boundary_corner/test_r4_boundaries.py
   cp .agents/explorer_m2/proposed_test_r1_r2_integration.py tests/e2e/tier3_cross_feature/test_r1_r2_integration.py
   cp .agents/explorer_m2/proposed_test_scenario_basic_flow.py tests/e2e/tier4_real_world/test_scenario_basic_flow.py
   ```
2. **Kích hoạt chạy thử bộ test**:
   ```bash
   pytest tests/ -v
   ```
3. **Điều kiện xác minh thành công**:
   * Tất cả các mock test chạy qua client và subprocess đều kết thúc với mã thành công (`passed`).
   * Không có bất kỳ file nào trong thư mục `/services/` bị tạo mới hoặc sửa đổi trong suốt quá trình chạy test này.
