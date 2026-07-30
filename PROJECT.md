# Project: CodeAvatar System Design (Dual-Engine MC Avatar Generator)

## Architecture Overview
**CodeAvatar** được thiết kế theo mô hình kiến trúc cắt dọc **Vertical Slice Architecture** trải qua 3 Sprints phát triển chính kết hợp các nâng cấp tối ưu hệ thống:
1. **Vertical Slice 1 (Sprint 1)**: Luồng CPU Viseme End-to-End (Web UI Upload + FastAPI Backend + CPU Viseme Engine 2-5s + Tải WebM VP9 Alpha nền trong suốt).
2. **Vertical Slice 2 (Sprint 2)**: Luồng GPU Wav2Lip CUDA Engine + Công tắc chuyển phần cứng `[ 🚀 CPU / 🔥 GPU ]` + Luồng SSE cập nhật tiến độ thời gian thực + Tự động lùi về CPU khi thiếu CUDA GPU.
3. **Vertical Slice 3 (Sprint 3)**: Khung chọn vùng khuôn mặt tương tác Crop ROI Canvas + Giao diện Glassmorphism UI + Trình phát xem trước nền lưới caro (`Transparent Checkerboard Player`).
4. **System Protection & Performance Upgrade**: Cơ chế Stream-Encoding Pipe bộ nhớ $O(1)$ ~150MB + Cửa sổ Terminal Live Console Log trên Web UI + Đóng gói Docker cô lập (8 CPUs / 16GB RAM).

## Code Layout
```text
/home/thienvu/workspace/CodeAvatar
  ├── Dockerfile                 # Container Debian cô lập tài nguyên cho CodeAvatar
  ├── docker-compose.yml         # Cấu hình Docker giới hạn 8.0 CPUs & 16GB RAM
  ├── run_docker.sh              # Script thực thi build & chạy container an toàn
  ├── requirements.txt           # Khai báo phụ thuộc Python
  ├── /services
  │    └── /pipeline          # Core Rendering Engines (CPU Viseme & GPU Wav2Lip)
  │         ├── cpu_viseme.py
  │         ├── gpu_lipsync.py
  │         └── webm_exporter.py
  │    └── /backend           # Backend FastAPI Job Orchestrator & Web UI
  │         └── main.py
  ├── /tests                  # Bộ kiểm thử tự động TDD (11/11 Passed)
  ├── README.md               # Tài liệu hướng dẫn chính
  ├── PROJECT.md              # Thiết kế tổng quan hệ thống
  ├── ARCHITECTURE.md         # Kiến trúc kỹ thuật chi tiết
  ├── TEST_INFRA.md           # Hướng dẫn hạ tầng kiểm thử
  └── HANDOFF.md              # Nhật ký bàn giao ngữ cảnh phát triển
```

## Milestones (Vertical Slices)
| # | Sprint Name | Scope (Vertical Slice End-to-End) | Status |
|---|-------------|-----------------------------------|--------|
| 1 | Basic End-to-End CPU Viseme Avatar Pipeline (Vertical Slice 1) | Web UI Upload + FastAPI Backend + CPU Viseme Engine (2-5s) + Tải video WebM VP9 Alpha. | COMPLETED |
| 2 | High-Quality GPU Wav2Lip & Hardware Switch (Vertical Slice 2) | Nút gạt phần cứng `[ CPU / GPU ]` + GPU Wav2Lip CUDA Engine + SSE Stream + Tự động lùi CPU. | COMPLETED |
| 3 | Interactive Crop ROI Canvas & Glassmorphic UI Polish (Vertical Slice 3) | Khung chọn vùng mặt MC Crop ROI Canvas + Player nền lưới caro + Glassmorphism UI. | COMPLETED |
| 4 | Stream Encoding Pipe & System Isolation | Stream-Encoding Pipe bộ nhớ $O(1)$ ~150MB + Terminal Live Execution Console Log + Container Docker (8 CPUs / 16GB RAM). | COMPLETED |

## Interface Contracts
### Input / Output
- **Đầu vào (Inputs)**: File Audio (`.wav` / `.mp3`), Mẫu ảnh chân dung MC (`.png` / `.jpg`), Tọa độ khung Crop ROI, Chế độ phần cứng (`cpu_viseme` / `gpu_wav2lip`).
- **Đầu ra (Outputs)**: Video MC ảo nền trong suốt định dạng WebM VP9 (`yuva420p` + `alpha_mode=1`).

### FastAPI API Endpoints
- `POST /api/generate-avatar`: Nhận audio & ảnh MC + tọa độ crop + `mode`. Trả về `job_id`.
- `GET /api/jobs/{job_id}/stream`: Luồng Server-Sent Events (SSE) phát tiến độ và log thời gian thực về Web UI.
- `GET /api/jobs/{job_id}/download`: Tải file WebM Alpha kết quả.
