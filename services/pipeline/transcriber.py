import os
import whisper
from typing import List, Dict, Any

class WhisperTranscriber:
    def __init__(self, model_name: str = "base"):
        # Why: "base" model strikes a good balance between speed and accuracy for local deployment.
        # Tại sao: Mô hình "base" đạt sự cân bằng tốt giữa tốc độ và độ chính xác khi triển khai local.
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            self._model = whisper.load_model(self.model_name)

    def transcribe(self, audio_path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        self._load_model()
        
        # Why: Word-level timestamps will be needed for precise Dynamic Time Alignment in Sprint 2.
        # Tại sao: Word-level timestamps sẽ cần thiết cho việc đồng bộ Dynamic Time Alignment chính xác ở Sprint 2.
        result = self._model.transcribe(audio_path, word_timestamps=True)
        
        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip(),
                "words": [
                    {
                        "word": w["word"].strip(),
                        "start": w["start"],
                        "end": w["end"]
                    }
                    for w in seg.get("words", [])
                ]
            })
        return segments

    def unload(self):
        # Why: Explicitly freeing GPU VRAM to prevent Out-Of-Memory errors when loading subsequent pipeline models.
        # Tại sao: Giải phóng GPU VRAM một cách hiển nhiên để ngăn lỗi tràn bộ nhớ VRAM khi load các mô hình tiếp theo.
        if self._model is not None:
            import torch
            del self._model
            self._model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
