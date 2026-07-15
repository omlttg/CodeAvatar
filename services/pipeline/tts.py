import os
import subprocess
from typing import Optional

class TTSEngine:
    def __init__(self, engine_type: str = "piper", model_path: Optional[str] = None):
        # Why: Piper is default because it runs extremely fast on CPU without blocking GPU memory.
        # Tại sao: Piper là mặc định vì nó chạy cực kỳ nhanh trên CPU mà không chiếm dụng bộ nhớ GPU.
        self.engine_type = engine_type
        self.model_path = model_path
        self._xtts_model = None

    def _lazy_load_xtts(self):
        if self._xtts_model is None:
            # Why: Delayed import and instantiation to prevent unnecessary torch/VRAM usage when using Piper.
            # Tại sao: Trì hoãn việc import và khởi tạo để tránh tốn torch/VRAM không cần thiết khi dùng Piper.
            from TTS.api import TTS
            print("Loading Coqui XTTS-v2 model...")
            self._xtts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
            if os.environ.get("CUDA_VISIBLE_DEVICES") != "" and self._xtts_model.device.type != 'cpu':
                self._xtts_model.to("cuda")

    def generate(self, text: str, output_wav_path: str, lang: str = "en", speaker_wav: Optional[str] = None):
        if not text.strip():
            return

        if self.engine_type == "piper":
            self._generate_piper(text, output_wav_path)
        elif self.engine_type == "xtts":
            self._generate_xtts(text, output_wav_path, lang, speaker_wav)
        else:
            raise ValueError(f"Unknown TTS engine: {self.engine_type}")

    def _generate_piper(self, text: str, output_wav_path: str):
        # Why: Piper model path is required. If not provided, we look for a default local path.
        # Tại sao: Đường dẫn model Piper là bắt buộc. Nếu không cung cấp, ta tìm kiếm ở đường dẫn mặc định local.
        model = self.model_path or "/models/piper/en_US-lessac-medium.onnx"
        if not os.path.exists(model):
            raise FileNotFoundError(f"Piper ONNX model not found at: {model}")

        # Why: Piping string into stdout to execute piper CLI, avoiding complex python binding issues.
        # Tại sao: Đưa chuỗi qua stdout để thực thi piper CLI, tránh các vấn đề liên quan đến python binding phức tạp.
        command = [
            "piper",
            "--model", model,
            "--output_file", output_wav_path
        ]
        
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            _, stderr = process.communicate(input=text)
            if process.returncode != 0:
                raise RuntimeError(f"Piper execution failed: {stderr}")
        except FileNotFoundError:
            raise RuntimeError("Piper binary not found on system PATH. Please ensure it is installed.")

    def _generate_xtts(self, text: str, output_wav_path: str, lang: str, speaker_wav: Optional[str]):
        self._lazy_load_xtts()
        if not speaker_wav or not os.path.exists(speaker_wav):
            raise ValueError("XTTS requires a valid reference speaker_wav file for voice cloning.")
            
        # Why: Calling XTTS-v2 API directly to run voice cloning.
        # Tại sao: Gọi trực tiếp API XTTS-v2 để thực hiện clone giọng nói.
        self._xtts_model.tts_to_file(
            text=text,
            speaker_wav=speaker_wav,
            language=lang,
            file_path=output_wav_path
        )

    def unload(self):
        # Why: Force unload XTTS from GPU memory to free VRAM for the Lip-sync stage.
        # Tại sao: Ép giải phóng XTTS khỏi bộ nhớ GPU để nhường VRAM cho giai đoạn Lip-sync.
        if self._xtts_model is not None:
            import torch
            del self._xtts_model
            self._xtts_model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
