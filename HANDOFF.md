# HANDOFF.md

## Current Status
* **Completed 100% of all 3 Vertical Slice Development Sprints**:
  * **Sprint 1 (Vertical Slice 1)**: End-to-End CPU Viseme Avatar Pipeline (`cpu_viseme.py`, `webm_exporter.py`, FastAPI backend & Web UI upload/download).
  * **Sprint 2 (Vertical Slice 2)**: GPU Wav2Lip Engine (`gpu_lipsync.py`) with automatic CPU fallback, Hardware Toggle Switch `[ GPU / CPU ]`, and SSE progress stream.
  * **Sprint 3 (Vertical Slice 3)**: Interactive Crop ROI Canvas, Glassmorphic UI polish, and Transparent Checkerboard Video Preview Player.
* **Test & Documentation Enhancements**:
  * Added high-quality Vietnamese female presenter assets to local ignored directory `test/` (`test/vietnamese_mc_phu_quoc.png` and `test/vietnamese_mc_studio.png`).
  * Updated `.gitignore` to ignore the `test/` directory.
  * Full international English documentation upgrade across all project `.md` files (`README.md`, `PROJECT.md`, `ARCHITECTURE.md`, `TEST_INFRA.md`, `ORIGINAL_REQUEST.md`, `HANDOFF.md`).
* **TDD & Security Compliance**:
  * Achieved **100% Pass Rate (11/11 tests PASSED)** across the full automated test suite.
  * Passed static security verification (**Semgrep Scan with 0 findings**).

## Uncommitted State
* Clean working tree. All source code changes and updated documentation are committed and pushed to GitHub `main` branch.

## Verification Shortcuts (Quick Commands for New Sessions)
1. **Run Full TDD Test Suite (11/11 tests)**:
   ```bash
   .venv/bin/python -m pytest tests/ -v
   ```
2. **Run Semgrep Static Security Scan**:
   ```bash
   semgrep scan --config=auto services/
   ```
3. **Run Local FastAPI Server**:
   ```bash
   .venv/bin/uvicorn services.backend.main:app --reload --port 8000
   ```

## Key Architectural Decisions & Gotchas
* **Office Laptop Optimization**: Ultra-fast CPU Viseme mode renders static mouth shape sprites within 2-5 seconds with < 2GB RAM consumption.
* **Graceful CPU Fallback**: Selecting GPU Wav2Lip mode on non-CUDA hardware automatically emits a non-blocking warning and safely falls back to CPU Viseme rendering.
* **Path Traversal Security**: Strict `Path.is_relative_to()` canonical check applied across all download endpoints.
* **Local Test Storage**: `test/` folder created in workspace root for temporary media tests, ignored in `.gitignore`.

## Next Steps for Future Sessions
1. Execute full test suite via `.venv/bin/python -m pytest tests/ -v` to confirm 100% pass status.
2. Launch local server via `.venv/bin/uvicorn services.backend.main:app --reload --port 8000` and navigate to `http://127.0.0.1:8000`.
