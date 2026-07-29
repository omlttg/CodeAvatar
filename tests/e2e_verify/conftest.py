"""
Verification Pytest conftest.py for e2e tests.
To be located at: tests/e2e_verify/conftest.py
Provides fixtures for intercepting CLI calls, starting mock FastAPI backend TestClient,
setting up environment test sandbox folders, and dynamically mocking heavy AI dependencies.
"""
import os
import sys
import shutil
import subprocess
import pytest
from unittest.mock import patch, MagicMock

# Dynamic Mocking of heavy AI dependencies at the module level.
mock_modules = [
    "whisper",
    "torch",
    "torch.cuda",
    "TTS",
    "TTS.api"
]
for module_name in mock_modules:
    if module_name not in sys.modules:
        sys.modules[module_name] = MagicMock()

# Import TestClient and verify app
from fastapi.testclient import TestClient
from tests.e2e_verify.mock_backend import app, TEST_DIR, DB_PATH, init_db

@pytest.fixture(scope="session", autouse=True)
def test_sandbox():
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR, exist_ok=True)
    init_db()
    yield
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

@pytest.fixture
def api_client():
    with TestClient(app) as client:
        yield client

@pytest.fixture(autouse=True)
def intercept_pipeline_cli():
    original_run = subprocess.run
    original_popen = subprocess.Popen
    mock_cli_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_cli.py")

    def mock_run(args, *run_args, **run_kwargs):
        if isinstance(args, list) and any("pipeline_cli.py" in str(arg) for arg in args):
            new_args = []
            for arg in args:
                if arg in ["python", "python3"]:
                    new_args.append(sys.executable)
                elif "pipeline_cli.py" in str(arg):
                    new_args.append(mock_cli_path)
                else:
                    new_args.append(arg)
            args = new_args
        return original_run(args, *run_args, **run_kwargs)

    def mock_popen(args, *popen_args, **popen_kwargs):
        if isinstance(args, list) and any("pipeline_cli.py" in str(arg) for arg in args):
            new_args = []
            for arg in args:
                if arg in ["python", "python3"]:
                    new_args.append(sys.executable)
                elif "pipeline_cli.py" in str(arg):
                    new_args.append(mock_cli_path)
                else:
                    new_args.append(arg)
            args = new_args
        return original_popen(args, *popen_args, **popen_kwargs)

    with patch("subprocess.run", side_effect=mock_run), patch("subprocess.Popen", side_effect=mock_popen):
        yield

@pytest.fixture
def mock_google_drive_api():
    with patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock_build.return_value
        mock_files = mock_service.files.return_value
        mock_files.create.return_value.execute.return_value = {
            "id": "mock_google_drive_file_id_56789",
            "name": "output_alpha.webm"
        }
        mock_files.get_media.return_value.execute.return_value = b"MOCK_GOOGLE_DRIVE_DOWNLOADED_DATA"
        yield mock_service
