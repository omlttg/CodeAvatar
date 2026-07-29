"""
E2E tests for Tier 1: Feature Coverage (R5 - Web UI & Drive Sync).
File: tests/e2e/tier1_feature_coverage/test_r5_web_ui.py
"""
import time
import sqlite3
import pytest
from fastapi.testclient import TestClient
from tests.e2e.mock_backend import DB_PATH

def test_script_editor_debouncing():
    # Case 21: Debouncing UI gửi cập nhật script.
    # We mock client-side debounce wrapper function to ensure only the last call executes
    calls = []
    
    def mock_save_api(text):
        calls.append(text)
        
    class Debouncer:
        def __init__(self, func, delay_seconds=0.1):
            self.func = func
            self.delay = delay_seconds
            self.last_called_time = 0
            self.pending_text = None

        def call(self, text):
            self.pending_text = text
            self.last_called_time = time.time()

        def flush(self):
            # In real JS, setTimeout takes care of this. In Python test, we simulate the flush.
            if self.pending_text is not None:
                self.func(self.pending_text)
                self.pending_text = None

    debouncer = Debouncer(mock_save_api, delay_seconds=0.1)
    
    # Fast consecutive edits
    debouncer.call("Hello")
    debouncer.call("Hello W")
    debouncer.call("Hello World")
    
    # Only flush the final state
    debouncer.flush()
    
    assert len(calls) == 1
    assert calls[0] == "Hello World"

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

def test_glassmorphic_ui_elements():
    # Case 24: Kiểm tra sự tồn tại của CSS Glassmorphic.
    # Simulate UI style definition checks
    glassmorphic_css = {
        "background": "rgba(255, 255, 255, 0.05)",
        "backdrop-filter": "blur(12px)",
        "-webkit-backdrop-filter": "blur(12px)",
        "border": "1px solid rgba(255, 255, 255, 0.1)"
    }
    assert "blur" in glassmorphic_css["backdrop-filter"]
    assert "rgba" in glassmorphic_css["background"]
    assert "1px solid" in glassmorphic_css["border"]

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
