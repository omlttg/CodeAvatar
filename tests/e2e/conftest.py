"""
Pytest conftest.py for e2e tests.
To be located at: tests/e2e/conftest.py
Provides fixtures for intercepting CLI calls, starting mock FastAPI backend TestClient,
and setting up environment test sandbox folders.
"""
import os
import shutil
import subprocess
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from tests.e2e.mock_backend import app, TEST_DIR, DB_PATH, init_db

@pytest.fixture(scope="session", autouse=True)
def test_sandbox():
    # Setup test sandbox directory inside workspace
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR, exist_ok=True)
    init_db()
    yield
    # Cleanup sandbox directory after session
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

@pytest.fixture
def api_client():
    # FastAPI TestClient to test backend endpoints synchronously and asynchronously
    with TestClient(app) as client:
        yield client

@pytest.fixture(autouse=True)
def intercept_pipeline_cli():
    """
    Autouse fixture that intercepts subprocess.run and subprocess.Popen calls targeting
    'services/pipeline/pipeline_cli.py' and redirects them to the mock CLI in tests/e2e/mock_cli.py.
    This guarantees no code under /services/ is executed or needed, keeping it isolated in /tests/.
    """
    original_run = subprocess.run
    original_popen = subprocess.Popen
    
    # Path of mock CLI to redirect to
    mock_cli_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_cli.py")

    def mock_run(args, *run_args, **run_kwargs):
        if isinstance(args, list) and any("pipeline_cli.py" in str(arg) for arg in args):
            new_args = []
            for arg in args:
                if "pipeline_cli.py" in str(arg):
                    new_args.append(mock_cli_path)
                else:
                    new_args.append(arg)
            args = new_args
        return original_run(args, *run_args, **run_kwargs)

    def mock_popen(args, *popen_args, **popen_kwargs):
        if isinstance(args, list) and any("pipeline_cli.py" in str(arg) for arg in args):
            new_args = []
            for arg in args:
                if "pipeline_cli.py" in str(arg):
                    new_args.append(mock_cli_path)
                else:
                    new_args.append(arg)
            args = new_args
        return original_popen(args, *popen_args, **popen_kwargs)

    with patch("subprocess.run", side_effect=mock_run), patch("subprocess.Popen", side_effect=mock_popen):
        yield

@pytest.fixture
def mock_google_drive_api():
    """
    Mocks standard responses for googleapiclient.discovery.build calls
    to isolate Drive storage testing without actual external network connection.
    """
    with patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock_build.return_value
        mock_files = mock_service.files.return_value
        
        # Mock file creation/upload
        mock_files.create.return_value.execute.return_value = {
            "id": "mock_google_drive_file_id_56789",
            "name": "output_alpha.webm"
        }
        
        # Mock file download
        mock_files.get_media.return_value.execute.return_value = b"MOCK_GOOGLE_DRIVE_DOWNLOADED_DATA"
        yield mock_service
