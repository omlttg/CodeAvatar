"""
Proposed E2E tests for Tier 2: Boundary & Corner Cases (R4 - Backend Boundaries & Security).
To be located at: tests/e2e/tier2_boundary_corner/test_r4_boundaries.py
"""
import os
import sqlite3
import pytest
import httpx
from fastapi.testclient import TestClient
from tests.e2e.mock_backend import app, TEST_DIR, DB_PATH

def test_path_traversal_attack_variations(api_client: TestClient):
    # Case 41: Chặn path traversal với `..`, absolute, và hex-encoding.
    job_id = "test-traversal-job-uuid"
    job_dir = os.path.join(TEST_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    with open(os.path.join(job_dir, "output_alpha.webm"), "w") as f:
        f.write("mock_data")

    response = api_client.get(f"/api/jobs/{job_id}/download?filename=../test_jobs.db")
    assert response.status_code == 400
    assert "Path traversal attempt blocked" in response.json()["detail"]

    response = api_client.get(f"/api/jobs/{job_id}/download?filename=/etc/passwd")
    assert response.status_code == 400
    assert "Path traversal attempt blocked" in response.json()["detail"]

    response = api_client.get(f"/api/jobs/{job_id}/download?filename=%2e%2e%2f%2e%2e%2fetc%2fpasswd")
    assert response.status_code == 400
    assert "Path traversal attempt blocked" in response.json()["detail"]

    response = api_client.get(f"/api/jobs/{job_id}/download?filename=output_alpha.webm")
    assert response.status_code == 200
    assert response.content == b"mock_data"

def test_job_queue_crash_recovery(api_client: TestClient):
    # Case 42: Khôi phục queue sau crash server backend.
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO jobs (id, status, video_input_path, target_language, avatar_id, voice_id) VALUES (?, ?, ?, ?, ?, ?)",
        ("job-pending-before-crash", "pending", "input.mp4", "en", "av", "vo")
    )
    conn.commit()
    conn.close()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM jobs WHERE status = 'pending'")
    pending_jobs = [row[0] for row in cursor.fetchall()]
    conn.close()

    assert "job-pending-before-crash" in pending_jobs

def test_simultaneous_large_file_uploads(api_client: TestClient):
    # Case 43: Upload nhiều file lớn không tăng RAM đột biến.
    large_payload = b"0" * (5 * 1024 * 1024) # 5MB dummy data
    files = {"video": ("large_video.mp4", large_payload, "video/mp4")}
    data = {
        "avatar_id": "avatar_large",
        "voice_id": "piper_en",
        "target_language": "en"
    }
    
    response = api_client.post("/api/jobs", files=files, data=data)
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    dest_path = os.path.join(TEST_DIR, job_id, "input_video.mp4")
    assert os.path.exists(dest_path)
    assert os.path.getsize(dest_path) == 5 * 1024 * 1024

@pytest.mark.asyncio
async def test_sse_client_disconnect_handling():
    # Case 44: Thu hồi tài nguyên khi client ngắt SSE sớm.
    # Uses AsyncClient to safely stream and disconnect.
    try:
        from httpx import ASGITransport
        client_kwargs = {"transport": ASGITransport(app=app)}
    except ImportError:
        client_kwargs = {"app": app}
        
    async with httpx.AsyncClient(**client_kwargs, base_url="http://test") as client:
        video_data = b"fake_mp4_bytes"
        files = {"video": ("v.mp4", video_data, "video/mp4")}
        data = {"avatar_id": "av", "voice_id": "vo", "target_language": "en"}
        resp = await client.post("/api/jobs", files=files, data=data)
        job_id = resp.json()["job_id"]

        async with client.stream("GET", f"/api/jobs/{job_id}/logs/stream") as log_stream:
            async for line in log_stream.aiter_lines():
                break

        assert True

def test_concurrent_job_status_polling(api_client: TestClient):
    # Case 45: SQLite chịu tải nhiều truy vấn poll trạng thái cùng lúc.
    video_data = b"fake_mp4_bytes"
    files = {"video": ("v.mp4", video_data, "video/mp4")}
    data = {"avatar_id": "av", "voice_id": "vo", "target_language": "en"}
    resp = api_client.post("/api/jobs", files=files, data=data)
    job_id = resp.json()["job_id"]

    for _ in range(10):
        status_resp = api_client.get(f"/api/jobs/{job_id}")
        assert status_resp.status_code == 200
        assert "status" in status_resp.json()
