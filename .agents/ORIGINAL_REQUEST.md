## 2026-07-15T22:17:24Z

CodeAvatar là một công cụ hybrid-compute AI avatar và lồng tiếng tự động cho video bài giảng (Google Meet), chuyển đổi video tiếng Việt gốc thành video lồng tiếng Anh/Hàn có MC ảo nền trong suốt đồng bộ khẩu hình và timeline.

Working directory: /home/thienvu/workspace/CodeAvatar
Integrity mode: development

## Requirements

### R1. Core AI Pipeline
Xây dựng pipeline xử lý chạy qua các mô hình local: Whisper (STT), Ollama (Dịch thuật tích hợp glossary thuật ngữ kỹ thuật), Piper/XTTS-v2 (TTS), Wav2Lip & GFPGAN (Nhép môi và làm nét khuôn mặt MC). Phải dọn dẹp GPU VRAM (`torch.cuda.empty_cache()`) và chạy các module AI nặng dưới dạng tiến trình con biệt lập (multiprocessing) để tránh rò rỉ bộ nhớ.

### R2. Dynamic Time Alignment (DTA) & Composition
Đồng bộ hóa âm thanh và hình ảnh của video bài giảng bằng cách tự động co giãn tốc độ nói của TTS (giữ nguyên pitch giọng bằng atempo filter từ 0.85x - 1.25x), chèn khoảng lặng (Silence Padding) hoặc chèn freeze frames vào video bài giảng gốc bằng FFMPEG (Video Padding).

### R3. Transparent Output & Timeline JSON
Xuất ra video MC ảo nền trong suốt sử dụng WebM VP9 (hỗ trợ alpha channel `yuva420p` và `alpha_mode=1`), phụ đề `.srt` đã hiệu chỉnh timestamps theo DTA, và file `timeline_shifts.json` mô tả timing delta để import vào Google Vids.

### R4. FastAPI Backend & Database
Xây dựng API Backend sử dụng FastAPI điều phối công việc xử lý tuần tự qua hàng đợi (Background Queue) để tránh chạy song song gây tràn GPU VRAM. Lưu trữ thông tin job và segment trong SQLite Database (WAL mode). API download phải kiểm tra tính hợp lệ của path để chống tấn công Path Traversal.

### R5. Aesthetic Web UI & Drive Sync
Xây dựng giao diện Web UI bằng React + Vite tối giản, hiện đại (glassmorphic dark mode). Hỗ trợ sửa kịch bản dịch song ngữ (Script Editor) với cơ chế Debounce, theo dõi log render thời gian thực qua Server-Sent Events (SSE), và tích hợp Google Identity Services (OAuth 2.0) lưu token trong HttpOnly Cookie để đồng bộ file lên Google Drive qua cơ chế Resumable Upload.

## Acceptance Criteria

### Verification & Automated Tests
- [ ] Xây dựng bộ unit tests tự động dưới thư mục `/tests` phủ sóng 100% các module AI (Whisper, Translator, DTA) và API backend FastAPI.
- [ ] Chạy lệnh `pytest` phải vượt qua 100% bài test thành công (Pass rate 100%).

### Core Pipeline CLI
- [ ] Script CLI `pipeline_cli.py` chạy thành công end-to-end từ video gốc ra video dịch lồng tiếng thô.
- [ ] Đóng gói thành công Dockerfile hỗ trợ GPU (`Dockerfile.pipeline`) giúp chạy CLI pipeline độc lập trên máy chủ.
- [ ] Giải phóng GPU VRAM hoàn toàn sau mỗi bước xử lý mô hình (VRAM Fragmented < 5%).

### Dynamic Time Alignment & WebM Export
- [ ] Đoạn video đầu ra của MC ảo khi lồng tiếng Anh không bị thay đổi pitch âm thanh (không bị giọng sóc chuột).
- [ ] Video MC ảo nền trong suốt định dạng WebM VP9 hiển thị đúng kênh alpha (không bị nền đen khi chạy trên trình duyệt).
- [ ] File `timeline_shifts.json` xuất đúng định dạng quy định và file `.srt` khớp chính xác thời lượng DTA.

### FastAPI & Web UI
- [ ] FastAPI không bị tràn RAM khi upload video Meet dung lượng lớn nhờ cơ chế stream disk-buffering.
- [ ] Hàng đợi xử lý tuần tự (FIFO) chỉ chạy 1 job AI tại một thời điểm để bảo vệ GPU.
- [ ] Web UI kết nối thành công API, hiển thị log SSE trực quan và thực hiện sửa đổi phụ đề thành công.
- [ ] Đồng bộ hóa Google Drive OAuth 2.0 tải lên các file kết quả thành công và an toàn.
