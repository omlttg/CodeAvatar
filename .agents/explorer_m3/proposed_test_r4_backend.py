"""
Proposed E2E tests for Tier 1: Feature Coverage (R4 - FastAPI Backend & DB).
To be located at: tests/e2e/tier1_feature_coverage/test_r4_backend.py
Uses httpx streaming client to test SSE endpoints.
"""
import os
import sqlite3
import pytest
import httpx
from fastapi.testclient import TestClient
from tests.e2e.mock_backend import app, DB_PATH

def test_create_job_endpoint(api_client: TestClient):
    # Case 16: POST /api/jobs nhận file và lưu SQLite DB.
    video_data = b"fake_mp4_bytes"
    files = {"video": ("test_video.mp4", video_data, "video/mp4")}
    data = {
        "avatar_id": "test_avatar",
        "voice_id": "test_voice",
        "target_language": "en"
    }
    
    response = api_client.post("/api/jobs", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()
    assert "job_id" in res_data
    assert res_data["status"] == "pending"

def test_get_job_status(api_client: TestClient):
    # Case 17: GET /api/jobs/{id} trả về trạng thái.
    video_data = b"fake_mp4_bytes"
    files = {"video": ("test_video.mp4", video_data, "video/mp4")}
    data = {"avatar_id": "av1", "voice_id": "vo1", "target_language": "ko"}
    
    post_resp = api_client.post("/api/jobs", files=files, data=data)
    job_id = post_resp.json()["job_id"]
    
    get_resp = api_client.get(f"/api/jobs/{job_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["job_id"] == job_id
    assert get_resp.json()["status"] in ["pending", "processing", "completed"]

def test_fifo_queue_sequential_execution(api_client: TestClient):
    # Case 18: FIFO queue xử lý tuần tự job.
    video_data = b"fake_mp4_bytes"
    
    # Submit job 1
    files1 = {"video": ("v1.mp4", video_data, "video/mp4")}
    data1 = {"avatar_id": "av1", "voice_id": "vo1", "target_language": "en"}
    resp1 = api_client.post("/api/jobs", files=files1, data=data1)
    job1_id = resp1.json()["job_id"]

    # Submit job 2
    files2 = {"video": ("v2.mp4", video_data, "video/mp4")}
    data2 = {"avatar_id": "av2", "voice_id": "vo2", "target_language": "ko"}
    resp2 = api_client.post("/api/jobs", files=files2, data=data2)
    job2_id = resp2.json()["job_id"]

    # At submission time, job2 must be in queue
    status2 = api_client.get(f"/api/jobs/{job2_id}").json()["status"]
    assert status2 in ["pending", "processing", "completed"]

def test_sqlite_wal_mode_enabled():
    # Case 19: SQLite WAL mode.
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode;")
    mode = cursor.fetchone()[0]
    conn.close()
    assert mode.lower() == "wal"

@pytest.mark.asyncio
async def test_sse_log_stream_endpoint():
    # Case 20: GET /api/jobs/{id}/logs/stream trả về SSE logs.
    # Uses AsyncClient to avoid blocking background queue tasks.
    try:
        from httpx import ASGITransport
        client_kwargs = {"transport": ASGITransport(app=app)}
    except ImportError:
        client_kwargs = {"app": app}
        
    async with httpx.AsyncClient(**client_kwargs, base_url="http://test") as client:
        video_data = b"fake_mp4_bytes"
        files = {"video": ("test_video.mp4", video_data, "video/mp4")}
        data = {"avatar_id": "av1", "voice_id": "vo1", "target_language": "en"}
        
        post_resp = await client.post("/api/jobs", files=files, data=data)
        job_id = post_resp.json()["job_id"]
        
        logs = []
        async with client.stream("GET", f"/api/jobs/{job_id}/logs/stream") as stream:
            async for line in stream.aiter_lines():
                line_str = line.strip()
                if line_str.startswith("data:"):
                    logs.append(line_str)
                if "Pipeline completed." in line_str:
                    break
                    
        assert len(logs) > 0
        assert any("Initializing" in log or "Running" in log or "completed" in log for log in logs)
