# Project: CodeAvatar System Design (Dual-Engine MC Avatar Generator)

## Architecture Overview
CodeAvatar được thiết kế thành một ứng dụng lai (hybrid) đa chế độ render, chia thành 3 Sprint theo mô hình **lát cắt dọc hoàn chỉnh (Vertical Slices)**:
1. **Vertical Slice 1 (Sprint 1)**: End-to-End CPU Viseme Pipeline (Web UI + FastAPI + Engine Viseme 2-5s + WebM Alpha download).
2. **Vertical Slice 2 (Sprint 2)**: End-to-End GPU Wav2Lip CUDA Engine + Hardware Switch `[ GPU / CPU ]` + SSE Real-time Progress Stream.
3. **Vertical Slice 3 (Sprint 3)**: End-to-End Interactive Crop ROI Canvas + Glassmorphic UI Polish + Transparent Checkerboard Preview.

## Code Layout
```text
/home/thienvu/workspace/CodeAvatar
  ├── /apps
  │    └── /web               # Web UI 1-Page (React/Vite) với Hardware Switch (GPU/CPU) & Crop ROI Canvas
  ├── /services
  │    └── /pipeline          # Engine Render (CPU Viseme & GPU Wav2Lip)
  │         ├── cpu_viseme.py
  │         ├── gpu_lipsync.py
  │         └── webm_exporter.py
  │    └── /backend           # Backend FastAPI điều phối jobs
  │         └── main.py
  ├── /tests                  # Bộ kiểm thử tự động (Unit, Integration & E2E tests)
  ├── PROJECT.md              # Tài liệu thiết kế hệ thống tổng quan
  ├── ORIGINAL_REQUEST.md     # Nhật ký yêu cầu ban đầu
  └── HANDOFF.md              # Nhật ký bàn giao tiến độ
```

## Milestones (Vertical Slices)
| # | Sprint Name | Scope (Vertical Slice End-to-End) | Dependencies | Status |
|---|-------------|-----------------------------------|--------------|--------|
| 1 | Basic End-to-End CPU Viseme Avatar Pipeline (Vertical Slice 1) | Web UI Upload + FastAPI API + Engine CPU Viseme (2-5s) + FFMPEG VP9 Alpha WebM download. Tối ưu cho mọi laptop văn phòng. | None | PLANNED |
| 2 | High-Quality GPU Wav2Lip & Hardware Switch (Vertical Slice 2) | Hardware Switch `[ GPU / CPU ]` + Engine GPU Wav2Lip CUDA + SSE Real-time Progress Stream + Tự động lùi CPU nếu thiếu GPU. | Sprint 1 | PLANNED |
| 3 | Interactive Crop ROI Canvas & Glassmorphic UI Polish (Vertical Slice 3) | Canvas Crop ROI chọn vị trí mặt MC + Player xem trước nền lưới caro trong suốt + Đánh bóng giao diện Glassmorphism. | Sprint 2 | PLANNED |

## Interface Contracts
### Input / Output
- Đầu vào: File Audio (`.wav`/`.mp3`), Mẫu MC (`.png`/`.jpg` hoặc `.mp4`), Khung tọa độ Crop ROI, Chế độ Render (`cpu_viseme` / `gpu_wav2lip`).
- Đầu ra: Layer Video MC ảo nền trong suốt chuẩn WebM VP9 (`yuva420p` + `alpha_mode=1`).

### FastAPI API Endpoints
- `POST /api/generate-avatar`: Upload audio & mẫu MC + tọa độ crop + `mode` (`cpu_viseme` | `gpu_wav2lip`). Trả về Job ID.
- `GET /api/jobs/{job_id}/stream`: Luồng log tiến độ thời gian thực (SSE stream).
- `GET /api/jobs/{job_id}/download`: Tải file WebM nền trong suốt.
