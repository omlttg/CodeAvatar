import os
import json
import urllib.request
from typing import List, Dict, Any

class OllamaTranslator:
    def __init__(self, model_name: str = "qwen2", host: str = "http://localhost:11434"):
        # Why: Qwen2 is highly optimized for bilingual tasks (Vietnamese/English) and runs lightweight locally.
        # Tại sao: Qwen2 được tối ưu hóa tốt cho các tác vụ song ngữ (Việt/Anh) và chạy nhẹ nhàng trên local.
        self.model_name = model_name
        self.host = host
        self.glossary = self._load_glossary()

    def _load_glossary(self) -> Dict[str, Any]:
        # Why: Glossary is stored alongside the pipeline service for consistency.
        # Tại sao: Glossary được lưu cùng thư mục với pipeline service để đảm bảo tính nhất quán.
        dir_path = os.path.dirname(os.path.realpath(__file__))
        glossary_path = os.path.join(dir_path, "glossary.json")
        if os.path.exists(glossary_path):
            with open(glossary_path, "r", encoding="utf-8") as f:
                return json.load(f).get("glossary", {})
        return {}

    def _build_system_prompt(self, text: str, target_lang: str) -> str:
        # Why: Simple dictionary scan to inject matches as hints in system prompt without needing heavy vector DBs.
        # Tại sao: Quét từ điển đơn giản để chèn gợi ý vào system prompt mà không cần Vector DB cồng kềnh.
        lang_key = "vi_to_en" if target_lang == "en" else "vi_to_ko"
        dict_map = self.glossary.get(lang_key, {})
        
        matches = {}
        lower_text = text.lower()
        for k, v in dict_map.items():
            if k in lower_text:
                matches[k] = v

        prompt = f"You are a professional translator specializing in IT, programming, and 'Vibe Code' terms.\n"
        prompt += f"Translate the following Vietnamese text to {'English' if target_lang == 'en' else 'Korean'}.\n"
        if matches:
            prompt += "Use these strict technical translations if applicable:\n"
            for k, v in matches.items():
                prompt += f"- '{k}' must be translated as '{v}'\n"
        prompt += "Only output the translated text. Do not explain, do not add introductions."
        return prompt

    def translate_segment(self, text: str, target_lang: str) -> str:
        if not text.strip():
            return ""

        system_prompt = self._build_system_prompt(text, target_lang)
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "stream": False,
            "options": {
                # Why: Force Ollama to release GPU memory immediately after processing.
                # Tại sao: Ép Ollama giải phóng bộ nhớ GPU ngay lập tức sau khi xử lý xong.
                "keep_alive": 0
            }
        }
        
        url = f"{self.host}/api/chat"
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        
        try:
            # Why: Using standard library urllib to avoid extra external HTTP client dependencies.
            # Tại sao: Sử dụng thư viện tiêu chuẩn urllib để tránh thêm các dependency client HTTP bên ngoài.
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["message"]["content"].strip()
        except Exception as e:
            # Why: Fallback behavior to ensure pipeline doesn't crash if Ollama is temporarily unavailable.
            # Tại sao: Cơ chế fallback đảm bảo pipeline không bị crash nếu Ollama tạm thời không khả dụng.
            print(f"Ollama translation failed: {e}. Falling back to original text.")
            return text
