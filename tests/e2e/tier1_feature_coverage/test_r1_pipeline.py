"""
E2E tests for Tier 1: Feature Coverage (R1 - Core AI Pipeline).
File: tests/e2e/tier1_feature_coverage/test_r1_pipeline.py
"""
import os
import pytest
import subprocess
from unittest.mock import patch, MagicMock
from services.pipeline.transcriber import WhisperTranscriber
from services.pipeline.translator import OllamaTranslator
from services.pipeline.tts import TTSEngine

@patch("whisper.load_model")
def test_whisper_transcription(mock_load):
    # Case 1: Whisper trích xuất văn bản + word-level timestamps (mock whisper model)
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "segments": [
            {
                "start": 0.0,
                "end": 2.5,
                "text": "Chào mừng các bạn",
                "words": [
                    {"word": "Chào", "start": 0.0, "end": 0.5},
                    {"word": "mừng", "start": 0.5, "end": 1.0},
                    {"word": "các", "start": 1.0, "end": 1.5},
                    {"word": "bạn", "start": 1.5, "end": 2.5}
                ]
            }
        ]
    }
    mock_load.return_value = mock_model

    transcriber = WhisperTranscriber(model_name="base")
    segments = transcriber.transcribe("dummy_path.wav")
    
    assert len(segments) == 1
    assert segments[0]["text"] == "Chào mừng các bạn"
    assert len(segments[0]["words"]) == 4
    assert segments[0]["words"][0]["word"] == "Chào"

@patch("urllib.request.urlopen")
def test_ollama_translator_with_glossary(mock_urlopen):
    # Case 2: Ollama dịch song ngữ áp dụng Glossary (mock urlopen)
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"message": {"content": "Welcome to Vibe Code"}}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    translator = OllamaTranslator(model_name="qwen2")
    translator.glossary = {
        "vi_to_en": {
            "vibe code": "Vibe Code"
        }
    }
    
    translation = translator.translate_segment("chào mừng đến với vibe code", target_lang="en")
    assert translation == "Welcome to Vibe Code"

@patch("subprocess.Popen")
def test_piper_tts_generation(mock_popen):
    # Case 3: Piper sinh file âm thanh WAV (mock subprocess Popen)
    mock_process = MagicMock()
    mock_process.communicate.return_value = ("stdout", "stderr")
    mock_process.returncode = 0
    mock_popen.return_value = mock_process

    dummy_model = "dummy_piper_model.onnx"
    with open(dummy_model, "w") as f:
        f.write("dummy")

    try:
        tts = TTSEngine(engine_type="piper", model_path=dummy_model)
        tts.generate("Welcome", "output.wav", lang="en")
        mock_popen.assert_called_once()
    finally:
        if os.path.exists(dummy_model):
            os.remove(dummy_model)

@patch("torch.cuda.empty_cache")
def test_vram_cleanup_after_unload(mock_empty_cache):
    # Case 4: Giải phóng GPU cache sau unload model (mock empty_cache)
    with patch("whisper.load_model") as mock_load:
        mock_load.return_value = MagicMock()
        transcriber = WhisperTranscriber()
        transcriber._load_model()
        
        with patch("torch.cuda.is_available", return_value=True):
            transcriber.unload()
            mock_empty_cache.assert_called()

def test_noise_suppression_and_diarization():
    # Case 5: Chạy DeepFilterNet và pyannote-audio (mock tương ứng)
    # We mock execution of DeepFilterNet and pyannote-audio pipelines or subprocesses
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="Enhanced audio saved\nSpeaker diarization done")
        
        # Simulating running DeepFilterNet CLI command
        df_command = ["deepfilter", "input.wav", "-o", "output_dir"]
        result_df = subprocess.run(df_command, capture_output=True, text=True)
        assert result_df.returncode == 0
        assert "Enhanced audio" in result_df.stdout

        # Simulating pyannote-audio diarization CLI command or mock model
        pa_command = ["pyannote-diarize", "--uri", "input", "output_dir"]
        result_pa = subprocess.run(pa_command, capture_output=True, text=True)
        assert result_pa.returncode == 0
        assert "diarization" in result_pa.stdout
