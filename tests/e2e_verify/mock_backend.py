"""
Proposed Mock FastAPI backend to simulate /services/backend behavior.
To be located at: tests/e2e_verify/mock_backend.py
"""
import os
import uuid
import sqlite3
import asyncio
from typing import Dict, Any, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Cookie, Query, Response, Header
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

app = FastAPI(title="CodeAvatar Mock Backend")

# Setup temporary test directory in the workspace dynamically based on current file location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(BASE_DIR, "test_sandbox")
os.makedirs(TEST_DIR, exist_ok=True)
DB_PATH = os.path.join(TEST_DIR, "test_jobs.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            video_input_path TEXT NOT NULL,
            target_language TEXT NOT NULL,
            avatar_id TEXT NOT NULL,
            voice_id TEXT NOT NULL,
            script_version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS script_segments (
            id TEXT PRIMARY KEY,
            job_id TEXT REFERENCES jobs(id),
            speaker_id TEXT NOT NULL,
            start_time REAL NOT NULL,
            end_time REAL NOT NULL,
            vietnamese_text TEXT NOT NULL,
            translated_text TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

class JobQueue:
    def __init__(self):
        self.queue: List[str] = []
        self.active_job: str = None
        self.lock = asyncio.Lock()
        self.logs: Dict[str, List[str]] = {}

    async def add_job(self, job_id: str):
        async with self.lock:
            self.queue.append(job_id)
            self.logs[job_id] = []
            asyncio.create_task(self._process_queue())

    async def _process_queue(self):
        async with self.lock:
            if self.active_job is not None:
                return
            if not self.queue:
                return
            self.active_job = self.queue.pop(0)

        job_id = self.active_job
        self.logs[job_id].append("Initializing Core AI Pipeline...")
        
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE jobs SET status = 'processing' WHERE id = ?", (job_id,))
        conn.commit()
        conn.close()
        
        steps = [
            ("noise_suppression", "Running Noise Suppression (DeepFilterNet)..."),
            ("diarization", "Running Speaker Diarization (pyannote-audio)..."),
            ("whisper", "Running Speech-to-Text (Whisper)..."),
            ("translation", "Translating transcript with Ollama & Glossary..."),
            ("tts", "Running Text-to-Speech (Piper)..."),
            ("lip_sync", "Running Lip-Sync & Face Restoration (Wav2Lip+GFPGAN)..."),
            ("ffmpeg", "Running FFMPEG CFR conversion and transparent WebM composition...")
        ]
        
        for step_code, step_log in steps:
            await asyncio.sleep(0.01)
            self.logs[job_id].append(step_log)
            if step_code in ["whisper", "tts", "lip_sync"]:
                self.logs[job_id].append("GPU VRAM cleared (torch.cuda.empty_cache called).")
        
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE jobs SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ?", (job_id,))
        
        job_dir = os.path.join(TEST_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)
        
        with open(os.path.join(job_dir, "output_alpha.webm"), "wb") as f:
            f.write(b"MOCK_WEBM_VP9_ALPHA_DATA")
        with open(os.path.join(job_dir, "output_video.mp4"), "wb") as f:
            f.write(b"MOCK_VIDEO_LAYER_DATA")
        with open(os.path.join(job_dir, "output_audio.wav"), "wb") as f:
            f.write(b"MOCK_AUDIO_LAYER_DATA")
        with open(os.path.join(job_dir, "output_subtitles.srt"), "w", encoding="utf-8") as f:
            f.write("1\n00:00:01,000 --> 00:00:04,500\n[Mocked subtitle segment]\n\n")
        with open(os.path.join(job_dir, "timeline_shifts.json"), "w", encoding="utf-8") as f:
            f.write('{"timeline_shifts": []}')
        with open(os.path.join(job_dir, "metadata.json"), "w", encoding="utf-8") as f:
            f.write('{"avatar_id": "test_avatar", "voice_id": "test_voice"}')
            
        conn.commit()
        conn.close()
        self.logs[job_id].append("Pipeline completed.")

        async with self.lock:
            self.active_job = None
            asyncio.create_task(self._process_queue())

job_queue = JobQueue()

@app.post("/api/jobs")
async def create_job(
    video: UploadFile = File(...),
    avatar_id: str = Form(...),
    voice_id: str = Form(...),
    target_language: str = Form(...)
):
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(TEST_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    dest_path = os.path.join(job_dir, "input_video.mp4")
    chunk_size = 1024 * 1024
    with open(dest_path, "wb") as buffer:
        while True:
            chunk = await video.read(chunk_size)
            if not chunk:
                break
            buffer.write(chunk)
            
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO jobs (id, status, video_input_path, target_language, avatar_id, voice_id, script_version) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (job_id, "pending", dest_path, target_language, avatar_id, voice_id, 1)
    )
    conn.execute(
        "INSERT INTO script_segments (id, job_id, speaker_id, start_time, end_time, vietnamese_text, translated_text) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), job_id, "Tutor", 0.0, 10.0, "Chào mừng các bạn đến với Vibe Code.", None)
    )
    conn.commit()
    conn.close()

    await job_queue.add_job(job_id)
    return {"job_id": job_id, "status": "pending"}

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, status, target_language, avatar_id, voice_id FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": row[0],
        "status": row[1],
        "target_language": row[2],
        "avatar_id": row[3],
        "voice_id": row[4]
    }

@app.get("/api/jobs/{job_id}/logs/stream")
async def get_logs_stream(job_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM jobs WHERE id = ?", (job_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Job not found")
    conn.close()

    async def log_generator():
        sent_count = 0
        while True:
            logs = job_queue.logs.get(job_id, [])
            if sent_count < len(logs):
                for i in range(sent_count, len(logs)):
                    yield f"data: {logs[i]}\n\n"
                sent_count = len(logs)
                if logs and logs[-1] == "Pipeline completed.":
                    break
            await asyncio.sleep(0.01)

    return StreamingResponse(log_generator(), media_type="text/event-stream")

class ScriptEditRequest(BaseModel):
    translated_text: str
    version: int = 1

@app.put("/api/jobs/{job_id}/script")
async def edit_script(job_id: str, payload: ScriptEditRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT script_version FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Job not found")
    
    current_version = row[0]
    
    if payload.version != current_version:
        conn.close()
        raise HTTPException(status_code=409, detail="Concurrent Edit Conflict: Version mismatch")
        
    next_version = current_version + 1
    cursor.execute("UPDATE jobs SET script_version = ? WHERE id = ?", (next_version, job_id))
    cursor.execute("UPDATE script_segments SET translated_text = ? WHERE job_id = ?", (payload.translated_text, job_id))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Script updated successfully", "version": next_version}

@app.get("/api/jobs/{job_id}/download")
async def download_file(job_id: str, filename: str = Query("output_alpha.webm")):
    job_dir = os.path.join(TEST_DIR, job_id)
    if not os.path.exists(job_dir):
        raise HTTPException(status_code=404, detail="Job folder not found")
        
    safe_base = os.path.abspath(job_dir)
    unsafe_target = os.path.join(job_dir, filename)
    safe_target = os.path.abspath(unsafe_target)
    
    if not safe_target.startswith(safe_base + os.sep) and safe_target != safe_base:
        raise HTTPException(status_code=400, detail="Security Violation: Path traversal attempt blocked")
        
    if not os.path.exists(safe_target) or not os.path.isfile(safe_target):
        raise HTTPException(status_code=404, detail="Requested file not found")
        
    return FileResponse(safe_target)

@app.post("/api/jobs/{job_id}/upload-drive")
async def upload_to_drive(
    job_id: str, 
    oauth_token: str = Cookie(None, alias="session_token"),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...)
):
    if oauth_token == "expired_token":
        raise HTTPException(status_code=401, detail="Unauthorized: Google OAuth credentials expired")
    if oauth_token == "invalid_permission_token":
        raise HTTPException(status_code=403, detail="Forbidden: Insufficient scope permissions")
    if not oauth_token or oauth_token != "mock_valid_token":
        raise HTTPException(status_code=401, detail="Unauthorized: Google OAuth credentials missing or invalid")
        
    if os.environ.get("DRIVE_INSUFFICIENT_SPACE") == "true":
        raise HTTPException(status_code=507, detail="Google Drive Insufficient Space")
        
    await asyncio.sleep(0.01)
    
    if chunk_index == 2 and os.environ.get("SIMULATE_NETWORK_FAILURE") == "true":
        os.environ["SIMULATE_NETWORK_FAILURE"] = "false"
        raise HTTPException(status_code=503, detail="Simulated Network Interruption")
        
    if chunk_index == total_chunks - 1:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE jobs SET status = 'synced_to_drive' WHERE id = ?", (job_id,))
        conn.commit()
        conn.close()
        return {"status": "completed", "file_id": "google_drive_file_id_12345"}
        
    return {"status": "chunk_received", "next_chunk": chunk_index + 1}

@app.post("/api/oauth/refresh")
async def refresh_oauth_token(response: Response, expired_token: str = Form(...)):
    if expired_token == "expired_token":
        response.set_cookie(key="session_token", value="mock_valid_token", httponly=True)
        return {"status": "refreshed", "session_token": "mock_valid_token"}
    raise HTTPException(status_code=400, detail="Invalid token to refresh")

@app.get("/api/ui/config")
async def get_ui_config():
    return {
        "theme": "dark",
        "glassmorphic_styles": {
            "background": "rgba(255, 255, 255, 0.05)",
            "backdrop-filter": "blur(12px)",
            "-webkit-backdrop-filter": "blur(12px)",
            "border": "1px solid rgba(255, 255, 255, 0.1)"
        }
    }
