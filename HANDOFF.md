# HANDOFF.md

## Current status
* **Đã hoàn thành bước Design & Align (/grill-me)**: Thống nhất chuyển hướng dự án CodeAvatar sang mô hình **Lightweight MC Avatar Generator** tối ưu cho Laptop văn phòng không card rời (CPU-only).
* Đã tinh gọn lộ trình từ 5 Sprint cồng kềnh thành 3 Sprint tập trung:
  * **Sprint 1**: Lightweight CPU Lip-Sync Engine (Wav2Lip ONNX Quantized) & Transparent WebM Exporter.
  * **Sprint 2**: Minimalist FastAPI Local Backend.
  * **Sprint 3**: 1-Page Glassmorphic React Web UI (Crop ROI, Live Preview nền lưới caro, Download WebM).
* Đã cập nhật toàn bộ tài liệu kiến trúc dự án ([PROJECT.md](file:///home/thienvu/workspace/CodeAvatar/PROJECT.md), [implementation_plan.md](file:///home/thienvu/.gemini/antigravity/brain/faf31dd8-fa57-4b7c-a5fb-8394719dbbc4/implementation_plan.md)).

## Uncommitted state
* Các file tài liệu kiến trúc đã được cập nhật sẵn sàng. Chưa thực thi viết mã nguồn cho Sprint 1 theo yêu cầu review của người dùng.

## Gotchas/New decisions
* **Tối ưu CPU**: Dùng Wav2Lip ONNX Quantized INT8 (~85MB) kết hợp ROI Face Crop $96\times 96$ giúp giảm 100x dung lượng tính toán, RAM < 2GB.
* **Tự động tăng tốc GPU**: Tự động bật CUDA/DirectML nếu máy có card rời.
* **Xuất nền trong suốt**: Xuất chuẩn WebM VP9 Alpha (`yuva420p` + `alpha_mode=1`) để người dùng dễ dàng kéo-thả vào phần mềm Edit chuyên dụng (CapCut/Premiere).

## Next steps
1. Chờ người dùng review chi tiết toàn bộ kế hoạch và xác nhận bắt đầu thực thi.
2. Tiến hành thực thi **Sprint 1**: Viết module `cpu_lipsync.py`, `webm_exporter.py` và bộ test suite `pytest`.
