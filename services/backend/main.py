"""
main.py - Full-Featured Minimalist FastAPI Backend Server
[English - Vietnamese bilingual documentation]

English: Complete backend for CodeAvatar supporting dual render engines, ROI face cropping, SSE progress logs, and glassmorphic Web UI.
Vietnamese: Server backend hoàn chỉnh cho CodeAvatar hỗ trợ dual engine, crop ROI mặt MC, SSE progress logs và giao diện Glassmorphism.
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

app = FastAPI(title="CodeAvatar API", version="3.0.0")

# Restrict CORS origins to local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STORAGE_DIR = Path("/home/thienvu/workspace/CodeAvatar/storage").resolve()
JOBS_DIR = STORAGE_DIR / "jobs"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
JOBS_DIR.mkdir(parents=True, exist_ok=True)

JOBS_REGISTRY = {}

async def process_avatar_job(job_id: str, audio_bytes: bytes, avatar_path: str, mode: str, crop_roi: dict):
    """
    English: Background job worker for dual render engine and crop ROI bounding box.
    Vietnamese: Worker xử lý job nền cho cả 2 engine render và tọa độ crop ROI.
    """
    try:
        JOBS_REGISTRY[job_id]["status"] = "processing"
        JOBS_REGISTRY[job_id]["progress"] = 15
        JOBS_REGISTRY[job_id]["message"] = f"Job initialized in '{mode}' mode."
        await asyncio.sleep(0.1)

        if mode == "gpu_wav2lip":
            engine = GPULipSyncEngine()
        else:
            engine = CPUVisemeEngine()

        JOBS_REGISTRY[job_id]["progress"] = 40
        JOBS_REGISTRY[job_id]["message"] = f"Applying ROI Crop {crop_roi} & generating lip-sync..."
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
    English: REST endpoint accepting audio, avatar image/video, mode, and ROI crop coordinates.
    Vietnamese: REST endpoint nhận audio, mẫu MC, mode và tọa độ crop ROI.
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
        "crop_roi": roi_dict,
        "status": "pending",
        "progress": 0,
        "message": "Job queued.",
        "avatar_path": avatar_save_path,
        "output_path": None,
        "error": None
    }

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
    English: Serve Glassmorphic 1-Page Web UI frontend with Interactive Crop ROI Canvas & Transparent Checkerboard Preview Player.
    Vietnamese: Giao diện Web UI Glassmorphism với Interactive Crop ROI Canvas & Player xem trước nền lưới caro.
    """
    return """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CodeAvatar - Transparent MC Avatar Generator</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * { box-sizing: border-box; }
            body { font-family: 'Inter', sans-serif; background: #090d16; color: #f8fafc; margin: 0; padding: 2rem; display: flex; justify-content: center; }
            .card { background: rgba(30, 41, 59, 0.65); backdrop-filter: blur(20px); border-radius: 20px; padding: 2.5rem; max-width: 720px; width: 100%; border: 1px solid rgba(255,255,255,0.12); box-shadow: 0 30px 60px rgba(0,0,0,0.7); }
            h1 { font-size: 2rem; background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0 0 0.5rem 0; font-weight: 700; }
            p.subtitle { color: #94a3b8; font-size: 0.95rem; margin-bottom: 2rem; }
            
            /* Hardware Switch Component */
            .switch-box { display: flex; align-items: center; justify-content: space-between; background: rgba(15, 23, 42, 0.8); padding: 0.85rem 1.2rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 1.5rem; }
            .switch-title { font-weight: 600; color: #e2e8f0; font-size: 0.95rem; }
            .toggle-btns { display: flex; gap: 0.5rem; }
            .toggle-btn { padding: 0.55rem 1.1rem; border-radius: 8px; border: 1px solid #475569; background: #1e293b; color: #94a3b8; cursor: pointer; font-weight: 600; font-size: 0.85rem; transition: all 0.2s ease; }
            .toggle-btn.active { background: linear-gradient(135deg, #0284c7, #4f46e5); color: white; border-color: #38bdf8; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4); }
            
            label { display: block; margin: 1.2rem 0 0.5rem; font-weight: 600; color: #cbd5e1; font-size: 0.9rem; }
            input[type="file"] { width: 100%; padding: 0.75rem; border-radius: 10px; background: rgba(15, 23, 42, 0.6); color: #fff; border: 1px solid #334155; }
            
            /* Interactive Canvas Crop ROI */
            #canvasContainer { margin-top: 1rem; position: relative; display: none; background: #0f172a; border-radius: 12px; padding: 1rem; border: 1px dashed #475569; text-align: center; }
            canvas { max-width: 100%; border-radius: 8px; cursor: crosshair; }
            
            button.submit-btn { margin-top: 2rem; width: 100%; padding: 1rem; background: linear-gradient(135deg, #0284c7, #6366f1); color: white; border: none; border-radius: 10px; font-weight: 700; font-size: 1.05rem; cursor: pointer; transition: transform 0.15 ease, box-shadow 0.15s ease; box-shadow: 0 8px 24px rgba(2, 132, 199, 0.3); }
            button.submit-btn:hover { transform: translateY(-2px); box-shadow: 0 12px 30px rgba(2, 132, 199, 0.5); }
            
            /* Progress & Preview Player */
            #progressSection { margin-top: 2rem; padding: 1.5rem; background: rgba(15, 23, 42, 0.9); border-radius: 14px; border: 1px solid rgba(255,255,255,0.05); display: none; }
            .bar-bg { width: 100%; height: 10px; background: #334155; border-radius: 5px; overflow: hidden; margin: 1rem 0; }
            .bar-fill { height: 100%; background: linear-gradient(90deg, #38bdf8, #818cf8); width: 0%; transition: width 0.3s ease; }
            
            /* Transparent Checkerboard Player */
            .checkerboard-player { margin-top: 1.5rem; background-image: conic-gradient(#334155 90deg, #1e293b 90deg 180deg, #334155 180deg 270deg, #1e293b 270deg); background-size: 20px 20px; border-radius: 12px; padding: 1rem; text-align: center; border: 1px solid #475569; }
            video { max-width: 100%; border-radius: 8px; }
            .download-btn { display: inline-block; margin-top: 1rem; padding: 0.8rem 1.5rem; background: #10b981; color: white; border-radius: 8px; text-decoration: none; font-weight: 700; }
            .download-btn:hover { background: #059669; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🎭 CodeAvatar Generator</h1>
            <p class="subtitle">Bộ tạo MC ảo nền trong suốt (WebM VP9 Alpha) tối ưu cho mọi cấu hình máy tính.</p>

            <!-- Hardware Toggle Switch -->
            <div class="switch-box">
                <span class="switch-title">⚡ Hardware Mode:</span>
                <div class="toggle-btns">
                    <button type="button" class="toggle-btn active" id="btnCPU" onclick="setMode('cpu_viseme')">🚀 CPU (Viseme 2-5s)</button>
                    <button type="button" class="toggle-btn" id="btnGPU" onclick="setMode('gpu_wav2lip')">🔥 GPU (Wav2Lip CUDA)</button>
                </div>
            </div>

            <form id="avatarForm">
                <label>1. Audio lồng tiếng (.mp3 / .wav):</label>
                <input type="file" id="audioInput" accept="audio/*" required>

                <label>2. Mẫu MC chân dung (.png / .jpg):</label>
                <input type="file" id="avatarInput" accept="image/*" required>

                <!-- Interactive Crop ROI Canvas -->
                <div id="canvasContainer">
                    <div style="font-size:0.85rem; color:#94a3b8; margin-bottom:0.5rem;">Kéo chuột trên ảnh để chọn vùng khuôn mặt MC (Crop ROI):</div>
                    <canvas id="cropCanvas"></canvas>
                </div>

                <button type="submit" class="submit-btn">Render MC Ảo Nền Trong Suốt</button>
            </form>

            <div id="progressSection">
                <div id="statusMsg" style="font-weight:600;">⏳ Đang khởi tạo...</div>
                <div class="bar-bg"><div class="bar-fill" id="barFill"></div></div>
                
                <!-- Preview Player with Checkerboard Background -->
                <div id="previewArea" style="display:none;" class="checkerboard-player">
                    <div style="font-size:0.85rem; color:#cbd5e1; margin-bottom:0.5rem;">📺 Xem trước MC ảo nền trong suốt (Lưới caro):</div>
                    <video id="videoPreview" controls autoplay loop></video>
                    <br>
                    <a id="downloadLink" class="download-btn" href="#" target="_blank">⬇️ Tải Video WebM Alpha</a>
                </div>
            </div>
        </div>

        <script>
            let currentMode = 'cpu_viseme';
            let cropRoi = {};
            let isDrawing = false;
            let startX, startY;

            function setMode(mode) {
                currentMode = mode;
                document.getElementById('btnCPU').classList.toggle('active', mode === 'cpu_viseme');
                document.getElementById('btnGPU').classList.toggle('active', mode === 'gpu_wav2lip');
            }

            // Canvas Crop ROI Selection Logic
            const avatarInput = document.getElementById('avatarInput');
            const canvasContainer = document.getElementById('canvasContainer');
            const canvas = document.getElementById('cropCanvas');
            const ctx = canvas.getContext('2d');
            let imgObj = new Image();

            avatarInput.onchange = (e) => {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = (evt) => {
                        imgObj.onload = () => {
                            canvasContainer.style.display = 'block';
                            canvas.width = imgObj.width;
                            canvas.height = imgObj.height;
                            ctx.drawImage(imgObj, 0, 0);
                            cropRoi = { x: 0, y: 0, w: imgObj.width, h: imgObj.height };
                        };
                        imgObj.src = evt.target.result;
                    };
                    reader.readAsDataURL(file);
                }
            };

            canvas.onmousedown = (e) => {
                const rect = canvas.getBoundingClientRect();
                const scaleX = canvas.width / rect.width;
                const scaleY = canvas.height / rect.height;
                startX = (e.clientX - rect.left) * scaleX;
                startY = (e.clientY - rect.top) * scaleY;
                isDrawing = true;
            };

            canvas.onmousemove = (e) => {
                if (!isDrawing) return;
                const rect = canvas.getBoundingClientRect();
                const scaleX = canvas.width / rect.width;
                const scaleY = canvas.height / rect.height;
                const currX = (e.clientX - rect.left) * scaleX;
                const currY = (e.clientY - rect.top) * scaleY;

                ctx.drawImage(imgObj, 0, 0);
                ctx.strokeStyle = '#38bdf8';
                ctx.lineWidth = 3;
                const w = currX - startX;
                const h = currY - startY;
                ctx.strokeRect(startX, startY, w, h);
                cropRoi = { x: Math.min(startX, currX), y: Math.min(startY, currY), w: Math.abs(w), h: Math.abs(h) };
            };

            canvas.onmouseup = () => { isDrawing = false; };

            // Submit Handler
            document.getElementById('avatarForm').onsubmit = async (e) => {
                e.preventDefault();
                const progressSection = document.getElementById('progressSection');
                const statusMsg = document.getElementById('statusMsg');
                const barFill = document.getElementById('barFill');
                const previewArea = document.getElementById('previewArea');

                progressSection.style.display = 'block';
                previewArea.style.display = 'none';
                statusMsg.innerText = '⏳ Đang tải tệp lên server...';
                barFill.style.width = '10%';

                const formData = new FormData();
                formData.append('audio', document.getElementById('audioInput').files[0]);
                formData.append('avatar', document.getElementById('avatarInput').files[0]);
                formData.append('mode', currentMode);
                formData.append('crop_roi', JSON.stringify(cropRoi));

                try {
                    const res = await fetch('/api/generate-avatar', { method: 'POST', body: formData });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || 'Lỗi khởi tạo job');

                    const jobId = data.job_id;
                    const eventSource = new EventSource(`/api/jobs/${jobId}/stream`);

                    eventSource.onmessage = (event) => {
                        const evtData = JSON.parse(event.data);
                        barFill.style.width = evtData.progress + '%';
                        statusMsg.innerText = `⚙️ [${evtData.progress}%] ${evtData.message}`;

                        if (evtData.status === 'completed') {
                            eventSource.close();
                            const downloadUrl = `/api/jobs/${jobId}/download`;
                            document.getElementById('videoPreview').src = downloadUrl;
                            document.getElementById('downloadLink').href = downloadUrl;
                            previewArea.style.display = 'block';
                        } else if (evtData.status === 'failed') {
                            eventSource.close();
                            statusMsg.innerText = `❌ Thất bại: ${evtData.message}`;
                        }
                    };
                } catch (err) {
                    statusMsg.innerText = `❌ Lỗi: ${err.message}`;
                }
            };
        </script>
    </body>
    </html>
    """
