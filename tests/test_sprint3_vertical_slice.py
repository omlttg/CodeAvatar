"""
test_sprint3_vertical_slice.py - TDD Test Suite for Sprint 3 (Vertical Slice 3)
[English - Vietnamese bilingual documentation]

English: Automated TDD test suite verifying Interactive Crop ROI Canvas, Glassmorphic Web UI, Checkerboard Player, and End-to-End integration across all 3 Sprints.
Vietnamese: Bộ kiểm thử TDD tự động kiểm tra Crop ROI Canvas, Web UI Glassmorphic, Player lưới caro và tích hợp End-to-End cả 3 Sprint.
"""

import io
import time
import json
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from services.pipeline.cpu_viseme import CPUVisemeEngine
from services.backend.main import app

client = TestClient(app)

@pytest.fixture
def sample_avatar_file(tmp_path):
    """
    English: Helper fixture creating a sample avatar image.
    Vietnamese: Fixture tạo file ảnh mẫu MC tạm thời.
    """
    img = Image.new("RGBA", (200, 200), (120, 160, 200, 255))
    file_path = tmp_path / "sample_crop_avatar.png"
    img.save(file_path, format="PNG")
    return str(file_path)

def test_crop_roi_bounding_box_processing(sample_avatar_file):
    """
    English: Verify CPU Engine correctly handles custom ROI crop bounding box.
    Vietnamese: Kiểm tra CPU Engine xử lý chính xác khung tọa độ crop ROI tùy chỉnh.
    """
    engine = CPUVisemeEngine(target_fps=25)
    custom_roi = {"x": 20, "y": 30, "w": 100, "h": 100}
    
    result = engine.process_sequence(
        avatar_image_path=sample_avatar_file,
        audio_bytes=b"\x00\x80" * 1000,
        duration=1.0,
        crop_roi=custom_roi
    )

    assert result["frame_count"] == 25
    assert len(result["frames"]) == 25
    assert result["frames"][0].size == (200, 200)

def test_web_ui_glassmorphic_components_rendered():
    """
    English: Verify Web UI endpoint serves HTML containing Crop Canvas and Checkerboard Preview Player.
    Vietnamese: Kiểm tra giao diện Web UI phục vụ HTML chứa Crop Canvas và Player lưới caro trong suốt.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    
    html_content = response.text
    assert "cropCanvas" in html_content
    assert "checkerboard-player" in html_content
    assert "Hardware Mode:" in html_content
    assert "CodeAvatar Generator" in html_content

def test_full_end_to_end_3_sprint_integration(sample_avatar_file):
    """
    English: Full End-to-End Integration Test across Sprints 1, 2, and 3.
    Vietnamese: Kiểm thử tích hợp End-to-End toàn bộ cả 3 Sprint.
    """
    avatar_bytes = open(sample_avatar_file, "rb").read()
    dummy_audio = b"\x00\x80" * 3000
    crop_roi = {"x": 10, "y": 10, "w": 80, "h": 80}

    # 1. Post job with custom Crop ROI and Mode
    res = client.post(
        "/api/generate-avatar",
        files={
            "audio": ("audio.mp3", io.BytesIO(dummy_audio), "audio/mp3"),
            "avatar": ("mc.jpg", io.BytesIO(avatar_bytes), "image/jpeg"),
        },
        data={"mode": "cpu_viseme", "crop_roi": json.dumps(crop_roi)}
    )

    assert res.status_code == 200
    job_id = res.json()["job_id"]

    # 2. Monitor job status to completion
    for _ in range(50):
        s_res = client.get(f"/api/jobs/{job_id}")
        if s_res.json()["status"] == "completed":
            break
        time.sleep(0.1)

    assert s_res.json()["status"] == "completed"
    assert s_res.json()["progress"] == 100

    # 3. Verify Downloadable WebM Output
    d_res = client.get(f"/api/jobs/{job_id}/download")
    assert d_res.status_code == 200
    assert d_res.headers["content-type"] == "video/webm"
    assert len(d_res.content) > 0
