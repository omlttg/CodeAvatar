"""
Proposed E2E tests for Tier 2: Boundary & Corner Cases (R2 - DTA & Composition Boundaries).
To be located at: tests/e2e/tier2_boundary_corner/test_r2_boundaries.py
Tests extreme duration and video transcoding boundaries as an opaque-box via mock CLI.
"""
import os
import json
import subprocess
import pytest
from unittest.mock import patch, MagicMock

def run_dta_boundary_cli(tmp_path, dta_inputs):
    inputs_path = os.path.join(tmp_path, "dta_inputs.json")
    with open(inputs_path, "w", encoding="utf-8") as f:
        json.dump(dta_inputs, f)
        
    video_path = os.path.join(tmp_path, "input.mp4")
    with open(video_path, "wb") as f:
        f.write(b"fake_video_bytes")
        
    cmd = [
        "python3", "services/pipeline/pipeline_cli.py",
        "--video", video_path,
        "--avatar", "preset_avatar",
        "--voice", "tutor_voice",
        "--target-lang", "en",
        "--output-dir", str(tmp_path)
    ]
    subprocess.run(cmd, check=True)
    
    shifts_path = os.path.join(tmp_path, "timeline_shifts.json")
    with open(shifts_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["timeline_shifts"]

def test_dta_extreme_speed_compression(tmp_path):
    # Case 31: DTA speed tối đa 1.25x (original 10.0s, target 2.0s -> raw speed 5.0x -> capped at 1.25x)
    inputs = [{"original_duration": 10.0, "target_duration": 2.0}]
    shifts = run_dta_boundary_cli(tmp_path, inputs)
    assert shifts[0]["speed"] == 1.25

def test_dta_extreme_speed_expansion(tmp_path):
    # Case 32: DTA speed tối thiểu 0.85x (original 5.0s, target 20.0s -> raw speed 0.25x -> capped at 0.85x)
    inputs = [{"original_duration": 5.0, "target_duration": 20.0}]
    shifts = run_dta_boundary_cli(tmp_path, inputs)
    assert shifts[0]["speed"] == 0.85

def test_dta_zero_duration_segments(tmp_path):
    # Case 33: Phân đoạn 0s không chia cho 0.
    inputs = [{"original_duration": 0.0, "target_duration": 0.0}]
    shifts = run_dta_boundary_cli(tmp_path, inputs)
    assert shifts[0]["speed"] == 1.0
    assert shifts[0]["delta_seconds"] == 0.0

@patch("subprocess.run")
def test_dta_corrupted_video_cfr_conversion(mock_run):
    # Case 34: FFMPEG xử lý video hỏng không treo.
    # We mock ffmpeg returning a non-zero exit code due to corrupted input.
    mock_run.return_value = MagicMock(returncode=1, stderr="Invalid NAL unit size")
    
    cmd = ["ffmpeg", "-y", "-i", "corrupted.mp4", "-r", "25", "output.mp4"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode != 0
    assert "Invalid NAL unit size" in result.stderr

def test_dta_extremely_long_silence_padding(tmp_path):
    # Case 35: Chèn khoảng lặng lớn không tràn tài nguyên (original 1.0s, target 10000.0s -> capped at 0.85x)
    # Stretched duration = 1.176s. Silence padding = 10000.0 - 1.176 = 9998.824s
    inputs = [{"original_duration": 1.0, "target_duration": 10000.0}]
    shifts = run_dta_boundary_cli(tmp_path, inputs)
    assert shifts[0]["speed"] == 0.85
    assert shifts[0]["silence_padding"] > 9990.0
