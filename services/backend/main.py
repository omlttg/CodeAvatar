"""
main.py - Minimalist FastAPI Backend Server
[English - Vietnamese bilingual documentation]

English: Serves REST API for CodeAvatar avatar generation, job status monitoring, and secure WebM downloads.
Vietnamese: Server REST API điều phối tạo MC ảo CodeAvatar, theo dõi tiến độ công việc và tải file WebM an toàn.
"""

import os
import uuid
import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from services.pipeline.cpu_viseme import CPUVisemeEngine
from services.pipeline.webm_exporter import WebMExporter

app = FastAPI(title="CodeAvatar API", version="1.0.0")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Workspace storage directories
STORAGE_DIR = Path("/home/thienvu/workspace/CodeAvatar/storage").resolve()
JOBS_DIR = STORAGE_DIR / "jobs"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
JOBS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory jobs registry (SQLite WAL mode in Sprint 2)
JOBS_REGISTRY = {}

def process_avatar_job(job_id: str, audio_bytes: bytes, avatar_path: str, mode: str, crop_roi: dict):
    """
    English: Background worker executing the avatar generation pipeline.
    Vietnamese: Tiến trình nền thực thi pipeline tạo MC ảo.
    """
    try:
        JOBS_REGISTRY[job_id]["status"] = "processing"
        JOBS_REGISTRY[job_id]["progress"] = 20

        # Step 1: Run Lip-Sync Engine
        engine = CPUVisemeEngine()
        result = engine.process_sequence(
            avatar_image_path=avatar_path,
            audio_bytes=audio_bytes,
            duration=3.0,
            crop_roi=crop_roi
        )

        JOBS_REGISTRY[job_id]["progress"] = 60

        # Step 2: Export Transparent WebM VP9 Layer
        exporter = WebMExporter()
        output_file = str(JOBS_DIR / f"{job_id}_transparent.webm")
        exporter.export_webm(result["frames"], output_file)

        JOBS_REGISTRY[job_id]["status"] = "completed"
        JOBS_REGISTRY[job_id]["progress"] = 100
        JOBS_REGISTRY[job_id]["output_path"] = output_file
        JOBS_REGISTRY[job_id]["render_time"] = result["render_time_seconds"]

    except Exception as e:
        JOBS_REGISTRY[job_id]["status"] = "failed"
        JOBS_REGISTRY[job_id]["error"] = str(e)

@app.post("/api/generate-avatar")
async def generate_avatar(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    avatar: UploadFile = File(...),
    mode: str = Form("cpu_viseme"),
    crop_roi: str = Form("{}")
):
    """
    English: Endpoint to trigger avatar video generation job.
    Vietnamese: Endpoint kích hoạt công việc tạo video MC ảo.
    """
    job_id = str(uuid.uuid4())
    
    # Parse crop ROI json safely
    try:
        roi_dict = json.loads(crop_roi)
    except Exception:
        roi_dict = {}

    # Save uploaded avatar template to disk
    avatar_ext = Path(avatar.filename).suffix or ".png"
    avatar_save_path = str(JOBS_DIR / f"{job_id}_input{avatar_ext}")
    
    avatar_content = await avatar.read()
    with open(avatar_save_path, "wb") as f:
        f.write(avatar_content)

    audio_bytes = await audio.read()

    # Register job metadata
    JOBS_REGISTRY[job_id] = {
        "job_id": job_id,
        "mode": mode,
        "status": "pending",
        "progress": 0,
        "avatar_path": avatar_save_path,
        "output_path": None,
        "error": None
    }

    # Dispatch to background task
    background_tasks.add_task(
        process_avatar_job,
        job_id,
        audio_bytes,
        avatar_save_path,
        mode,
        roi_dict
    )

    return {"job_id": job_id, "status": "pending", "message": "Avatar generation job queued successfully."}

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    English: Endpoint to query job status and progress.
    Vietnamese: Endpoint truy vấn trạng thái và tiến độ công việc.
    """
    if job_id not in JOBS_REGISTRY:
        raise HTTPException(status_code=404, detail="Job ID not found.")
    return JOBS_REGISTRY[job_id]

@app.get("/api/jobs/{job_id}/download")
async def download_webm(job_id: str):
    """
    WHY: Enforce strict path traversal check using Path.is_relative_to().
    [Tiếng Việt: Ngăn chặn tấn công Path Traversal bằng kiểm tra is_relative_to().]
    """
    if job_id not in JOBS_REGISTRY:
        raise HTTPException(status_code=404, detail="Job ID not found.")

    job_info = JOBS_REGISTRY[job_id]
    if job_info["status"] != "completed" or not job_info["output_path"]:
        raise HTTPException(status_code=400, detail="Job is not completed yet.")

    target_path = Path(job_info["output_path"]).resolve()

    # Path Traversal Security Check
    try:
        if not target_path.is_relative_to(STORAGE_DIR):
            raise HTTPException(status_code=403, detail="Access denied: Invalid file path traversal detected.")
    except AttributeError:
        # Compatibility check for Python < 3.9
        if not str(target_path).startswith(str(STORAGE_DIR)):
            raise HTTPException(status_code=403, detail="Access denied: Invalid file path traversal detected.")

    if not target_path.exists():
        raise HTTPException(status_code=404, detail="Requested file does not exist on server.")

    return FileResponse(
        path=str(target_path),
        filename=f"codeavatar_{job_id[:8]}.webm",
        media_type="video/webm"
    )

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """
    English: Serve basic 1-Page Web UI frontend.
    Vietnamese: Hiển thị giao diện Web UI 1 trang tối giản.
    """
    return """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>CodeAvatar Lightweight UI</title>
        <style>
            body { font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; padding: 2rem; }
            .card { background: #1e293b; padding: 2rem; border-radius: 12px; max-width: 600px; margin: 0 auto; box-shadow: 0 8px 32px rgba(0,0,0,0.4); }
            h1 { font-size: 1.5rem; color: #38bdf8; margin-top: 0; }
            label { display: block; margin: 1rem 0 0.5rem; font-weight: 500; }
            input[type="file"], select { width: 100%; padding: 0.5rem; border-radius: 6px; background: #334155; color: #fff; border: 1px solid #475569; }
            button { margin-top: 1.5rem; width: 100%; padding: 0.75rem; background: #0284c7; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
            button:hover { background: #0369a1; }
            #status { margin-top: 1.5rem; padding: 1rem; background: #0f172a; border-radius: 6px; display: none; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🎭 CodeAvatar Lightweight UI</h1>
            <form id="uploadForm">
                <label>1. Audio lồng tiếng (.mp3 / .wav):</label>
                <input type="file" id="audioFile" accept="audio/*" required>
                
                <label>2. Mẫu MC (.png / .jpg):</label>
                <input type="file" id="avatarFile" accept="image/*" required>

                <label>3. Chế độ Render:</label>
                <select id="modeSelect">
                    <option value="cpu_viseme">Chế độ Siêu tốc (CPU Viseme 2-5s)</option>
                    <option value="gpu_wav2lip">Chế độ Chất lượng cao (GPU Wav2Lip CUDA)</option>
                </select>

                <button type="submit">Render MC Ảo Nền Trong Suốt</button>
            </form>
            <div id="status"></div>
        </div>
        <script>
            document.getElementById('uploadForm').onsubmit = async (e) => {
                e.preventDefault();
                const statusDiv = document.getElementById('status');
                statusDiv.style.display = 'block';
                statusDiv.innerHTML = '⏳ Đang tải tệp lên server...';

                const formData = new FormData();
                formData.append('audio', document.getElementById('audioFile').files[0]);
                formData.append('avatar', document.getElementById('avatarFile').files[0]);
                formData.append('mode', document.getElementById('modeSelect').value);

                try {
                    const res = await fetch('/api/generate-avatar', { method: 'POST', body: formData });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || 'Lỗi tạo job');
                    
                    const jobId = data.job_id;
                    statusDiv.innerHTML = `⚙️ Job ID: ${jobId}<br>Trạng thái: Đang xử lý...`;
                    
                    // Poll status
                    const interval = setInterval(async () => {
                        const sRes = await fetch(`/api/jobs/${jobId}`);
                        const sData = await sRes.json();
                        if (sData.status === 'completed') {
                            clearInterval(interval);
                            statusDiv.innerHTML = `✅ Hoàn thành!<br><a href="/api/jobs/${jobId}/download" style="color: #38bdf8; font-weight: bold;" target="_blank">⬇️ Tải Video WebM Nền Trong Suốt</a>`;
                        } else if (sData.status === 'failed') {
                            clearInterval(interval);
                            statusDiv.innerHTML = `❌ Thất bại: ${sData.error}`;
                        }
                    }, 1000);
                } catch (err) {
                    statusDiv.innerHTML = `❌ Lỗi: ${err.message}`;
                }
            };
        </script>
    </body>
    </html>
    """
