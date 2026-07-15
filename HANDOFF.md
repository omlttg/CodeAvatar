# HANDOFF.md

## Current status
* Đã hoàn thành bước **Design & Align (Step 1)**: Thống nhất lộ trình phát triển CodeAvatar thành 5 Sprint lát cắt dọc (Vertical Slices).
* Đã cấu hình và cập nhật [.gitignore](file:///home/thienvu/workspace/CodeAvatar/.gitignore) để bỏ qua các file tài liệu private (`AGENT.md`, `ARCHITECTURE.md`) và thư mục `bin/` chứa portable binary của GitHub CLI.
* Đã đẩy thành công 5 Issue PRD tương ứng với 5 Sprint lên GitHub repo [omlttg/CodeAvatar](https://github.com/omlttg/CodeAvatar/issues) (Issue #1 đến #5).
* Đã khởi tạo cấu trúc thư mục [/services/pipeline](file:///home/thienvu/workspace/CodeAvatar/services/pipeline) và viết các module cốt lõi ban đầu của Sprint 1 (`transcriber.py`, `translator.py`, `tts.py`, `glossary.json`).

## Uncommitted state
* File [.gitignore](file:///home/thienvu/workspace/CodeAvatar/.gitignore) đã sửa đổi (chờ commit).
* Các file mã nguồn mới trong [/services/pipeline/](file:///home/thienvu/workspace/CodeAvatar/services/pipeline) đang ở trạng thái `untracked`.

## Gotchas/New decisions
* Thống nhất 30 điểm tối ưu "chí huyệt" cho toàn hệ thống sản xuất thực tế (ví dụ: VRAM offloading qua Python Multiprocessing, chunking video cho Wav2Lip chống tràn bộ nhớ, và pixel format yuva420p cho WebM alpha).
* Triển khai Docker-first hoàn toàn cho Pipeline AI để tránh xung đột thư viện CUDA/C++ local của Wav2Lip.

## Next steps
1. Thực hiện commit các thay đổi hiện tại (file `.gitignore`, `HANDOFF.md`, và các file code ban đầu) lên nhánh `main`.
2. Bắt đầu **Sprint 1: Basic End-to-End CLI Pipeline** (viết script `pipeline_cli.py`, đóng gói `Dockerfile.pipeline`, viết test suite và chạy thử nghiệm thực tế).
