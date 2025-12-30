import pytest
from pathlib import Path
from file_sync import get_md5, load_config
import requests
import requests_mock

def test_server_unreachable(caplog):
    """Test that the script logs an error and continues when the server is down."""
    with requests_mock.Mocker() as m:
        m.get("https://api.example.com/files", exc=requests.exceptions.ConnectTimeout)
        # Call your process_directory function here
        # Assert that 'Server unreachable' appears in caplog.text

def test_md5_calculation(tmp_path):
    """Test that MD5 hashing works correctly on a dummy file."""
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text("hello world")
    
    # MD5 of "hello world" is 5eb63bbbe01eeed093cb22bb8f5acdc3
    assert get_md5(p) == "5eb63bbbe01eeed093cb22bb8f5acdc3"

def test_config_loading_no_file(monkeypatch):
    """Test that load_config handles missing files gracefully."""
    # Mock Path.home to a temporary directory to ensure no config exists
    monkeypatch.setattr(Path, "home", lambda: Path("/tmp/nonexistent_filizer_path"))
    config = load_config()
    assert isinstance(config, dict)
    #assert len(config) == 0