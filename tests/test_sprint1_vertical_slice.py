"""
test_sprint1_vertical_slice.py - TDD Test Suite for Sprint 1 (Vertical Slice 1)
[English - Vietnamese bilingual documentation]

English: Automated TDD test suite verifying CPU Viseme Engine, WebM Exporter, FastAPI Backend, and Security Path Traversal prevention.
Vietnamese: Bộ kiểm thử TDD tự động kiểm tra CPU Viseme Engine, WebM Exporter, FastAPI Backend và phòng chống lỗ hổng Path Traversal.
"""

import os
import io
import time
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from services.pipeline.cpu_viseme import CPUVisemeEngine
from services.pipeline.webm_exporter import WebMExporter
from services.backend.main import app, STORAGE_DIR, JOBS_REGISTRY

client = TestClient(app)

@pytest.fixture
def sample_avatar_file(tmp_path):
    """
    English: Helper fixture creating a temporary sample avatar image file.
    Vietnamese: Fixture tạo file ảnh mẫu MC tạm thời để test.
    """
    img = Image.new("RGBA", (128, 128), (200, 150, 100, 255))
    file_path = tmp_path / "sample_avatar.png"
    img.save(file_path, format="PNG")
    return str(file_path)

@pytest.fixture
def sample_audio_bytes():
    """
    English: Helper fixture generating synthetic audio bytes.
    Vietnamese: Fixture tạo dữ liệu audio mẫu dạng bytes.
    """
    # Create 3 seconds of synthetic 8kHz PCM audio bytes
    return bytes([int(128 + 50 * math.sin(2 * math.pi * 440 * i / 8000)) for i in range(8000 * 3)])

import math

def test_cpu_viseme_engine_happy_path(sample_avatar_file, sample_audio_bytes):
    """
    English: Verify CPU Viseme Engine runs under 5 seconds and returns valid frames.
    Vietnamese: Kiểm tra CPU Viseme Engine chạy dưới 5s và trả về khung hình hợp lệ.
    """
    engine = CPUVisemeEngine(target_fps=25)
    start = time.time()
    result = engine.process_sequence(sample_avatar_file, sample_audio_bytes, duration=3.0)
    elapsed = time.time() - start

    assert result["frame_count"] == 75 # 25 FPS * 3.0s = 75 frames
    assert len(result["frames"]) == 75
    assert elapsed < 5.0 # Performance constraint: Must complete in < 5s on CPU
    assert result["frames"][0].mode == "RGBA"

def test_webm_exporter_happy_path(tmp_path):
    """
    English: Verify WebM Exporter generates valid file on disk.
    Vietnamese: Kiểm tra WebM Exporter xuất file WebM hợp lệ trên ổ đĩa.
    """
    frames = [Image.new("RGBA", (64, 64), (100, 100, 200, 255)) for _ in range(10)]
    output_file = str(tmp_path / "test_output.webm")

    exporter = WebMExporter()
    out_path = exporter.export_webm(frames, output_file, fps=25)

    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0

def test_backend_end_to_end_pipeline(sample_avatar_file):
    """
    English: Verify FastAPI End-to-End flow: Upload -> Process Job -> Download WebM.
    Vietnamese: Kiểm tra luồng End-to-End FastAPI: Upload -> Xử lý Job -> Tải WebM.
    """
    avatar_bytes = open(sample_avatar_file, "rb").read()
    dummy_audio_bytes = b"\x00\x80" * 4000

    # 1. Trigger Job creation
    response = client.post(
        "/api/generate-avatar",
        files={
            "audio": ("voice.wav", io.BytesIO(dummy_audio_bytes), "audio/wav"),
            "avatar": ("mc.png", io.BytesIO(avatar_bytes), "image/png"),
        },
        data={"mode": "cpu_viseme", "crop_roi": "{}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    job_id = data["job_id"]

    # 2. Wait for background task completion
    for _ in range(50):
        s_res = client.get(f"/api/jobs/{job_id}")
        assert s_res.status_code == 200
        status_data = s_res.json()
        if status_data["status"] == "completed":
            break
        time.sleep(0.1)

    assert status_data["status"] == "completed"
    assert status_data["progress"] == 100

    # 3. Download WebM File
    d_res = client.get(f"/api/jobs/{job_id}/download")
    assert d_res.status_code == 200
    assert d_res.headers["content-type"] == "video/webm"
    assert len(d_res.content) > 0

def test_path_traversal_security_check(tmp_path):
    """
    English: Security test verifying path traversal attacks outside storage are blocked (HTTP 403).
    Vietnamese: Kiểm tra bảo mật đảm bảo tấn công Path Traversal bị chặn với HTTP 403.
    """
    fake_job_id = "malicious_job_123"
    outside_file = tmp_path / "etc_passwd_fake.txt"
    outside_file.write_text("root:x:0:0:root:/root:/bin/bash")

    # Register malicious path outside storage
    JOBS_REGISTRY[fake_job_id] = {
        "job_id": fake_job_id,
        "status": "completed",
        "output_path": str(outside_file),
    }

    # Attempt forbidden download
    response = client.get(f"/api/jobs/{fake_job_id}/download")
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]

def test_empty_audio_edge_case(sample_avatar_file):
    """
    English: Edge case test verifying empty audio input is handled gracefully without crashing.
    Vietnamese: Edge case test kiểm tra audio rỗng được xử lý mượt mà không gây crash server.
    """
    engine = CPUVisemeEngine(target_fps=25)
    result = engine.process_sequence(sample_avatar_file, audio_bytes=b"", duration=1.0)
    
    assert result["frame_count"] == 25
    assert all(v == "REST" for v in result["visemes"])
