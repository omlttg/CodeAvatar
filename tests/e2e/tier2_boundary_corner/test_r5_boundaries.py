"""
E2E tests for Tier 2: Boundary & Corner Cases (R5 - Web UI & Drive Sync Boundaries).
File: tests/e2e/tier2_boundary_corner/test_r5_boundaries.py
"""
import os
import pytest
from fastapi.testclient import TestClient

def test_drive_resumable_upload_network_interruption(api_client: TestClient):
    # Case 46: Giả lập đứt mạng và resume upload thành công (sử dụng biến môi trường SIMULATE_NETWORK_FAILURE).
    video_data = b"fake_mp4_bytes"
    files = {"video": ("v.mp4", video_data, "video/mp4")}
    data = {"avatar_id": "av", "voice_id": "vo", "target_language": "en"}
    resp = api_client.post("/api/jobs", files=files, data=data)
    job_id = resp.json()["job_id"]

    api_client.cookies.set("session_token", "mock_valid_token")
    
    # Send chunk 0 (ok)
    resp0 = api_client.post(f"/api/jobs/{job_id}/upload-drive", data={"chunk_index": 0, "total_chunks": 4})
    assert resp0.status_code == 200
    
    # Send chunk 1 (ok)
    resp1 = api_client.post(f"/api/jobs/{job_id}/upload-drive", data={"chunk_index": 1, "total_chunks": 4})
    assert resp1.status_code == 200

    # Turn on simulation flag
    os.environ["SIMULATE_NETWORK_FAILURE"] = "true"
    
    # Send chunk 2 -> should fail with 503
    resp2_fail = api_client.post(f"/api/jobs/{job_id}/upload-drive", data={"chunk_index": 2, "total_chunks": 4})
    assert resp2_fail.status_code == 503

    # The backend will automatically turn off the flag (or we verify it is off)
    # Resume chunk 2
    resp2_retry = api_client.post(f"/api/jobs/{job_id}/upload-drive", data={"chunk_index": 2, "total_chunks": 4})
    assert resp2_retry.status_code == 200

    # Send final chunk 3 (ok)
    resp3 = api_client.post(f"/api/jobs/{job_id}/upload-drive", data={"chunk_index": 3, "total_chunks": 4})
    assert resp3.status_code == 200
    assert resp3.json()["status"] == "completed"

def test_expired_oauth_token_refresh(api_client: TestClient):
    # Case 47: Gọi refresh token khi hết hạn.
    video_data = b"fake_mp4_bytes"
    files = {"video": ("v.mp4", video_data, "video/mp4")}
    data = {"avatar_id": "av", "voice_id": "vo", "target_language": "en"}
    resp = api_client.post("/api/jobs", files=files, data=data)
    job_id = resp.json()["job_id"]

    # Set expired token
    api_client.cookies.set("session_token", "expired_token")
    
    # Call upload drive -> expects 401
    resp_upload = api_client.post(f"/api/jobs/{job_id}/upload-drive", data={"chunk_index": 0, "total_chunks": 1})
    assert resp_upload.status_code == 401
    assert "expired" in resp_upload.json()["detail"].lower()

    # Call refresh token
    resp_refresh = api_client.post("/api/oauth/refresh", data={"expired_token": "expired_token"})
    assert resp_refresh.status_code == 200
    assert resp_refresh.json()["session_token"] == "mock_valid_token"

    # Call upload drive again -> expects 200 OK
    resp_upload_retry = api_client.post(f"/api/jobs/{job_id}/upload-drive", data={"chunk_index": 0, "total_chunks": 1})
    assert resp_upload_retry.status_code == 200

def test_drive_insufficient_space(api_client: TestClient):
    # Case 48: Báo lỗi rõ ràng khi Drive hết dung lượng.
    video_data = b"fake_mp4_bytes"
    files = {"video": ("v.mp4", video_data, "video/mp4")}
    data = {"avatar_id": "av", "voice_id": "vo", "target_language": "en"}
    resp = api_client.post("/api/jobs", files=files, data=data)
    job_id = resp.json()["job_id"]

    api_client.cookies.set("session_token", "mock_valid_token")
    
    os.environ["DRIVE_INSUFFICIENT_SPACE"] = "true"
    try:
        resp_upload = api_client.post(f"/api/jobs/{job_id}/upload-drive", data={"chunk_index": 0, "total_chunks": 1})
        assert resp_upload.status_code == 507
        assert "Insufficient Space" in resp_upload.json()["detail"]
    finally:
        os.environ["DRIVE_INSUFFICIENT_SPACE"] = "false"

def test_script_editor_concurrent_edit_conflict(api_client: TestClient):
    # Case 49: Xử lý xung đột khi 2 client sửa script cùng lúc.
    video_data = b"fake_mp4_bytes"
    files = {"video": ("v.mp4", video_data, "video/mp4")}
    data = {"avatar_id": "av", "voice_id": "vo", "target_language": "en"}
    resp = api_client.post("/api/jobs", files=files, data=data)
    job_id = resp.json()["job_id"]

    # Current job script version starts at 1
    # Client A updates with version=1 -> successful, updates version in db to 2
    resp_a = api_client.put(f"/api/jobs/{job_id}/script", json={"translated_text": "Text A", "version": 1})
    assert resp_a.status_code == 200
    assert resp_a.json()["version"] == 2

    # Client B updates with version=1 -> should trigger 409 Conflict because DB version is now 2
    resp_b = api_client.put(f"/api/jobs/{job_id}/script", json={"translated_text": "Text B", "version": 1})
    assert resp_b.status_code == 409
    assert "Conflict" in resp_b.json()["detail"]

def test_drive_invalid_file_permissions(api_client: TestClient):
    # Case 50: Chặn và báo lỗi 403 khi thiếu quyền.
    video_data = b"fake_mp4_bytes"
    files = {"video": ("v.mp4", video_data, "video/mp4")}
    data = {"avatar_id": "av", "voice_id": "vo", "target_language": "en"}
    resp = api_client.post("/api/jobs", files=files, data=data)
    job_id = resp.json()["job_id"]

    # Cookie with invalid permissions scope
    api_client.cookies.set("session_token", "invalid_permission_token")
    
    resp_upload = api_client.post(f"/api/jobs/{job_id}/upload-drive", data={"chunk_index": 0, "total_chunks": 1})
    assert resp_upload.status_code == 403
    assert "scope permissions" in resp_upload.json()["detail"].lower()
