#!/usr/bin/env python3
"""
Proposed Mock CLI to simulate services/pipeline/pipeline_cli.py.
To be located at: tests/e2e/mock_cli.py
Parses arguments, simulates processing steps, logs GPU cache release,
outputs transparent WebM video, subtitles, and timeline_shifts.json dynamically.
Handles boundary condition inputs for E2E tests (empty audio, long diarization, unresponsive ollama, etc.)
"""
import os
import sys
import json
import argparse
import time
import re

def parse_args():
    parser = argparse.ArgumentParser(description="Mock CodeAvatar Pipeline CLI")
    parser.add_argument("--video", required=True, help="Input video path")
    parser.add_argument("--avatar", required=True, help="Avatar ID")
    parser.add_argument("--voice", required=True, help="Voice ID")
    parser.add_argument("--target-lang", required=True, choices=["en", "ko"], help="Target language")
    parser.add_argument("--output-dir", default=".", help="Output directory")
    parser.add_argument("--script", help="Optional script text or file path")
    return parser.parse_args()

def simulate_pipeline(args):
    print("[INFO] Starting CodeAvatar E2E Pipeline (MOCK)...")
    
    # Boundary Check 1: XTTS missing speaker reference file
    if args.voice in ["missing_voice", "nonexistent.wav"]:
        print("[ERROR] XTTS requires a valid reference speaker_wav", file=sys.stderr)
        sys.exit(1)
        
    # 1. Noise Suppression
    print("[INFO] Running Noise Suppression (DeepFilterNet)...")
    time.sleep(0.01)
    
    # 2. Speaker Diarization
    print("[INFO] Running Speaker Diarization (pyannote-audio)...")
    if "long_audio.mp4" in args.video:
        print("[INFO] Diarization: Processing chunk 0-60s...")
        print("[INFO] Diarization: Processing chunk 60-120s...")
        print("[INFO] Diarization: Completed 60 chunks.")
    time.sleep(0.01)
    
    # 3. Speech-to-Text (Whisper)
    print("[INFO] Running Speech-to-Text (Whisper)...")
    if "empty_audio.mp4" in args.video:
        print("[INFO] Whisper: empty audio, no segments generated.")
    time.sleep(0.01)
    print("[INFO] GPU VRAM cleared (torch.cuda.empty_cache called).")
    
    # 4. Translation
    if args.voice == "unresponsive_ollama":
        print("[INFO] Ollama translation unresponsive, falling back to original text.")
        translation_text = args.script or "[Mocked subtitle segment]"
    else:
        print(f"[INFO] Translating transcript to {args.target_lang} using Ollama with Glossary...")
        raw_text = args.script or "[Mocked subtitle segment]"
        # Apply glossary case-insensitively
        # Glossary: "vibe code" -> "Vibe Code"
        translation_text = re.sub(r"(?i)vibe code", "Vibe Code", raw_text)
    time.sleep(0.01)
    
    # 5. Text-to-Speech (Piper / Coqui)
    print("[INFO] Running Text-to-Speech (Piper)...")
    time.sleep(0.01)
    print("[INFO] GPU VRAM cleared (torch.cuda.empty_cache called).")
    
    # 6. Lip-Sync & Face Restoration (Wav2Lip + GFPGAN)
    print("[INFO] Running Lip-Sync & Face Restoration...")
    time.sleep(0.01)
    print("[INFO] GPU VRAM cleared (torch.cuda.empty_cache called).")
    
    # 7. FFMPEG Dynamic Time Alignment & WebM Composition
    print("[INFO] Running FFMPEG CFR conversion and transparent WebM composition...")
    time.sleep(0.01)
    
    # Generate Output Files
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Target file paths
    video_base = os.path.splitext(os.path.basename(args.video))[0]
    out_webm = os.path.join(args.output_dir, f"{video_base}_rendered_alpha.webm")
    out_srt = os.path.join(args.output_dir, f"{video_base}_subtitles.srt")
    out_json = os.path.join(args.output_dir, "timeline_shifts.json")
    
    # Write a dummy transparent WebM
    with open(out_webm, "wb") as f:
        f.write(b"MOCK_WEBM_VP9_ALPHA_DATA")
        
    # Write a dummy SRT (empty if empty_audio)
    with open(out_srt, "w", encoding="utf-8") as f:
        if "empty_audio.mp4" not in args.video:
            f.write(f"1\n00:00:01,000 --> 00:00:04,500\n{translation_text}\n\n")
        
    # Write timeline_shifts.json dynamically if dta_inputs.json is provided
    dta_inputs_path = os.path.join(args.output_dir, "dta_inputs.json")
    if os.path.exists(dta_inputs_path):
        with open(dta_inputs_path, "r", encoding="utf-8") as f:
            inputs = json.load(f)
            
        timeline_shifts = []
        for idx, item in enumerate(inputs):
            orig = item.get("original_duration", 0.0)
            target = item.get("target_duration", 0.0)
            
            # Simple DTA Alignment logic simulation
            if orig == 0.0 or target == 0.0:
                speed = 1.0
                silence_padding = 0.0
                freeze_duration = 0.0
                delta = 0.0
            else:
                raw_speed = orig / target
                speed = max(0.85, min(1.25, raw_speed))
                stretched_duration = orig / speed
                silence_padding = max(0.0, target - stretched_duration)
                freeze_duration = max(0.0, stretched_duration - target)
                delta = target - orig
                
            timeline_shifts.append({
                "slide_index": idx,
                "original_duration_seconds": orig,
                "target_duration_seconds": target,
                "speed": speed,
                "silence_padding": silence_padding,
                "freeze_duration": freeze_duration,
                "delta_seconds": delta,
                "action_required": "loop_last_frame" if freeze_duration > 0 or silence_padding > 0 else "speed_up_video_or_pad_silence"
            })
            
        shifts_data = {
            "job_id": "mock-job-uuid",
            "source_language": "vi",
            "target_language": args.target_lang,
            "timeline_shifts": timeline_shifts
        }
    else:
        # Default shifts
        shifts_data = {
            "job_id": "mock-job-uuid",
            "source_language": "vi",
            "target_language": args.target_lang,
            "timeline_shifts": [
                {
                    "slide_index": 0,
                    "original_duration_seconds": 12.5,
                    "target_duration_seconds": 15.2,
                    "delta_seconds": 2.7,
                    "action_required": "loop_last_frame"
                },
                {
                    "slide_index": 1,
                    "original_duration_seconds": 24.0,
                    "target_duration_seconds": 20.5,
                    "delta_seconds": -3.5,
                    "action_required": "speed_up_video_or_pad_silence"
                }
            ]
        }
        
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(shifts_data, f, indent=2)
        
    print(f"[INFO] Pipeline completed. Outputs generated at {args.output_dir}")

def main():
    args = parse_args()
    simulate_pipeline(args)

if __name__ == "__main__":
    main()
