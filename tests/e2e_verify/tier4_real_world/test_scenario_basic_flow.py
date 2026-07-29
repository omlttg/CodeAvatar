"""
Proposed E2E tests for Tier 4: Real-World Scenarios.
To be located at: tests/e2e/tier4_real_world/test_scenario_basic_flow.py
"""
import os
import time
import json
import sqlite3
import subprocess
import pytest
import httpx
from fastapi.testclient import TestClient
from tests.e2e_verify.mock_backend import app, TEST_DIR, DB_PATH

@pytest.mark.asyncio
async def test_standard_meet_recording_e2e():
    try:
        from httpx import ASGITransport
        transport = ASGITransport(app=app)
    except ImportError:
        transport = None
        
    async with httpx.AsyncClient(transport=transport, app=app, base_url="http://test") as client:
        video_bytes = b"dummy_google_meet_recording_bytes"
        files = {"video": ("meet_recording.mp4", video_bytes, "video/mp4")}
        data = {
            "avatar_id": "mc_tutor_portrait",
            "voice_id": "coqui_xtts_v2_en",
            "target_language": "en"
        }
        
        response = await client.post("/api/jobs", files=files, data=data)
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        
        logs_received = []
        async with client.stream("GET", f"/api/jobs/{job_id}/logs/stream") as log_stream:
            async for line in log_stream.aiter_lines():
                line_str = line.strip()
                if line_str.startswith("data: "):
                    logs_received.append(line_str[6:])
                if "Pipeline completed." in line_str:
                    break
                    
        assert any("Noise Suppression" in log for log in logs_received)
        assert any("Speaker Diarization" in log for log in logs_received)
        assert any("VRAM cleared" in log for log in logs_received)
        
        status_response = await client.get(f"/api/jobs/{job_id}")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "completed"
        
        download_response = await client.get(f"/api/jobs/{job_id}/download?filename=output_alpha.webm")
        assert download_response.status_code == 200
        assert download_response.content == b"MOCK_WEBM_VP9_ALPHA_DATA"

def test_long_translation_slide_freeze_e2e(tmp_path):
    inputs = [{"original_duration": 10.0, "target_duration": 15.0}]
    inputs_path = os.path.join(tmp_path, "dta_inputs.json")
    with open(inputs_path, "w", encoding="utf-8") as f:
        json.dump(inputs, f)
        
    video_path = os.path.join(tmp_path, "input.mp4")
    with open(video_path, "wb") as f:
        f.write(b"fake_video")
        
    cmd = [
        "python3", "services/pipeline/pipeline_cli.py",
        "--video", video_path,
        "--avatar", "preset_avatar",
        "--voice", "tutor_voice",
        "--target-lang", "en",
        "--output-dir", str(tmp_path)
    ]
    subprocess.run(cmd, check=True)
    
    shifts_path = os.path.join(tmp_path, "timeline_shifts.json")
    with open(shifts_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    shifts = data["timeline_shifts"]
    assert len(shifts) == 1
    assert shifts[0]["speed"] == 0.85
    assert shifts[0]["delta_seconds"] == 5.0
    assert shifts[0]["action_required"] == "loop_last_frame"

def test_remote_gpu_worker_audio_only_e2e(api_client: TestClient):
    audio_bytes = b"dummy_extracted_audio_wav_data"
    files = {"video": ("extracted_audio.wav", audio_bytes, "audio/wav")}
    data = {
        "avatar_id": "none_audio_only",
        "voice_id": "piper_en",
        "target_language": "en"
    }
    
    resp = api_client.post("/api/jobs", files=files, data=data)
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]
    
    for _ in range(50):
        status = api_client.get(f"/api/jobs/{job_id}").json()["status"]
        if status == "completed":
            break
        time.sleep(0.01)

    audio_resp = api_client.get(f"/api/jobs/{job_id}/download?filename=output_audio.wav")
    assert audio_resp.status_code == 200
    assert audio_resp.content == b"MOCK_AUDIO_LAYER_DATA"
    
    sub_resp = api_client.get(f"/api/jobs/{job_id}/download?filename=output_subtitles.srt")
    assert sub_resp.status_code == 200
    assert "[Mocked subtitle segment]" in sub_resp.text

def test_resumable_large_file_drive_backup_e2e(api_client: TestClient):
    job_id = "backup-large-file-job"
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO jobs (id, status, video_input_path, target_language, avatar_id, voice_id) VALUES (?, ?, ?, ?, ?, ?)",
        (job_id, "completed", "input.mp4", "en", "av", "vo")
    )
    conn.commit()
    conn.close()

    api_client.cookies.set("session_token", "mock_valid_token")
    
    total_chunks = 5
    for i in range(total_chunks):
        if i in [2, 4]:
            os.environ["SIMULATE_NETWORK_FAILURE"] = "true"
            resp = api_client.post(f"/api/jobs/{job_id}/upload-drive", data={"chunk_index": i, "total_chunks": total_chunks})
            assert resp.status_code == 503
            
            os.environ["SIMULATE_NETWORK_FAILURE"] = "false"
            resp_retry = api_client.post(f"/api/jobs/{job_id}/upload-drive", data={"chunk_index": i, "total_chunks": total_chunks})
            assert resp_retry.status_code == 200
        else:
            resp = api_client.post(f"/api/jobs/{job_id}/upload-drive", data={"chunk_index": i, "total_chunks": total_chunks})
            assert resp.status_code == 200
            
    status_resp = api_client.get(f"/api/jobs/{job_id}")
    assert status_resp.json()["status"] == "synced_to_drive"

@pytest.mark.asyncio
async def test_concurrent_multi_user_gpu_saturation_e2e():
    try:
        from httpx import ASGITransport
        transport = ASGITransport(app=app)
    except ImportError:
        transport = None
        
    async with httpx.AsyncClient(transport=transport, app=app, base_url="http://test") as client:
        video_data = b"fake_mp4_bytes"
        
        job_ids = []
        for i in range(5):
            files = {"video": (f"user_{i}.mp4", video_data, "video/mp4")}
            data = {"avatar_id": "mc", "voice_id": "vo", "target_language": "en"}
            resp = await client.post("/api/jobs", files=files, data=data)
            job_ids.append(resp.json()["job_id"])

        for jid in job_ids:
            logs = []
            async with client.stream("GET", f"/api/jobs/{jid}/logs/stream") as stream:
                async for line in stream.aiter_lines():
                    line_str = line.strip()
                    if line_str.startswith("data:"):
                        logs.append(line_str)
                    if "Pipeline completed." in line_str:
                        break
            assert any("GPU VRAM cleared" in log for log in logs)
