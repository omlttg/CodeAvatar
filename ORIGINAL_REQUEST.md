# Original User Request

## Initial Request — 2026-07-15T22:17:24Z

CodeAvatar is a hybrid-compute AI avatar generation and automated video dubbing tool designed for lecture videos (Google Meet). It converts original lecture videos into dubbed videos with lip-synced transparent-background virtual MC presenters and synchronized timelines.

Working directory: `/home/thienvu/workspace/CodeAvatar`
Integrity mode: development

## Functional Requirements

### R1. Core AI Pipeline
Build a processing pipeline utilizing local AI models: Whisper (STT), Ollama (Bilingual translation with technical glossary integration), Piper/XTTS-v2 (TTS), Wav2Lip & GFPGAN (Lip sync and face restoration). Must enforce GPU VRAM cleanup (`torch.cuda.empty_cache()`) and isolate heavy model tasks inside worker subprocesses (multiprocessing) to prevent memory leaks.

### R2. Dynamic Time Alignment (DTA) & Composition
Synchronize audio and video tracks by dynamically adjusting TTS speech tempo (preserving vocal pitch via `atempo` filter between 0.85x - 1.25x), inserting silence padding, or applying freeze-frame video padding via FFmpeg.

### R3. Transparent Output & Timeline JSON
Export transparent avatar video layers using WebM VP9 (`yuva420p` + `alpha_mode=1`), `.srt` subtitles with timestamps adjusted according to DTA results, and `timeline_shifts.json` recording slide timing deltas for Google Vids integration.

### R4. FastAPI Backend & Database
Build a FastAPI API backend orchestrating processing jobs sequentially via a background FIFO queue to prevent concurrent GPU VRAM exhaustion. Persist job metadata and segment states in SQLite Database (WAL mode). Enforce canonical path checking on download endpoints to block Path Traversal attacks.

### R5. Aesthetic Web UI & Drive Sync
Construct a modern, responsive Web UI using React + Vite (Glassmorphic dark mode styling). Support debounced script editing for bilingual subtitles, real-time log monitoring via Server-Sent Events (SSE), and Google Identity Services (OAuth 2.0) storing tokens in HttpOnly cookies for resumable file uploads to Google Drive.

## Acceptance Criteria

### Verification & Automated Tests
- [x] Build automated unit test suites under `/tests` covering AI pipeline modules (Whisper, Translator, DTA) and FastAPI backend endpoints.
- [x] Execute `pytest` achieving a 100% pass rate.

### Core Pipeline CLI
- [x] CLI script `pipeline_cli.py` executes end-to-end processing from original video to dubbed output.
- [x] Dockerfile with GPU acceleration support (`Dockerfile.pipeline`) packages independent CLI pipeline execution.
- [x] Release GPU VRAM completely after each model processing phase (VRAM fragmented < 5%).

### Dynamic Time Alignment & WebM Export
- [x] Dubbed avatar voice output preserves natural pitch without chipmunk distortion.
- [x] Transparent WebM VP9 avatar video correctly renders Alpha channel without black background artifacts.
- [x] Exported `timeline_shifts.json` adheres to schema, and `.srt` file timestamps match DTA output.

### FastAPI & Web UI
- [x] FastAPI prevents RAM overflow during large file uploads via disk-buffering stream handlers.
- [x] Sequential FIFO processing queue runs 1 AI job at a time to protect GPU resources.
- [x] Web UI connects to backend endpoints, renders SSE progress logs, and updates script edits.
- [x] Google Drive OAuth 2.0 integration securely uploads resulting video artifacts.
