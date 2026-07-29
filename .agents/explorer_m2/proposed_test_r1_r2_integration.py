"""
Proposed test file for Tier 3: Cross-Feature Integration (R1 Translation - R2 DTA Sync).
To be located at: tests/e2e/tier3_cross_feature/test_r1_r2_integration.py
"""
import os
import json
import subprocess
import pytest

def test_translation_dta_sync():
    # 1. Create a dummy input video file
    video_input = "/tmp/codeavatar_test_backend/input_test_integration.mp4"
    os.makedirs(os.path.dirname(video_input), exist_ok=True)
    with open(video_input, "wb") as f:
        f.write(b"dummy_video_bytes")
        
    output_dir = "/tmp/codeavatar_test_backend/out_integration"
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)
        
    # 2. Run the pipeline CLI (intercepted by fixture and run via mock_cli.py)
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
    
    # 3. Verify output files
    expected_webm = os.path.join(output_dir, "input_test_integration_rendered_alpha.webm")
    expected_srt = os.path.join(output_dir, "input_test_integration_subtitles.srt")
    expected_json = os.path.join(output_dir, "timeline_shifts.json")
    
    assert os.path.exists(expected_webm)
    assert os.path.exists(expected_srt)
    assert os.path.exists(expected_json)
    
    # 4. Verify DTA timeline shifts content
    with open(expected_json, "r", encoding="utf-8") as f:
        shifts = json.load(f)
        
    assert shifts["target_language"] == "en"
    assert "timeline_shifts" in shifts
    assert len(shifts["timeline_shifts"]) == 2
    assert shifts["timeline_shifts"][0]["slide_index"] == 0
    assert shifts["timeline_shifts"][0]["action_required"] == "loop_last_frame"
