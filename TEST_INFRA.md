# TEST_INFRA — E2E Testing Infrastructure Specification

This document details the testing philosophy, 4-tier test suite hierarchy, feature breakdown, and execution guide for the **CodeAvatar** project.

---

## 1. Testing Philosophy

CodeAvatar's E2E test infrastructure follows an **Opaque-Box Testing** paradigm:
* **Requirements-Driven:** Tests are mapped directly against functional requirements (R1 through R5) rather than implementation details.
* **User-Centric Interactions:** Tests simulate end-user behaviors through `pipeline_cli.py` CLI invocations and FastAPI backend endpoints.
* **Deterministic Assertions:** Ensures output artifacts (transparent WebM videos, `.srt` subtitles, `timeline_shifts.json`) conform to specification schemas and security constraints.
* **VRAM & Resource Monitoring:** Tracks GPU VRAM and system memory allocation during test execution to prevent memory leaks.

---

## 2. 4-Tier Test Directory Structure

The E2E test suite resides within `/tests/e2e/` organized into 4 distinct tiers:

```text
/home/thienvu/workspace/CodeAvatar/
  ├── tests/
  │    ├── conftest.py                   # Global pytest fixtures and configurations
  │    └── e2e/
  │         ├── conftest.py              # External API mocks (Google Drive, offline servers)
  │         ├── tier1_feature_coverage/  # Tier 1: Isolated feature coverage (>=5 cases/feature)
  │         │    ├── test_r1_pipeline.py
  │         │    ├── test_r2_dta.py
  │         │    ├── test_r3_outputs.py
  │         │    ├── test_r4_backend.py
  │         │    └── test_r5_web_ui.py
  │         ├── tier2_boundary_corner/   # Tier 2: Boundary and edge case handling (>=5 cases/feature)
  │         │    ├── test_r1_boundaries.py
  │         │    ├── test_r2_boundaries.py
  │         │    ├── test_r3_boundaries.py
  │         │    ├── test_r4_boundaries.py
  │         │    └── test_r5_boundaries.py
  │         ├── tier3_cross_feature/     # Tier 3: Cross-feature interaction testing
  │         │    ├── test_r1_r2_integration.py
  │         │    ├── test_r2_r3_integration.py
  │         │    ├── test_r1_r4_integration.py
  │         │    ├── test_r4_r5_integration.py
  │         │    └── test_r3_r5_integration.py
  │         └── tier4_real_world/        # Tier 4: End-to-End real-world integration scenarios
  │              ├── test_scenario_basic_flow.py
  │              ├── test_scenario_slide_freeze.py
  │              ├── test_scenario_hybrid_mode.py
  │              ├── test_scenario_resumable_upload.py
  │              └── test_scenario_adversarial_vram.py
```

---

## 3. Feature Mapping & Test Cases

The table below maps the 5 core functional requirements (R1 - R5) to their corresponding E2E test suites:

### R1. Core AI Pipeline
* **F1.1 Noise Suppression (DeepFilterNet):** Audio signal denoising.
* **F1.2 Speaker Diarization (pyannote-audio):** Speaker segment identification.
* **F1.3 Speech-to-Text (Whisper):** Vietnamese STT transcription with word-level timestamps.
* **F1.4 Translation (Ollama):** Bilingual translation enriched with technical terms glossary.
* **F1.5 Text-to-Speech (Piper / Coqui XTTS-v2):** Synchronized English/Korean voice synthesis.
* **F1.6 Lip-Sync & Face Restoration (Wav2Lip + GFPGAN):** Avatar lip synchronization and face enhancement.
* **F1.7 GPU Memory Protection:** GPU VRAM cleanup using `torch.cuda.empty_cache()` and isolated worker subprocesses.
* *Key Test Cases:*
  * `tier1_feature_coverage/test_r1_pipeline.py::test_whisper_transcription`
  * `tier1_feature_coverage/test_r1_pipeline.py::test_ollama_translator_with_glossary`
  * `tier1_feature_coverage/test_r1_pipeline.py::test_vram_cleanup_after_unload`
  * `tier2_boundary_corner/test_r1_boundaries.py::test_empty_audio_transcription`

### R2. Dynamic Time Alignment (DTA) & Composition
* **F2.1 Audio Time-Stretching:** Dynamic speech tempo adjustment (0.85x - 1.25x) maintaining pitch via `atempo` filter.
* **F2.2 Silence Padding:** Automatic silence insertion when translated audio is shorter than original video.
* **F2.3 Video Padding (Freeze Frames):** Automatic freeze-frame insertion when translation is longer than original video.
* **F2.4 VFR to CFR Transcoding:** Video frame rate normalization to Constant Frame Rate via FFmpeg.
* *Key Test Cases:*
  * `tier1_feature_coverage/test_r2_dta.py::test_audio_time_stretching_within_limits`
  * `tier1_feature_coverage/test_r2_dta.py::test_video_padding_freeze_frames`

### R3. Transparent Output & Timeline JSON
* **F3.1 Transparent WebM VP9 Layer:** Transparent avatar video layer export (alpha channel, `yuva420p`, `alpha_mode=1`).
* **F3.2 Aligned SRT Subtitles:** `.srt` subtitle timestamp alignment following DTA processing.
* **F3.3 Timeline Shifts JSON:** `timeline_shifts.json` file export recording timing deltas for Google Vids integration.
* *Key Test Cases:*
  * `tier1_feature_coverage/test_r3_outputs.py::test_transparent_webm_alpha_channel`
  * `tier1_feature_coverage/test_r3_outputs.py::test_timeline_shifts_json_format`

### R4. FastAPI Backend & Database
* **F4.1 Job Creation Endpoint (`POST /api/jobs`):** Disk-buffering stream upload to prevent memory spikes.
* **F4.2 Job Status & SSE Log Stream:** Endpoint `GET /api/jobs/{id}/logs/stream` returning real-time progress events.
* **F4.3 FIFO Queue Orchestration:** Sequential AI job execution protecting GPU resources.
* **F4.4 SQLite WAL Mode Storage:** Job metadata and segment state persistence via SQLite WAL mode.
* **F4.5 Path Traversal Defenses:** Path traversal attack mitigations on file download endpoints.
* *Key Test Cases:*
  * `tier1_feature_coverage/test_r4_backend.py::test_create_job_endpoint`
  * `tier2_boundary_corner/test_r4_boundaries.py::test_path_traversal_attack_variations`

### R5. Aesthetic Web UI & Drive Sync
* **F5.1 Glassmorphic Dark Mode UI:** Modern user dashboard and script editing interface.
* **F5.2 Debounced Script Editor:** Debounced subtitle script editing and autosave.
* **F5.3 Google OAuth 2.0 via HttpOnly Cookie:** Secure authentication token management.
* **F5.4 Google Drive Resumable Upload:** Large file upload to Google Drive with minimal `drive.file` scope.

---

## 4. Test Execution Guide

### Prerequisites
* Python 3.10+
* Pytest (`pip install pytest pytest-asyncio pytest-cov`)
* FFmpeg (compiled with `libvpx` VP9 support)
* SQLite3

### Execution Commands

1. **Run Full Test Suite (Tiers 1 - 4):**
   ```bash
   pytest tests/ -v
   ```

2. **Run Individual Test Tiers:**
   * **Tier 1 (Feature Coverage):**
     ```bash
     pytest tests/e2e/tier1_feature_coverage/ -v
     ```
   * **Tier 2 (Boundary & Corner Cases):**
     ```bash
     pytest tests/e2e/tier2_boundary_corner/ -v
     ```

3. **Run Specific Feature Tests (e.g., R4 Backend):**
   ```bash
   pytest -k "r4" -v
   ```

4. **Generate Coverage Report:**
   ```bash
   pytest --cov=services --cov=apps tests/ -v
   ```
