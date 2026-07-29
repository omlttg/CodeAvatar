# HANDOFF.md

## Current status
* **Đã hoàn thành 100% cả 3 Sprint phát triển lát cắt dọc (Vertical Slices MVP)**:
  * **Sprint 1 (Vertical Slice 1)**: Hoàn thành End-to-End CPU Viseme Avatar Pipeline (`cpu_viseme.py`, `webm_exporter.py`, FastAPI backend & Web UI upload/download).
  * **Sprint 2 (Vertical Slice 2)**: Hoàn thành GPU Wav2Lip Engine (`gpu_lipsync.py`) với tính năng tự động lùi CPU, Nút gạt Hardware Switch `[ GPU / CPU ]` và SSE progress stream.
  * **Sprint 3 (Vertical Slice 3)**: Hoàn thành Interactive Crop ROI Canvas, Glassmorphic UI polish và Transparent Checkerboard Video Preview Player.
* **Kiểm thử TDD & Bảo mật**:
  * Đạt tỷ lệ vượt qua **100% (11/11 tests PASSED)** trên toàn bộ test suite.
  * Đã qua bài kiểm tra quét bảo mật tĩnh **Semgrep Scan với 0 lỗ hổng (0 findings)**.
* **Tài liệu hệ thống**: Đã đồng bộ toàn bộ sơ đồ Mermaid, [PROJECT.md](file:///home/thienvu/workspace/CodeAvatar/PROJECT.md), [ARCHITECTURE.md](file:///home/thienvu/workspace/CodeAvatar/ARCHITECTURE.md) và GitHub Issues (#1, #2, #3).

## Uncommitted state
* Clean working tree. Toàn bộ mã nguồn đã được commit và push thành công lên nhánh `main` trên GitHub.

## Verification Shortcuts (Lệnh chạy test nhanh cho phiên mới)
1. **Chạy toàn bộ bài test TDD (11/11 tests)**:
   ```bash
   .venv/bin/python -m pytest tests/ -v
   ```
2. **Quét bảo mật tĩnh Semgrep Scan**:
   ```bash
   semgrep scan --config=auto services/
   ```
3. **Chạy Server Local trọn gói**:
   ```bash
   .venv/bin/uvicorn services.backend.main:app --reload --port 8000
   ```

## Gotchas/New decisions
* **Tối ưu Laptop Văn Phòng**: Chế độ CPU Viseme ghép khẩu hình tĩnh siêu tốc trong 2-5 giây với lượng RAM tiêu thụ < 2GB.
* **Tự động lùi về CPU**: Khi chọn chế độ GPU Wav2Lip trên máy không có CUDA, hệ thống tự động cảnh báo và lùi về CPU Viseme an toàn không làm crash server.
* **Bảo mật Path Traversal**: Đã áp dụng kiểm tra nghiêm ngặt `Path.is_relative_to()` trên tất cả các endpoint tải file.

## Next steps for New Session
1. Chạy bài test toàn diện bằng lệnh `.venv/bin/python -m pytest tests/ -v` để nghiệm thu 11/11 bài test.
2. Khởi chạy server local `.venv/bin/uvicorn services.backend.main:app --reload --port 8000` và mở `http://localhost:8000` để trải nghiệm trực quan.
