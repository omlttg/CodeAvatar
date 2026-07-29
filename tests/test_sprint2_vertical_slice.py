"""
test_sprint2_vertical_slice.py - TDD Test Suite for Sprint 2 (Vertical Slice 2)
[English - Vietnamese bilingual documentation]

English: Automated TDD test suite verifying GPU LipSync Engine, CPU Fallback, Hardware Switch Mode Selection, and SSE Real-time Progress Streaming.
Vietnamese: Bộ kiểm thử TDD tự động kiểm tra GPU LipSync Engine, tính năng lùi CPU, Nút gạt Hardware Switch và luồng SSE streaming tiến độ.
"""

import io
import time
import json
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from services.pipeline.gpu_lipsync import GPULipSyncEngine
from services.backend.main import app

client = TestClient(app)

@pytest.fixture
def sample_avatar_file(tmp_path):
    """
    English: Helper fixture creating a sample avatar image file.
    Vietnamese: Fixture tạo file ảnh mẫu MC tạm thời để test.
    """
    img = Image.new("RGBA", (128, 128), (150, 180, 210, 255))
    file_path = tmp_path / "sample_gpu_avatar.png"
    img.save(file_path, format="PNG")
    return str(file_path)

def test_gpu_engine_cpu_fallback(sample_avatar_file):
    """
    English: Verify GPU LipSync Engine handles absence of CUDA by gracefully falling back to CPU Viseme.
    Vietnamese: Kiểm tra GPU Engine tự động lùi về CPU Viseme mượt mà khi hệ thống không có CUDA.
    """
    engine = GPULipSyncEngine()
    result = engine.process_sequence(sample_avatar_file, audio_bytes=b"\x00\x80" * 2000, duration=2.0)

    assert result["frame_count"] == 50 # 25 FPS * 2.0s = 50 frames
    assert len(result["frames"]) == 50
    assert "mode_used" in result
    # If system has no CUDA GPU, fallback notice must be present
    if not engine.has_cuda:
        assert result["mode_used"] == "cpu_viseme_fallback"
        assert result["fallback_notice"] is not None

def test_sse_progress_stream_endpoint(sample_avatar_file):
    """
    English: Verify SSE Stream endpoint returns progress events.
    Vietnamese: Kiểm tra endpoint luồng SSE phát ra các sự kiện tiến độ thời gian thực.
    """
    avatar_bytes = open(sample_avatar_file, "rb").read()
    dummy_audio_bytes = b"\x00\x80" * 3000

    # 1. Post Job with GPU mode
    response = client.post(
        "/api/generate-avatar",
        files={
            "audio": ("voice.wav", io.BytesIO(dummy_audio_bytes), "audio/wav"),
            "avatar": ("mc.png", io.BytesIO(avatar_bytes), "image/png"),
        },
        data={"mode": "gpu_wav2lip", "crop_roi": "{}"}
    )

    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # 2. Connect to SSE stream
    with client.stream("GET", f"/api/jobs/{job_id}/stream") as stream_response:
        assert stream_response.status_code == 200
        assert "text/event-stream" in stream_response.headers["content-type"]
        
        events = []
        for line in stream_response.iter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[5:].strip()))
                if len(events) >= 2:
                    break

        assert len(events) > 0
        assert "progress" in events[0]
        assert "status" in events[0]

def test_hardware_switch_dual_mode_end_to_end(sample_avatar_file):
    """
    English: Verify End-to-End processing for both CPU and GPU mode selections.
    Vietnamese: Kiểm tra luồng End-to-End hoạt động cho cả 2 lựa chọn CPU và GPU.
    """
    avatar_bytes = open(sample_avatar_file, "rb").read()
    dummy_audio = b"\x00\x80" * 2000

    for selected_mode in ["cpu_viseme", "gpu_wav2lip"]:
        res = client.post(
            "/api/generate-avatar",
            files={
                "audio": ("audio.wav", io.BytesIO(dummy_audio), "audio/wav"),
                "avatar": ("avatar.png", io.BytesIO(avatar_bytes), "image/png"),
            },
            data={"mode": selected_mode, "crop_roi": "{}"}
        )
        assert res.status_code == 200
        job_id = res.json()["job_id"]

        # Wait for job completion
        for _ in range(50):
            s_res = client.get(f"/api/jobs/{job_id}")
            if s_res.json()["status"] == "completed":
                break
            time.sleep(0.1)

        assert s_res.json()["status"] == "completed"
        assert s_res.json()["progress"] == 100
