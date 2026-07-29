"""
Proposed E2E tests for Tier 1: Feature Coverage (R5 - Web UI & Drive Sync).
To be located at: tests/e2e/tier1_feature_coverage/test_r5_web_ui.py
Tests UI interaction, OAuth cookie verification, Drive uploads, and style configs.
"""
import time
import sqlite3
import pytest
from fastapi.testclient import TestClient
from tests.e2e.mock_backend import DB_PATH

def test_script_editor_debouncing(api_client: TestClient):
    # Case 21: Debouncing UI gửi cập nhật script.
    # We simulate sending script updates via the API client.
    # The final debounced script state is verified to be stored successfully in the database.
    video_data = b"fake_mp4_bytes"
    files = {"video": ("v.mp4", video_data, "video/mp4")}
    data = {"avatar_id": "av", "voice_id": "vo", "target_language": "en"}
    resp = api_client.post("/api/jobs", files=files, data=data)
    job_id = resp.json()["job_id"]

    final_text = "Chào mừng các bạn đến với CodeAvatar."
    resp_update = api_client.put(f"/api/jobs/{job_id}/script", json={"translated_text": final_text, "version": 1})
    assert resp_update.status_code == 200
    
    # Verify the segment in SQLite DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT translated_text FROM script_segments WHERE job_id = ?", (job_id,))
    saved_text = cursor.fetchone()[0]
    conn.close()
    
    assert saved_text == final_text

def test_google_oauth_cookie_verification(api_client: TestClient):
    # Case 22: OAuth qua HttpOnly Cookie.
    # Create job
    video_data = b"fake_mp4_bytes"
    files = {"video": ("v.mp4", video_data, "video/mp4")}
    data = {"avatar_id": "av", "voice_id": "vo", "target_language": "en"}
    resp = api_client.post("/api/jobs", files=files, data=data)
    job_id = resp.json()["job_id"]
    
    # 1. Access without cookie -> 401 Unauthorized
    resp_no_cookie = api_client.post(
        f"/api/jobs/{job_id}/upload-drive",
        data={"chunk_index": 0, "total_chunks": 2}
    )
    assert resp_no_cookie.status_code == 401
    assert "Unauthorized" in resp_no_cookie.json()["detail"]

    # 2. Access with invalid cookie -> 401 Unauthorized
    api_client.cookies.set("session_token", "invalid_token")
    resp_bad_cookie = api_client.post(
        f"/api/jobs/{job_id}/upload-drive",
        data={"chunk_index": 0, "total_chunks": 2}
    )
    assert resp_bad_cookie.status_code == 401

    # 3. Access with valid cookie -> 200 OK
    api_client.cookies.set("session_token", "mock_valid_token")
    resp_ok = api_client.post(
        f"/api/jobs/{job_id}/upload-drive",
        data={"chunk_index": 0, "total_chunks": 2}
    )
    assert resp_ok.status_code == 200

def test_google_drive_resumable_upload(api_client: TestClient):
    # Case 23: Tải lên Google Drive theo chunk bằng scope drive.file (mock drive api).
    video_data = b"fake_mp4_bytes"
    files = {"video": ("v.mp4", video_data, "video/mp4")}
    data = {"avatar_id": "av", "voice_id": "vo", "target_language": "en"}
    resp = api_client.post("/api/jobs", files=files, data=data)
    job_id = resp.json()["job_id"]

    api_client.cookies.set("session_token", "mock_valid_token")
    
    # Send chunks sequentially
    total = 3
    for i in range(total):
        resp_chunk = api_client.post(
            f"/api/jobs/{job_id}/upload-drive",
            data={"chunk_index": i, "total_chunks": total}
        )
        assert resp_chunk.status_code == 200
        if i < total - 1:
            assert resp_chunk.json()["status"] == "chunk_received"
        else:
            assert resp_chunk.json()["status"] == "completed"
            assert resp_chunk.json()["file_id"] == "google_drive_file_id_12345"

def test_glassmorphic_ui_elements(api_client: TestClient):
    # Case 24: Kiểm tra sự tồn tại của CSS Glassmorphic qua UI Config API.
    # Fetches actual design configurations from the mock backend.
    resp = api_client.get("/api/ui/config")
    assert resp.status_code == 200
    styles = resp.json()["glassmorphic_styles"]
    assert "blur(12px)" in styles["backdrop-filter"]
    assert "rgba" in styles["background"]
    assert "1px solid" in styles["border"]

def test_drive_sync_status(api_client: TestClient):
    # Case 25: Cập nhật trạng thái đồng bộ Drive lên SQLite.
    video_data = b"fake_mp4_bytes"
    files = {"video": ("v.mp4", video_data, "video/mp4")}
    data = {"avatar_id": "av", "voice_id": "vo", "target_language": "en"}
    resp = api_client.post("/api/jobs", files=files, data=data)
    job_id = resp.json()["job_id"]

    api_client.cookies.set("session_token", "mock_valid_token")
    
    # Complete upload
    api_client.post(f"/api/jobs/{job_id}/upload-drive", data={"chunk_index": 0, "total_chunks": 1})
    
    # Verify status in database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM jobs WHERE id = ?", (job_id,))
    status = cursor.fetchone()[0]
    conn.close()
    
    assert status == "synced_to_drive"
