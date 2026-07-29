"""
Proposed E2E tests for Tier 2: Boundary & Corner Cases (R1 - Core AI Pipeline Boundaries).
To be located at: tests/e2e/tier2_boundary_corner/test_r1_boundaries.py
Tests boundary behaviors as an opaque-box via subprocess/CLI calls.
"""
import os
import subprocess
import pytest

def run_boundary_cli(video_name, tmp_path, voice="tutor_voice", target_lang="en", script=None):
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

def test_empty_audio_transcription(tmp_path):
    # Case 26: Whisper xử lý âm thanh trống không crash.
    # Passing 'empty_audio.mp4' triggers the empty audio simulation in the mock CLI.
    res = run_boundary_cli("empty_audio.mp4", tmp_path)
    assert res.returncode == 0
    assert "Whisper: empty audio, no segments generated." in res.stdout
    
    # Empty srt file generated
    srt_path = os.path.join(tmp_path, "empty_audio_subtitles.srt")
    assert os.path.exists(srt_path)
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert content.strip() == ""

def test_ollama_unresponsive_fallback(tmp_path):
    # Case 27: Fallback giữ nguyên khi Ollama mất kết nối.
    # Passing voice='unresponsive_ollama' triggers connection failure simulation.
    script_text = "Thử nghiệm dịch thuật"
    res = run_boundary_cli("input.mp4", tmp_path, voice="unresponsive_ollama", script=script_text)
    assert res.returncode == 0
    assert "Ollama translation unresponsive, falling back to original text." in res.stdout
    
    # Subtitles contain the original text
    sub_path = os.path.join(tmp_path, "input_subtitles.srt")
    with open(sub_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert script_text in content

def test_glossary_case_insensitivity(tmp_path):
    # Case 28: Glossary hoạt động không phân biệt chữ hoa/thường.
    res1 = run_boundary_cli("input1.mp4", tmp_path, target_lang="en", script="vibe code")
    assert res1.returncode == 0
    sub_path1 = os.path.join(tmp_path, "input1_subtitles.srt")
    with open(sub_path1, "r", encoding="utf-8") as f:
        assert "Vibe Code" in f.read()

    res2 = run_boundary_cli("input2.mp4", tmp_path, target_lang="en", script="VIBE CODE")
    assert res2.returncode == 0
    sub_path2 = os.path.join(tmp_path, "input2_subtitles.srt")
    with open(sub_path2, "r", encoding="utf-8") as f:
        assert "Vibe Code" in f.read()

def test_extremely_long_sentence_diarization(tmp_path):
    # Case 29: Diarization xử lý hội thoại dài không tràn RAM.
    # Passing 'long_audio.mp4' triggers the diarization chunking simulation.
    res = run_boundary_cli("long_audio.mp4", tmp_path)
    assert res.returncode == 0
    assert "Diarization: Processing chunk 0-60s..." in res.stdout
    assert "Diarization: Completed 60 chunks." in res.stdout

def test_xtts_missing_speaker_reference(tmp_path):
    # Case 30: Bắn lỗi khi thiếu file mẫu giọng.
    # Passing voice='missing_voice' or 'nonexistent.wav' triggers the reference file check failure.
    res = run_boundary_cli("input.mp4", tmp_path, voice="nonexistent.wav")
    assert res.returncode != 0
    assert "XTTS requires a valid reference speaker_wav" in res.stderr
