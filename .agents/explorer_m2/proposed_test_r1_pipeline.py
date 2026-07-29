"""
Proposed test file for Tier 1: Feature Coverage (R1 - Core AI Pipeline).
To be located at: tests/e2e/tier1_feature_coverage/test_r1_pipeline.py
"""
import os
import pytest
from unittest.mock import patch, MagicMock

# Import the actual classes which already exist in services/pipeline
from services.pipeline.transcriber import WhisperTranscriber
from services.pipeline.translator import OllamaTranslator
from services.pipeline.tts import TTSEngine

@patch("whisper.load_model")
def test_whisper_transcription(mock_load):
    # Mock whisper model behavior
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
    # Mock Ollama API response
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"message": {"content": "Welcome to Vibe Code"}}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    translator = OllamaTranslator(model_name="qwen2")
    # Force mock glossary entry for testing
    translator.glossary = {
        "vi_to_en": {
            "vibe code": "Vibe Code"
        }
    }
    
    translation = translator.translate_segment("chào mừng đến với vibe code", target_lang="en")
    assert translation == "Welcome to Vibe Code"

@patch("subprocess.Popen")
def test_piper_tts_generation(mock_popen):
    # Mock subprocess execution for Piper CLI
    mock_process = MagicMock()
    mock_process.communicate.return_value = ("stdout", "stderr")
    mock_process.returncode = 0
    mock_popen.return_value = mock_process

    # Create dummy model file to pass exist check
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
    with patch("whisper.load_model") as mock_load:
        mock_load.return_value = MagicMock()
        transcriber = WhisperTranscriber()
        transcriber._load_model()
        
        # Unload and verify torch cache release
        transcriber.unload()
        assert transcriber._model is None
        # empty_cache will be called if torch.cuda.is_available() is mocked to True
        with patch("torch.cuda.is_available", return_value=True):
            transcriber.unload()
            mock_empty_cache.assert_called()
