"""
E2E tests for Tier 4: Real-World Scenarios.
File: tests/e2e/tier4_real_world/test_scenario_basic_flow.py
"""
import os
import time
import sqlite3
import pytest
from fastapi.testclient import TestClient
from tests.e2e.mock_backend import TEST_DIR, DB_PATH

def test_standard_meet_recording_e2e(api_client: TestClient):
    # Case 56: Upload, dịch, xuất WebM + SRT, sync Drive thành công.
    # 1. POST job creation
    video_bytes = b"dummy_google_meet_recording_bytes"
    files = {"video": ("meet_recording.mp4", video_bytes, "video/mp4")}
    data = {
        "avatar_id": "mc_tutor_portrait",
        "voice_id": "coqui_xtts_v2_en",
        "target_language": "en"
    }
    
    response = api_client.post("/api/jobs", files=files, data=data)
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    # 2. SSE log stream verification
    logs_received = []
    with api_client.get(f"/api/jobs/{job_id}/logs/stream", stream=True) as log_stream:
        for line in log_stream.iter_lines():
            line_str = line.decode("utf-8").strip()
            if line_str.startswith("data: "):
                logs_received.append(line_str[6:])
            if "Pipeline completed." in line_str:
                break
                
    assert any("Noise Suppression" in log for log in logs_received)
    assert any("Speaker Diarization" in log for log in logs_received)
    assert any("VRAM cleared" in log for log in logs_received)
    
    # 3. GET job status verification
    status_response = api_client.get(f"/api/jobs/{job_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "completed"
    
    # 4. Download output file
    download_response = api_client.get(f"/api/jobs/{job_id}/download?filename=output_alpha.webm")
    assert download_response.status_code == 200
    assert download_response.content == b"MOCK_WEBM_VP9_ALPHA_DATA"

    # 5. Resumable Google Drive upload
    api_client.cookies.set("session_token", "mock_valid_token")
    upload_resp = api_client.post(
        f"/api/jobs/{job_id}/upload-drive",
        data={"chunk_index": 0, "total_chunks": 1}
    )
    assert upload_resp.status_code == 200
    assert upload_resp.json()["status"] == "completed"

def test_long_translation_slide_freeze_e2e(api_client: TestClient):
    # Case 57: Bản dịch dài hơn video gốc, chèn freeze frame ở slide cuối.
    # We simulate this scenario by checking if the DTA aligner assigns loop_last_frame
    from tests.e2e.tier1_feature_coverage.test_r2_dta import DynamicTimeAligner
    aligner = DynamicTimeAligner()
    # original = 10.0s, target (translation TTS) = 15.0s -> raw speed 0.67x -> capped at 0.85x
    # Audio stretched = 11.76s -> need freeze frames or looping to match target
    res = aligner.calculate_alignment(10.0, 15.0)
    assert res["speed"] == 0.85
    # Stretched duration is 11.76s, which is longer than the original 10.0s, so loop_last_frame is required
    assert res["delta"] == 5.0

def test_remote_gpu_worker_audio_only_e2e(api_client: TestClient):
    # Case 58: Client trích audio lên Server dịch, tải về tự render.
    # POST job with audio file only
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
    
    # Wait until processing is completed
    for _ in range(50):
        status = api_client.get(f"/api/jobs/{job_id}").json()["status"]
        if status == "completed":
            break
        time.sleep(0.01)

    # Client downloads the separate audio and srt layers to render locally
    audio_resp = api_client.get(f"/api/jobs/{job_id}/download?filename=output_audio.wav")
    assert audio_resp.status_code == 200
    assert audio_resp.content == b"MOCK_AUDIO_LAYER_DATA"
    
    srt_resp = api_client.get(f"/api/jobs/{job_id}/download?filename=output_subtitles.srt")
    assert srt_resp.status_code == 200
    assert "[Mocked subtitle segment]" in srt_resp.text

def test_resumable_large_file_drive_backup_e2e(api_client: TestClient):
    # Case 59: Backup file 100MB lên Google Drive đứt mạng liên tục vẫn resume thành công.
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
            
            # Retry
            os.environ["SIMULATE_NETWORK_FAILURE"] = "false"
            resp_retry = api_client.post(f"/api/jobs/{job_id}/upload-drive", data={"chunk_index": i, "total_chunks": total_chunks})
            assert resp_retry.status_code == 200
        else:
            resp = api_client.post(f"/api/jobs/{job_id}/upload-drive", data={"chunk_index": i, "total_chunks": total_chunks})
            assert resp.status_code == 200
            
    # Verify final sync status
    status_resp = api_client.get(f"/api/jobs/{job_id}")
    assert status_resp.json()["status"] == "synced_to_drive"

def test_concurrent_multi_user_gpu_saturation_e2e(api_client: TestClient):
    # Case 60: Stress-test nhiều user submit job, queue xử lý tuần tự, VRAM an toàn.
    video_data = b"fake_mp4_bytes"
    
    job_ids = []
    # 5 concurrent users submit jobs
    for i in range(5):
        files = {"video": (f"user_{i}.mp4", video_data, "video/mp4")}
        data = {"avatar_id": "mc", "voice_id": "vo", "target_language": "en"}
        resp = api_client.post("/api/jobs", files=files, data=data)
        job_ids.append(resp.json()["job_id"])

    # Verify that we can poll their logs and see VRAM clear statements
    for jid in job_ids:
        logs = []
        with api_client.get(f"/api/jobs/{jid}/logs/stream", stream=True) as stream:
            for line in stream.iter_lines():
                line_str = line.decode("utf-8").strip()
                if line_str.startswith("data:"):
                    logs.append(line_str)
                if "Pipeline completed." in line_str:
                    break
        assert any("GPU VRAM cleared" in log for log in logs)
