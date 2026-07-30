# TEST_INFRA — E2E Testing Infrastructure Specification

Tài liệu này chi tiết hóa triết lý kiểm thử, phân cấp bộ test suite 4 tầng, danh mục tính năng và hướng dẫn chạy test tự động cho dự án **CodeAvatar**.

---

## 1. Testing Philosophy

Hạ tầng kiểm thử E2E của CodeAvatar tuân thủ nguyên tắc **Opaque-Box Testing**:
* **Kiểm thử theo Yêu cầu (Requirements-Driven):** Các bài test kiểm tra trực tiếp tính năng (R1 đến R5) thay vì phụ thuộc vào chi tiết triển khai bên trong.
* **Mô phỏng Người dùng:** Giả lập thao tác người dùng thực tế qua API Backend FastAPI và luồng render Web UI.
* **Kiểm tra Xác định (Deterministic Assertions):** Đảm bảo đầu ra (video WebM Alpha nền trong suốt, mảng log SSE, file tải về) đạt 100% chuẩn định dạng và quy tắc bảo mật.
* **Kiểm soát Tài nguyên & Memory:** Theo dõi dung lượng RAM và tiến trình FFMPEG Stream Pipe để đảm bảo bộ nhớ luôn ở mức $O(1)$ ~150MB, không đơ máy.

---

## 2. 4-Tier Test Directory Structure

Bộ test suite tự động nằm trong `/tests/` được chia thành các tầng rõ ràng:

```text
/home/thienvu/workspace/CodeAvatar/
  ├── tests/
  │    ├── conftest.py                   # Pytest fixtures dùng chung
  │    ├── test_sprint1_vertical_slice.py # Tier 1: CPU Viseme, WebM Exporter, FastAPI & Security
  │    ├── test_sprint2_vertical_slice.py # Tier 2: GPU Engine, CPU Fallback, Hardware Switch & SSE Stream
  │    └── test_sprint3_vertical_slice.py # Tier 3: Crop ROI Canvas, Glassmorphic UI & End-to-End Integration
```

---

## 3. Automated Test Execution Commands

### 1. Run Full Test Suite (11/11 Passed)
```bash
.venv/bin/python -m pytest tests/ -v
```

### 2. Run Specific Test Tier
```bash
.venv/bin/python -m pytest tests/test_sprint1_vertical_slice.py -v
.venv/bin/python -m pytest tests/test_sprint2_vertical_slice.py -v
.venv/bin/python -m pytest tests/test_sprint3_vertical_slice.py -v
```
