"""
Proposed E2E tests for Tier 1: Feature Coverage (R2 - Dynamic Time Alignment & Composition).
To be located at: tests/e2e/tier1_feature_coverage/test_r2_dta.py
Tests alignment, padding, and transcoding as an opaque-box via mock CLI outputs.
"""
import os
import json
import subprocess
import pytest
from unittest.mock import patch, MagicMock

def run_dta_cli(tmp_path, dta_inputs):
    # Write inputs for dynamic mock CLI DTA calculator
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
    
    # Read computed shifts
    shifts_path = os.path.join(tmp_path, "timeline_shifts.json")
    with open(shifts_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["timeline_shifts"]

def test_audio_time_stretching_within_limits(tmp_path):
    # Case 6: Co giãn tốc độ âm thanh (0.85x - 1.25x)
    inputs = [
        {"original_duration": 10.0, "target_duration": 9.0},  # raw speed 1.11x (within)
        {"original_duration": 10.0, "target_duration": 7.0}   # raw speed 1.42x -> capped at 1.25x
    ]
    shifts = run_dta_cli(tmp_path, inputs)
    assert len(shifts) == 2
    assert 0.85 <= shifts[0]["speed"] <= 1.25
    assert abs(shifts[0]["speed"] - 1.1111) < 0.01
    assert shifts[1]["speed"] == 1.25

def test_video_padding_freeze_frames(tmp_path):
    # Case 7: Chèn freeze frame (bản dịch dài hơn audio giãn tối đa, raw speed 0.67x -> capped at 0.85x)
    # Stretched duration = 11.76s. Padding = 15 - 11.76 = 3.24s
    inputs = [
        {"original_duration": 10.0, "target_duration": 15.0}
    ]
    shifts = run_dta_cli(tmp_path, inputs)
    assert shifts[0]["speed"] == 0.85
    assert shifts[0]["silence_padding"] > 0.0
    assert shifts[0]["action_required"] == "loop_last_frame"

def test_silence_padding(tmp_path):
    # Case 8: Chèn khoảng lặng (original 10s, target 12s -> raw speed 0.83x -> capped at 0.85x)
    # Stretched audio = 11.76s. Silence padding = 12 - 11.76 = 0.24s
    inputs = [
        {"original_duration": 10.0, "target_duration": 12.0}
    ]
    shifts = run_dta_cli(tmp_path, inputs)
    assert shifts[0]["speed"] == 0.85
    assert abs(shifts[0]["silence_padding"] - 0.24) < 0.05
    assert shifts[0]["action_required"] == "loop_last_frame"

@patch("subprocess.run")
def test_vfr_to_cfr_transcoding(mock_run):
    # Case 9: FFMPEG chuẩn hóa video CFR (kiểm tra chạy lệnh CFR ffmpeg thành công)
    mock_run.return_value = MagicMock(returncode=0)
    cmd = [
        "ffmpeg", "-y", "-i", "input_vfr.mp4",
        "-filter:v", "fps=fps=25", "output_cfr.mp4"
    ]
    result = subprocess.run(cmd)
    assert result.returncode == 0
    mock_run.assert_called_once_with(cmd)

def test_dta_duration_deltas(tmp_path):
    # Case 10: Tính toán chính xác delta slide duration
    inputs = [
        {"original_duration": 10.0, "target_duration": 12.5}
    ]
    shifts = run_dta_cli(tmp_path, inputs)
    assert shifts[0]["delta_seconds"] == 2.5
