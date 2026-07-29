"""
main.py - Minimalist FastAPI Backend Server with Dual Render & SSE Progress Streaming
[English - Vietnamese bilingual documentation]

English: Serves REST API for CodeAvatar avatar generation, SSE progress streaming, Hardware Switch mode selection, and secure downloads.
Vietnamese: Server REST API điều phối tạo MC ảo CodeAvatar, luồng log SSE thời gian thực, nút gạt Hardware Switch và tải file an toàn.
"""

import os
import uuid
import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from services.pipeline.cpu_viseme import CPUVisemeEngine
from services.pipeline.gpu_lipsync import GPULipSyncEngine
from services.pipeline.webm_exporter import WebMExporter

app = FastAPI(title="CodeAvatar API", version="2.0.0")

# Restrict CORS to local development origins
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

# In-memory jobs registry
JOBS_REGISTRY = {}

async def process_avatar_job(job_id: str, audio_bytes: bytes, avatar_path: str, mode: str, crop_roi: dict):
    """
    English: Sequential background job processor supporting CPU Viseme and GPU Wav2Lip modes.
    Vietnamese: Tiến trình xử lý job nền hỗ trợ cả 2 chế độ CPU Viseme và GPU Wav2Lip.
    """
    try:
        JOBS_REGISTRY[job_id]["status"] = "processing"
        JOBS_REGISTRY[job_id]["progress"] = 15
        JOBS_REGISTRY[job_id]["message"] = f"Started rendering in '{mode}' mode."
        await asyncio.sleep(0.1)

        # Step 1: Select Engine according to Hardware Switch mode
        if mode == "gpu_wav2lip":
            engine = GPULipSyncEngine()
        else:
            engine = CPUVisemeEngine()

        JOBS_REGISTRY[job_id]["progress"] = 40
        JOBS_REGISTRY[job_id]["message"] = "Processing frame-by-frame lip-sync..."
        await asyncio.sleep(0.1)

        result = engine.process_sequence(
            avatar_image_path=avatar_path,
            audio_bytes=audio_bytes,
            duration=3.0,
            crop_roi=crop_roi
        )

        JOBS_REGISTRY[job_id]["progress"] = 75
        JOBS_REGISTRY[job_id]["message"] = "Encoding WebM VP9 Alpha transparent layer..."
        await asyncio.sleep(0.1)

        # Step 2: Export Transparent WebM VP9 Layer
        exporter = WebMExporter()
        output_file = str(JOBS_DIR / f"{job_id}_transparent.webm")
        exporter.export_webm(result["frames"], output_file)

        JOBS_REGISTRY[job_id]["status"] = "completed"
        JOBS_REGISTRY[job_id]["progress"] = 100
        JOBS_REGISTRY[job_id]["output_path"] = output_file
        JOBS_REGISTRY[job_id]["render_time"] = result["render_time_seconds"]
        JOBS_REGISTRY[job_id]["message"] = "Render completed successfully!"
        if result.get("fallback_notice"):
            JOBS_REGISTRY[job_id]["message"] += f" ({result['fallback_notice']})"

    except Exception as e:
        JOBS_REGISTRY[job_id]["status"] = "failed"
        JOBS_REGISTRY[job_id]["error"] = str(e)
        JOBS_REGISTRY[job_id]["message"] = f"Failed: {e}"

@app.post("/api/generate-avatar")
async def generate_avatar(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    avatar: UploadFile = File(...),
    mode: str = Form("cpu_viseme"),
    crop_roi: str = Form("{}")
):
    """
    English: Endpoint to queue avatar rendering job.
    Vietnamese: Endpoint tiếp nhận và xếp hàng job tạo MC ảo.
    """
    job_id = str(uuid.uuid4())
    
    try:
        roi_dict = json.loads(crop_roi)
    except Exception:
        roi_dict = {}

    avatar_ext = Path(avatar.filename).suffix or ".png"
    avatar_save_path = str(JOBS_DIR / f"{job_id}_input{avatar_ext}")
    
    avatar_content = await avatar.read()
    with open(avatar_save_path, "wb") as f:
        f.write(avatar_content)

    audio_bytes = await audio.read()

    JOBS_REGISTRY[job_id] = {
        "job_id": job_id,
        "mode": mode,
        "status": "pending",
        "progress": 0,
        "message": "Job queued successfully.",
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

    return {"job_id": job_id, "status": "pending", "message": "Avatar job queued successfully."}

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    English: Query job status.
    Vietnamese: Truy vấn trạng thái job.
    """
    if job_id not in JOBS_REGISTRY:
        raise HTTPException(status_code=404, detail="Job ID not found.")
    return JOBS_REGISTRY[job_id]

@app.get("/api/jobs/{job_id}/stream")
async def stream_job_progress(job_id: str):
    """
    English: SSE Endpoint to stream real-time progress events.
    Vietnamese: SSE Endpoint phát luồng log tiến độ thời gian thực.
    """
    if job_id not in JOBS_REGISTRY:
        raise HTTPException(status_code=404, detail="Job ID not found.")

    async def event_generator():
        while True:
            if job_id not in JOBS_REGISTRY:
                break
            job_info = JOBS_REGISTRY[job_id]
            data = json.dumps({
                "status": job_info["status"],
                "progress": job_info["progress"],
                "message": job_info.get("message", "")
            })
            yield {"event": "progress", "data": data}

            if job_info["status"] in ["completed", "failed"]:
                break
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())

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

    try:
        if not target_path.is_relative_to(STORAGE_DIR):
            raise HTTPException(status_code=403, detail="Access denied: Invalid file path traversal detected.")
    except AttributeError:
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
    English: Serve Glassmorphic 1-Page Web UI frontend with Hardware Switch.
    Vietnamese: Giao diện Web UI 1 trang Glassmorphism với Nút gạt Hardware Switch.
    """
    return """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>CodeAvatar - Dual Engine UI</title>
        <style>
            body { font-family: 'Inter', system-ui, sans-serif; background: #090d16; color: #f8fafc; padding: 2rem; }
            .card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(16px); padding: 2.5rem; border-radius: 16px; max-width: 640px; margin: 0 auto; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 20px 40px rgba(0,0,0,0.6); }
            h1 { font-size: 1.8rem; background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 0; }
            .switch-container { display: flex; align-items: center; justify-content: space-between; background: rgba(15, 23, 42, 0.8); padding: 0.75rem 1rem; border-radius: 10px; margin: 1.5rem 0; border: 1px solid rgba(255,255,255,0.05); }
            .switch-label { font-weight: 600; color: #cbd5e1; }
            .toggle-btn-group { display: flex; gap: 0.5rem; }
            .toggle-btn { padding: 0.5rem 1rem; border-radius: 6px; border: 1px solid #475569; background: #1e293b; color: #94a3b8; cursor: pointer; font-weight: 500; }
            .toggle-btn.active { background: #0284c7; color: white; border-color: #38bdf8; }
            label { display: block; margin: 1.2rem 0 0.5rem; font-weight: 500; color: #cbd5e1; }
            input[type="file"] { width: 100%; padding: 0.6rem; border-radius: 8px; background: rgba(15, 23, 42, 0.6); color: #fff; border: 1px solid #334155; }
            button.submit-btn { margin-top: 2rem; width: 100%; padding: 0.9rem; background: linear-gradient(135deg, #0284c7, #4f46e5); color: white; border: none; border-radius: 8px; font-weight: bold; font-size: 1rem; cursor: pointer; transition: transform 0.1s ease; }
            button.submit-btn:hover { transform: translateY(-2px); }
            #progressContainer { margin-top: 1.5rem; padding: 1.2rem; background: rgba(15, 23, 42, 0.9); border-radius: 10px; display: none; }
            .progress-bar { width: 100%; height: 8px; background: #334155; border-radius: 4px; overflow: hidden; margin-top: 0.75rem; }
            .progress-fill { height: 100%; background: #38bdf8; width: 0%; transition: width 0.3s ease; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🎭 CodeAvatar - Dual Engine UI</h1>
            
            <!-- Hardware Toggle Switch -->
            <div class="switch-container">
                <span class="switch-label">⚡ Hardware Switch Mode:</span>
                <div class="toggle-btn-group">
                    <button type="button" class="toggle-btn active" id="btnCPU" onclick="setMode('cpu_viseme')">🚀 CPU (Viseme 2-5s)</button>
                    <button type="button" class="toggle-btn" id="btnGPU" onclick="setMode('gpu_wav2lip')">🔥 GPU (Wav2Lip CUDA)</button>
                </div>
            </div>

            <form id="uploadForm">
                <label>1. Audio lồng tiếng (.mp3 / .wav):</label>
                <input type="file" id="audioFile" accept="audio/*" required>
                
                <label>2. Mẫu MC (.png / .jpg / .mp4):</label>
                <input type="file" id="avatarFile" accept="image/*,video/*" required>

                <button type="submit" class="submit-btn">Render MC Ảo Nền Trong Suốt</button>
            </form>

            <div id="progressContainer">
                <div id="statusText">⏳ Đang khởi tạo...</div>
                <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
                <div id="downloadArea" style="margin-top: 1rem;"></div>
            </div>
        </div>

        <script>
            let currentMode = 'cpu_viseme';
            function setMode(mode) {
                currentMode = mode;
                document.getElementById('btnCPU').classList.toggle('active', mode === 'cpu_viseme');
                document.getElementById('btnGPU').classList.toggle('active', mode === 'gpu_wav2lip');
            }

            document.getElementById('uploadForm').onsubmit = async (e) => {
                e.preventDefault();
                const container = document.getElementById('progressContainer');
                const statusText = document.getElementById('statusText');
                const progressFill = document.getElementById('progressFill');
                const downloadArea = document.getElementById('downloadArea');

                container.style.display = 'block';
                statusText.innerText = '⏳ Đang tải tệp lên...';
                progressFill.style.width = '10%';
                downloadArea.innerHTML = '';

                const formData = new FormData();
                formData.append('audio', document.getElementById('audioFile').files[0]);
                formData.append('avatar', document.getElementById('avatarFile').files[0]);
                formData.append('mode', currentMode);

                try {
                    const res = await fetch('/api/generate-avatar', { method: 'POST', body: formData });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || 'Lỗi khởi tạo job');
                    
                    const jobId = data.job_id;
                    
                    // Listen to Real-Time SSE Stream Endpoint
                    const eventSource = new EventSource(`/api/jobs/${jobId}/stream`);
                    eventSource.onmessage = (event) => {
                        const evtData = JSON.parse(event.data);
                        progressFill.style.width = evtData.progress + '%';
                        statusText.innerText = `⚙️ [${evtData.progress}%] ${evtData.message}`;

                        if (evtData.status === 'completed') {
                            eventSource.close();
                            downloadArea.innerHTML = `<a href="/api/jobs/${jobId}/download" style="color: #38bdf8; font-weight: bold;" target="_blank">⬇️ Tải Video WebM Nền Trong Suốt</a>`;
                        } else if (evtData.status === 'failed') {
                            eventSource.close();
                            statusText.innerText = `❌ Thất bại: ${evtData.message}`;
                        }
                    };
                } catch (err) {
                    statusText.innerText = `❌ Lỗi: ${err.message}`;
                }
            };
        </script>
    </body>
    </html>
    """
