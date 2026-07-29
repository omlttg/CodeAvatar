## 2026-07-16T06:36:37Z
Bạn là E2E Test Implementer cho dự án CodeAvatar.
Working directory của bạn là: /home/thienvu/workspace/CodeAvatar/.agents/worker_m2/
Mục tiêu của bạn:
1. Sao chép và hoàn thiện hạ tầng mock kiểm thử từ thư mục `/home/thienvu/workspace/CodeAvatar/.agents/explorer_m2/`:
   - `proposed_mock_cli.py` -> Lưu thành `tests/e2e/mock_cli.py`
   - `proposed_mock_backend.py` -> Lưu thành `tests/e2e/mock_backend.py`
   - `proposed_conftest.py` -> Lưu thành `tests/e2e/conftest.py`
2. Triển khai đầy đủ 60 test cases E2E (Tier 1 đến Tier 4) trong các file dưới thư mục `tests/e2e/`. Các test cases này phải sử dụng FastAPI TestClient hoặc gọi CLI qua subprocess thực tế (được intercept bởi fixture). Dưới đây là danh sách chi tiết các file và test cases cần tạo:

* Thư mục `tests/e2e/tier1_feature_coverage/`:
  - `test_r1_pipeline.py`: (5 cases)
    1. `test_whisper_transcription`: Whisper trích xuất văn bản + word-level timestamps (mock whisper model).
    2. `test_ollama_translator_with_glossary`: Ollama dịch song ngữ áp dụng Glossary (mock urlopen).
    3. `test_piper_tts_generation`: Piper sinh file âm thanh WAV (mock subprocess Popen).
    4. `test_vram_cleanup_after_unload`: Giải phóng GPU cache sau unload model (mock empty_cache).
    5. `test_noise_suppression_and_diarization`: Chạy DeepFilterNet và pyannote-audio (mock tương ứng).
  - `test_r2_dta.py`: (5 cases)
    6. `test_audio_time_stretching_within_limits`: Co giãn tốc độ âm thanh (0.85x - 1.25x).
    7. `test_video_padding_freeze_frames`: Chèn freeze frame.
    8. `test_silence_padding`: Chèn khoảng lặng.
    9. `test_vfr_to_cfr_transcoding`: FFMPEG chuẩn hóa video CFR.
    10. `test_dta_duration_deltas`: Tính toán chính xác delta slide duration.
  - `test_r3_outputs.py`: (5 cases)
    11. `test_transparent_webm_alpha_channel`: Xuất WebM VP9 kênh alpha.
    12. `test_srt_subtitle_sync`: Đồng bộ `.srt` theo timestamps DTA.
    13. `test_timeline_shifts_json_format`: Kiểm tra định dạng timeline_shifts JSON.
    14. `test_separate_layers_output`: Xuất các file layer riêng lẻ (video, audio, srt).
    15. `test_metadata_injection`: Ghi cấu hình metadata vào file.
  - `test_r4_backend.py`: (5 cases)
    16. `test_create_job_endpoint`: POST `/api/jobs` nhận file và lưu SQLite DB.
    17. `test_get_job_status`: GET `/api/jobs/{id}` trả về trạng thái.
    18. `test_fifo_queue_sequential_execution`: FIFO queue xử lý tuần tự job.
    19. `test_sqlite_wal_mode_enabled`: SQLite WAL mode.
    20. `test_sse_log_stream_endpoint`: GET `/api/jobs/{id}/logs/stream` trả về SSE logs.
  - `test_r5_web_ui.py`: (5 cases)
    21. `test_script_editor_debouncing`: Debouncing UI gửi cập nhật script.
    22. `test_google_oauth_cookie_verification`: OAuth qua HttpOnly Cookie.
    23. `test_google_drive_resumable_upload`: Tải lên Google Drive theo chunk bằng scope drive.file (mock drive api).
    24. `test_glassmorphic_ui_elements`: Kiểm tra sự tồn tại của CSS Glassmorphic.
    25. `test_drive_sync_status`: Cập nhật trạng thái đồng bộ Drive lên SQLite.

* Thư mục `tests/e2e/tier2_boundary_corner/`:
  - `test_r1_boundaries.py`: (5 cases)
    26. `test_empty_audio_transcription`: Whisper xử lý âm thanh trống không crash.
    27. `test_ollama_unresponsive_fallback`: Fallback giữ nguyên khi Ollama mất kết nối.
    28. `test_glossary_case_insensitivity`: Glossary hoạt động không phân biệt chữ hoa/thường.
    29. `test_extremely_long_sentence_diarization`: Diarization xử lý hội thoại dài không tràn RAM.
    30. `test_xtts_missing_speaker_reference`: Bắn lỗi khi thiếu file mẫu giọng.
  - `test_r2_boundaries.py`: (5 cases)
    31. `test_dta_extreme_speed_compression`: DTA speed tối đa 1.25x.
    32. `test_dta_extreme_speed_expansion`: DTA speed tối thiểu 0.85x.
    33. `test_dta_zero_duration_segments`: Phân đoạn 0s không chia cho 0.
    34. `test_dta_corrupted_video_cfr_conversion`: FFMPEG xử lý video hỏng không treo.
    35. `test_dta_extremely_long_silence_padding`: Chèn khoảng lặng lớn không tràn tài nguyên.
  - `test_r3_boundaries.py`: (5 cases)
    36. `test_srt_timestamps_overlap`: Timestamps phụ đề không đè chéo nhau.
    37. `test_invalid_avatar_id_paths`: Validate avatar ID không hợp lệ.
    38. `test_timeline_json_empty_shifts`: JSON timing hoạt động đúng khi shifts trống.
    39. `test_webm_alpha_corrupt_frames`: FFMPEG bỏ qua các frame lỗi khi gộp alpha.
    40. `test_srt_unicode_characters`: Phụ đề chứa ký tự đặc biệt/emoji không lỗi font.
  - `test_r4_boundaries.py`: (5 cases)
    41. `test_path_traversal_attack_variations`: Chặn path traversal với `..`, absolute, và hex-encoding.
    42. `test_job_queue_crash_recovery`: Khôi phục queue sau crash server backend.
    43. `test_simultaneous_large_file_uploads`: Upload nhiều file lớn không tăng RAM đột biến.
    44. `test_sse_client_disconnect_handling`: Thu hồi tài nguyên khi client ngắt SSE sớm.
    45. `test_concurrent_job_status_polling`: SQLite chịu tải nhiều truy vấn poll trạng thái cùng lúc.
  - `test_r5_boundaries.py`: (5 cases)
    46. `test_drive_resumable_upload_network_interruption`: Giả lập đứt mạng và resume upload thành công (sử dụng biến môi trường SIMULATE_NETWORK_FAILURE).
    47. `test_expired_oauth_token_refresh`: Gọi refresh token khi hết hạn.
    48. `test_drive_insufficient_space`: Báo lỗi rõ ràng khi Drive hết dung lượng.
    49. `test_script_editor_concurrent_edit_conflict`: Xử lý xung đột khi 2 client sửa script cùng lúc.
    50. `test_drive_invalid_file_permissions`: Chặn và báo lỗi 403 khi thiếu quyền.

* Thư mục `tests/e2e/tier3_cross_feature/`:
  - `test_r1_r2_integration.py` (hoặc tạo file chung): (5 cases)
    51. `test_translation_dta_sync`: R1 Dịch và R2 DTA đồng bộ tốc độ nói.
    52. `test_dta_shift_to_timeline_json_sync`: Thời gian DTA cập nhật vào timeline_shifts.json và .srt.
    53. `test_pipeline_unloading_under_fastapi_load`: API queue quản lý tuần tự pipeline giữ VRAM an toàn dưới tải cao.
    54. `test_script_edit_reprocesses_dta_pipeline`: Sửa kịch bản UI kích hoạt chạy lại DTA trên backend.
    55. `test_alpha_webm_drive_upload_flow`: Xuất WebM và đẩy lên Drive qua resumable upload.

* Thư mục `tests/e2e/tier4_real_world/`:
  - `test_scenario_basic_flow.py` (hoặc tạo file chung): (5 cases)
    56. `test_standard_meet_recording_e2e`: Upload, dịch, xuất WebM + SRT, sync Drive thành công.
    57. `test_long_translation_slide_freeze_e2e`: Bản dịch dài hơn video gốc, chèn freeze frame ở slide cuối.
    58. `test_remote_gpu_worker_audio_only_e2e`: Client trích audio lên Server dịch, tải về tự render.
    59. `test_resumable_large_file_drive_backup_e2e`: Backup file 100MB lên Google Drive đứt mạng liên tục vẫn resume thành công.
    60. `test_concurrent_multi_user_gpu_saturation_e2e`: Stress-test nhiều user submit job, queue xử lý tuần tự, VRAM an toàn.
