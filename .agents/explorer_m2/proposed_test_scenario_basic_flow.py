"""
Proposed test file for Tier 4: Real-World Scenarios (Basic Flow).
To be located at: tests/e2e/tier4_real_world/test_scenario_basic_flow.py
"""
import os
import time
import pytest
from fastapi.testclient import TestClient

def test_standard_meet_recording_e2e(api_client: TestClient):
    # 1. POST job creation with multipart/form-data
    video_bytes = b"dummy_google_meet_recording_bytes"
    files = {"video": ("meet_recording.mp4", video_bytes, "video/mp4")}
    data = {
        "avatar_id": "mc_tutor_portrait",
        "voice_id": "coqui_xtts_v2_en",
        "target_language": "en"
    }
    
    response = api_client.post("/api/jobs", files=files, data=data)
    assert response.status_code == 200
    job_info = response.json()
    assert "job_id" in job_info
    job_id = job_info["job_id"]
    assert job_info["status"] == "pending"

    # 2. SSE log stream verification
    logs_received = []
    with api_client.get(f"/api/jobs/{job_id}/logs/stream", stream=True) as log_stream:
        # Read lines from event stream
        for line in log_stream.iter_lines():
            line_str = line.decode("utf-8").strip()
            if line_str.startswith("data: "):
                logs_received.append(line_str[6:])
            if "Pipeline completed." in line_str:
                break
                
    # Assert logs contain key steps
    assert any("Noise Suppression" in log for log in logs_received)
    assert any("Speaker Diarization" in log for log in logs_received)
    assert any("VRAM cleared" in log for log in logs_received)
    assert any("FFMPEG" in log for log in logs_received)
    
    # 3. GET job status verification (should be completed now)
    status_response = api_client.get(f"/api/jobs/{job_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "completed"
    
    # 4. Download output file and verify (also verifying path traversal protection)
    download_response = api_client.get(f"/api/jobs/{job_id}/download?filename=output_alpha.webm")
    assert download_response.status_code == 200
    assert download_response.content == b"MOCK_WEBM_VP9_ALPHA_DATA"

    # 5. Simulate resumable Google Drive upload with HttpOnly Cookie
    api_client.cookies.set("session_token", "mock_valid_token")
    
    # First chunk
    upload_resp = api_client.post(
        f"/api/jobs/{job_id}/upload-drive",
        data={"chunk_index": 0, "total_chunks": 3}
    )
    assert upload_resp.status_code == 200
    assert upload_resp.json()["status"] == "chunk_received"
    assert upload_resp.json()["next_chunk"] == 1

    # Second chunk
    upload_resp = api_client.post(
        f"/api/jobs/{job_id}/upload-drive",
        data={"chunk_index": 1, "total_chunks": 3}
    )
    assert upload_resp.status_code == 200
    assert upload_resp.json()["status"] == "chunk_received"
    
    # Last chunk
    upload_resp = api_client.post(
        f"/api/jobs/{job_id}/upload-drive",
        data={"chunk_index": 2, "total_chunks": 3}
    )
    assert upload_resp.status_code == 200
    assert upload_resp.json()["status"] == "completed"
    assert "file_id" in upload_resp.json()
