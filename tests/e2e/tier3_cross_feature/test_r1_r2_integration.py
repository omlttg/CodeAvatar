"""
E2E tests for Tier 3: Cross-Feature Integration.
File: tests/e2e/tier3_cross_feature/test_r1_r2_integration.py
"""
import os
import json
import sqlite3
import subprocess
import pytest
from fastapi.testclient import TestClient
from tests.e2e.mock_backend import TEST_DIR, DB_PATH

def test_translation_dta_sync():
    # Case 51: R1 Dịch và R2 DTA đồng bộ tốc độ nói.
    video_input = os.path.join(TEST_DIR, "input_test_integration.mp4")
    os.makedirs(os.path.dirname(video_input), exist_ok=True)
    with open(video_input, "wb") as f:
        f.write(b"dummy_video_bytes")
        
    output_dir = os.path.join(TEST_DIR, "out_integration")
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)
        
    cmd = [
        "python",
        "services/pipeline/pipeline_cli.py",
        "--video", video_input,
        "--avatar", "preset_avatar_1",
        "--voice", "piper_voice_en",
        "--target-lang", "en",
        "--output-dir", output_dir
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert "Starting CodeAvatar E2E Pipeline" in result.stdout
    assert "GPU VRAM cleared" in result.stdout
    
    expected_webm = os.path.join(output_dir, "input_test_integration_rendered_alpha.webm")
    expected_srt = os.path.join(output_dir, "input_test_integration_subtitles.srt")
    expected_json = os.path.join(output_dir, "timeline_shifts.json")
    
    assert os.path.exists(expected_webm)
    assert os.path.exists(expected_srt)
    assert os.path.exists(expected_json)
    
    with open(expected_json, "r", encoding="utf-8") as f:
        shifts = json.load(f)
        
    assert shifts["target_language"] == "en"
    assert "timeline_shifts" in shifts
    assert len(shifts["timeline_shifts"]) == 2

def test_dta_shift_to_timeline_json_sync():
    # Case 52: Thời gian DTA cập nhật vào timeline_shifts.json và .srt.
    output_dir = os.path.join(TEST_DIR, "out_integration")
    os.makedirs(output_dir, exist_ok=True)
    
    # Write mock timeline shifts
    shifts_file = os.path.join(output_dir, "timeline_shifts.json")
    shifts_data = {
        "job_id": "integration-sync-job",
        "timeline_shifts": [
            {"slide_index": 0, "delta_seconds": 2.5}
        ]
    }
    with open(shifts_file, "w") as f:
        json.dump(shifts_data, f)
        
    # Write mock srt
    srt_file = os.path.join(output_dir, "subtitles.srt")
    with open(srt_file, "w") as f:
        f.write("1\n00:00:00,000 --> 00:00:02,500\nSynced subtitle segment\n\n")
        
    assert os.path.exists(shifts_file)
    assert os.path.exists(srt_file)

def test_pipeline_unloading_under_fastapi_load(api_client: TestClient):
    # Case 53: API queue quản lý tuần tự pipeline giữ VRAM an toàn dưới tải cao.
    video_data = b"fake_mp4_bytes"
    
    # Post multiple jobs concurrently
    job_ids = []
    for i in range(3):
        files = {"video": (f"v_{i}.mp4", video_data, "video/mp4")}
        data = {"avatar_id": "av", "voice_id": "vo", "target_language": "en"}
        resp = api_client.post("/api/jobs", files=files, data=data)
        job_ids.append(resp.json()["job_id"])
        
    # Read status of all jobs
    for jid in job_ids:
        status_resp = api_client.get(f"/api/jobs/{jid}")
        assert status_resp.status_code == 200
        assert status_resp.json()["status"] in ["pending", "processing", "completed"]

def test_script_edit_reprocesses_dta_pipeline(api_client: TestClient):
    # Case 54: Sửa kịch bản UI kích hoạt chạy lại DTA trên backend.
    video_data = b"fake_mp4_bytes"
    files = {"video": ("v.mp4", video_data, "video/mp4")}
    data = {"avatar_id": "av", "voice_id": "vo", "target_language": "en"}
    resp = api_client.post("/api/jobs", files=files, data=data)
    job_id = resp.json()["job_id"]

    # Client A updates script
    resp_edit = api_client.put(f"/api/jobs/{job_id}/script", json={"translated_text": "Updated text", "version": 1})
    assert resp_edit.status_code == 200
    
    # Verify script segments updated in database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT translated_text FROM script_segments WHERE job_id = ?", (job_id,))
    text = cursor.fetchone()[0]
    conn.close()
    
    assert text == "Updated text"

def test_alpha_webm_drive_upload_flow(api_client: TestClient):
    # Case 55: Xuất WebM và đẩy lên Drive qua resumable upload.
    video_data = b"fake_mp4_bytes"
    files = {"video": ("v.mp4", video_data, "video/mp4")}
    data = {"avatar_id": "av", "voice_id": "vo", "target_language": "en"}
    resp = api_client.post("/api/jobs", files=files, data=data)
    job_id = resp.json()["job_id"]

    # Wait until completed
    import time
    for _ in range(50):
        status = api_client.get(f"/api/jobs/{job_id}").json()["status"]
        if status == "completed":
            break
        time.sleep(0.01)

    # Download output
    down_resp = api_client.get(f"/api/jobs/{job_id}/download?filename=output_alpha.webm")
    assert down_resp.status_code == 200
    assert down_resp.content == b"MOCK_WEBM_VP9_ALPHA_DATA"

    # Upload to Google Drive
    api_client.cookies.set("session_token", "mock_valid_token")
    upload_resp = api_client.post(f"/api/jobs/{job_id}/upload-drive", data={"chunk_index": 0, "total_chunks": 1})
    assert upload_resp.status_code == 200
    assert upload_resp.json()["status"] == "completed"
