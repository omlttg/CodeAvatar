# Project: CodeAvatar System Design (Dual-Engine MC Avatar Generator)

## Architecture Overview
CodeAvatar is designed as a hybrid-compute application supporting dual rendering modes, structured across 3 Sprints using the **Vertical Slice Architecture** model:
1. **Vertical Slice 1 (Sprint 1)**: End-to-End CPU Viseme Pipeline (Web UI + FastAPI + CPU Viseme Engine 2-5s + WebM Alpha download).
2. **Vertical Slice 2 (Sprint 2)**: End-to-End GPU Wav2Lip CUDA Engine + Hardware Switch `[ GPU / CPU ]` + SSE Real-time Progress Stream.
3. **Vertical Slice 3 (Sprint 3)**: End-to-End Interactive Crop ROI Canvas + Glassmorphic UI Polish + Transparent Checkerboard Preview Player.

## Code Layout
```text
/home/thienvu/workspace/CodeAvatar
  ├── /apps
  │    └── /web               # Single-Page Web UI (React/Vite) with Hardware Switch (GPU/CPU) & Crop ROI Canvas
  ├── /services
  │    └── /pipeline          # Rendering Engines (CPU Viseme & GPU Wav2Lip)
  │         ├── cpu_viseme.py
  │         ├── gpu_lipsync.py
  │         └── webm_exporter.py
  │    └── /backend           # Backend FastAPI Job Orchestrator Service
  │         └── main.py
  ├── /tests                  # Automated Test Suite (Unit, Integration & E2E Tests)
  ├── /test                   # Local Test Assets Storage (Git-Ignored)
  ├── README.md               # Main Project Documentation
  ├── PROJECT.md              # System Design Overview
  ├── ARCHITECTURE.md         # Technical Architecture & Interface Contracts
  ├── TEST_INFRA.md           # 4-Tier Test Infrastructure Specification
  ├── ORIGINAL_REQUEST.md     # Initial Requirements Log
  └── HANDOFF.md              # Developer Session Handoff Log
```

## Milestones (Vertical Slices)
| # | Sprint Name | Scope (Vertical Slice End-to-End) | Dependencies | Status |
|---|-------------|-----------------------------------|--------------|--------|
| 1 | Basic End-to-End CPU Viseme Avatar Pipeline (Vertical Slice 1) | Web UI Upload + FastAPI Backend + CPU Viseme Engine (2-5s) + FFmpeg VP9 Alpha WebM download. Optimized for standard office laptops. | None | COMPLETED |
| 2 | High-Quality GPU Wav2Lip & Hardware Switch (Vertical Slice 2) | Hardware Switch `[ GPU / CPU ]` + GPU Wav2Lip CUDA Engine + SSE Real-time Progress Stream + Automatic CPU fallback on missing GPU. | Sprint 1 | COMPLETED |
| 3 | Interactive Crop ROI Canvas & Glassmorphic UI Polish (Vertical Slice 3) | Interactive Canvas Crop ROI face position selector + Transparent checkerboard preview player + Glassmorphism UI Polish. | Sprint 2 | COMPLETED |

## Interface Contracts
### Input / Output
- **Inputs**: Audio file (`.wav` / `.mp3`), Avatar Template (`.png` / `.jpg` or `.mp4`), Crop ROI bounding box coordinates, Render Mode (`cpu_viseme` / `gpu_wav2lip`).
- **Outputs**: Virtual MC Avatar Video Layer with transparent background in standard WebM VP9 format (`yuva420p` + `alpha_mode=1`).

### FastAPI API Endpoints
- `POST /api/generate-avatar`: Upload audio & avatar template + crop coordinates + `mode` (`cpu_viseme` | `gpu_wav2lip`). Returns `job_id`.
- `GET /api/jobs/{job_id}/stream`: Real-time Server-Sent Events (SSE) progress log stream.
- `GET /api/jobs/{job_id}/download`: Download transparent WebM output file.
