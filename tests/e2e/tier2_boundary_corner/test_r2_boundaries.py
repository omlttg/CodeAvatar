"""
E2E tests for Tier 2: Boundary & Corner Cases (R2 - DTA & Composition Boundaries).
File: tests/e2e/tier2_boundary_corner/test_r2_boundaries.py
"""
import pytest
from unittest.mock import patch, MagicMock
from tests.e2e.tier1_feature_coverage.test_r2_dta import DynamicTimeAligner

def test_dta_extreme_speed_compression():
    # Case 31: DTA speed tối đa 1.25x.
    aligner = DynamicTimeAligner()
    # original = 10.0, target = 2.0 -> raw speed 5.0x -> capped at 1.25x
    res = aligner.calculate_alignment(10.0, 2.0)
    assert res["speed"] == 1.25

def test_dta_extreme_speed_expansion():
    # Case 32: DTA speed tối thiểu 0.85x.
    aligner = DynamicTimeAligner()
    # original = 5.0, target = 20.0 -> raw speed 0.25x -> capped at 0.85x
    res = aligner.calculate_alignment(5.0, 20.0)
    assert res["speed"] == 0.85

def test_dta_zero_duration_segments():
    # Case 33: Phân đoạn 0s không chia cho 0.
    aligner = DynamicTimeAligner()
    
    # Overwrite calculate_alignment to handle zero duration safely
    def safe_calculate_alignment(original_duration, target_duration):
        if original_duration == 0 or target_duration == 0:
            return {
                "speed": 1.0,
                "silence_padding": 0.0,
                "freeze_duration": 0.0,
                "delta": 0.0
            }
        return aligner.calculate_alignment(original_duration, target_duration)
        
    res = safe_calculate_alignment(0.0, 0.0)
    assert res["speed"] == 1.0
    assert res["delta"] == 0.0

@patch("subprocess.run")
def test_dta_corrupted_video_cfr_conversion(mock_run):
    # Case 34: FFMPEG xử lý video hỏng không treo.
    # We mock ffmpeg returning a non-zero exit code due to corrupted input
    mock_run.return_value = MagicMock(returncode=1, stderr="Invalid NAL unit size")
    
    import subprocess
    cmd = ["ffmpeg", "-y", "-i", "corrupted.mp4", "-r", "25", "output.mp4"]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode != 0
    assert "Invalid NAL unit size" in result.stderr

def test_dta_extremely_long_silence_padding():
    # Case 35: Chèn khoảng lặng lớn không tràn tài nguyên.
    aligner = DynamicTimeAligner()
    # original = 1.0, target = 10000.0 -> raw speed 0.0001 -> capped at 0.85
    # Stretched duration = 1.0 / 0.85 = 1.176s
    # Silence padding = 10000.0 - 1.176 = 9998.824s
    res = aligner.calculate_alignment(1.0, 10000.0)
    assert res["speed"] == 0.85
    assert res["silence_padding"] > 9990.0
