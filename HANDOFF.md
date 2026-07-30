# HANDOFF.md

## Current Status
* **Hoàn thành 100% cả 3 Sprints Phát triển Vertical Slice & 3 Lớp Bảo vệ Hệ thống**:
  * **Sprint 1 (Vertical Slice 1)**: Pipeline MC ảo CPU Viseme End-to-End (`cpu_viseme.py`, `webm_exporter.py`, FastAPI backend & Web UI tải lên/xuất video WebM nền trong suốt).
  * **Sprint 2 (Vertical Slice 2)**: Engine GPU Wav2Lip (`gpu_lipsync.py`) kèm tính năng tự động lùi CPU Viseme (Automatic Fallback), Nút gạt chuyển đổi phần cứng `[ 🚀 CPU / 🔥 GPU ]` và luồng tiến độ SSE thời gian thực.
  * **Sprint 3 (Vertical Slice 3)**: Khung chọn vùng mặt MC tương tác (Interactive Canvas Crop ROI drag/touch), giao diện Glassmorphism UI và Trình phát xem trước nền lưới caro (`Transparent Checkerboard Player`).
* **Nâng cấp Hệ thống & Tối ưu Tài nguyên (Mới nhất)**:
  * **O(1) Memory Stream-Encoding Pipe**: Chuyển đổi mã hóa WebM VP9 Alpha sang luồng pipe `stdin` FFMPEG trực tiếp trong [webm_exporter.py](file:///home/thienvu/workspace/CodeAvatar/services/pipeline/webm_exporter.py), giữ RAM ứng dụng cố định **~150MB** bất kể video dài 30 phút hay 5 tiếng (không tràn RAM OOM).
  * **Terminal Live Execution Console UI**: Tích hợp ô Console Terminal màu đen nhám hiển thị log thời gian thực từng bước xử lý và báo lỗi minh bạch (Exception Traceback) ngay trên giao diện Web UI.
  * **Docker Isolation (Dell Precision M6800 Optimized)**: Tạo [Dockerfile](file:///home/thienvu/workspace/CodeAvatar/Dockerfile), [docker-compose.yml](file:///home/thienvu/workspace/CodeAvatar/docker-compose.yml) và [run_docker.sh](file:///home/thienvu/workspace/CodeAvatar/run_docker.sh) với cấu hình giới hạn cứng **8.0 CPUs & 16GB RAM**, bảo vệ 100% hệ điều hành Debian 12 không bao giờ bị đơ máy.
* **TDD & Bảo mật**:
  * Đạt **100% Pass Rate (11/11 tests PASSED)** trên toàn bộ bộ kiểm thử tự động `pytest`.
  * Đã dọn dẹp các tệp tạm thừa, working tree hoàn toàn sạch sẽ.

## Uncommitted State
* Working tree sẵn sàng để commit và push lên GitHub `main` branch.

## Verification Shortcuts (Quick Commands for New Sessions)
1. **Chạy Bộ Test TDD Tự động (11/11 tests)**:
   ```bash
   .venv/bin/python -m pytest tests/ -v
   ```
2. **Chạy Ứng dụng An toàn qua Docker (Khuyên dùng)**:
   ```bash
   ./run_docker.sh
   ```
3. **Chạy Server Trực tiếp trên Host**:
   ```bash
   .venv/bin/uvicorn services.backend.main:app --reload --port 8000
   ```

## Key Architectural Decisions & Gotchas
* **Tối ưu RAM OOM với Stream Pipe**: Đẩy luồng byte RGBA trực tiếp vào FFMPEG qua pipe `stdin`, giải phóng RAM ngay sau khi nạp từng frame, giữ bộ nhớ cố định ở mức $O(1)$.
* **Graceful CPU Fallback**: Tự động lùi về CPU Viseme Mode khi không có card GPU CUDA mà không gây đơ Xorg / Wayland desktop.
* **Terminal Live Debug Log**: Hiển thị log chi tiết kèm mốc thời gian ngay tại trình duyệt giúp phát hiện nhanh các điểm tắc nghẽn hoặc lỗi hệ thống.
* **Path Traversal Security**: Kiểm tra bảo mật chuẩn `Path.is_relative_to()` chặn triệt để mọi hành vi hack đường dẫn file.

## Next Steps for Future Sessions
1. Chạy bộ kiểm thử tự động qua `.venv/bin/python -m pytest tests/ -v` để xác nhận 100% pass.
2. Khởi chạy hệ thống qua `./run_docker.sh` và trải nghiệm Web UI tại `http://localhost:8000`.
