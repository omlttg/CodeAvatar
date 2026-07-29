#!/usr/bin/env python3
"""
Mock CLI to simulate services/pipeline/pipeline_cli.py.
This script parses arguments, simulates processing steps, logs GPU cache release,
and outputs a transparent WebM video, subtitles, and timeline_shifts.json.
To be located at: tests/e2e/mock_cli.py
"""
import os
import sys
import json
import argparse
import time

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
    
    # 1. Noise Suppression
    print("[INFO] Running Noise Suppression (DeepFilterNet)...")
    time.sleep(0.01)
    
    # 2. Speaker Diarization
    print("[INFO] Running Speaker Diarization (pyannote-audio)...")
    time.sleep(0.01)
    
    # 3. Speech-to-Text (Whisper)
    print("[INFO] Running Speech-to-Text (Whisper)...")
    time.sleep(0.01)
    print("[INFO] GPU VRAM cleared (torch.cuda.empty_cache called).")
    
    # 4. Translation
    print(f"[INFO] Translating transcript to {args.target_lang} using Ollama with Glossary...")
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
    
    # Write a dummy transparent WebM (mocked content)
    with open(out_webm, "wb") as f:
        f.write(b"MOCK_WEBM_VP9_ALPHA_DATA")
        
    # Write a dummy SRT
    with open(out_srt, "w", encoding="utf-8") as f:
        f.write("1\n00:00:01,000 --> 00:00:04,500\n[Mocked subtitle segment]\n\n")
        
    # Write timeline_shifts.json
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
