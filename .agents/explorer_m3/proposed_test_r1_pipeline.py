"""
Proposed E2E tests for Tier 1: Feature Coverage (R1 - Core AI Pipeline).
To be located at: tests/e2e/tier1_feature_coverage/test_r1_pipeline.py
Tests the core AI pipeline as an opaque-box via subprocess/CLI call.
"""
import os
import subprocess
import pytest

def run_pipeline_cli(video_name, tmp_path, target_lang="en", voice="tutor_voice", script=None):
    video_path = os.path.join(tmp_path, video_name)
    with open(video_path, "wb") as f:
        f.write(b"fake_video_bytes")
        
    cmd = [
        "python3", "services/pipeline/pipeline_cli.py",
        "--video", video_path,
        "--avatar", "preset_avatar",
        "--voice", voice,
        "--target-lang", target_lang,
        "--output-dir", str(tmp_path)
    ]
    if script:
        cmd.extend(["--script", script])
        
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

def test_whisper_transcription_step_via_cli(tmp_path):
    # Case 1: Whisper trích xuất văn bản + word-level timestamps (kiểm tra log bước STT qua CLI)
    res = run_pipeline_cli("input_case1.mp4", tmp_path)
    assert res.returncode == 0
    assert "Running Speech-to-Text (Whisper)" in res.stdout
    assert os.path.exists(os.path.join(tmp_path, "input_case1_subtitles.srt"))

def test_ollama_translation_step_via_cli(tmp_path):
    # Case 2: Ollama dịch song ngữ áp dụng Glossary (kiểm tra log bước Translation qua CLI)
    res = run_pipeline_cli("input_case2.mp4", tmp_path, target_lang="en", script="vibe code")
    assert res.returncode == 0
    assert "Translating transcript to en using Ollama with Glossary" in res.stdout
    
    # Verify glossary application ("vibe code" -> "Vibe Code") in subtitles
    sub_path = os.path.join(tmp_path, "input_case2_subtitles.srt")
    with open(sub_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Vibe Code" in content

def test_piper_tts_generation_step_via_cli(tmp_path):
    # Case 3: Piper sinh file âm thanh WAV (kiểm tra log bước TTS qua CLI)
    res = run_pipeline_cli("input_case3.mp4", tmp_path)
    assert res.returncode == 0
    assert "Running Text-to-Speech (Piper)" in res.stdout
    assert os.path.exists(os.path.join(tmp_path, "input_case3_rendered_alpha.webm"))

def test_gpu_vram_cleanup_step_via_cli(tmp_path):
    # Case 4: Giải phóng GPU cache sau unload model (kiểm tra log GPU cache clear qua CLI)
    res = run_pipeline_cli("input_case4.mp4", tmp_path)
    assert res.returncode == 0
    assert "GPU VRAM cleared (torch.cuda.empty_cache called)" in res.stdout

def test_noise_suppression_and_diarization_step_via_cli(tmp_path):
    # Case 5: Chạy DeepFilterNet và pyannote-audio (kiểm tra log suppression/diarization qua CLI)
    res = run_pipeline_cli("input_case5.mp4", tmp_path)
    assert res.returncode == 0
    assert "Running Noise Suppression (DeepFilterNet)" in res.stdout
    assert "Running Speaker Diarization (pyannote-audio)" in res.stdout
