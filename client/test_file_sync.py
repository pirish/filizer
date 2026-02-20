import pytest
import os
import logging
from pathlib import Path
from unittest.mock import patch
from file_sync import get_md5, load_config, process_directory, DuplicateStatus
import requests
import requests_mock

def test_duplicate_contents_detection(tmp_path, caplog):
    """Test that a file with same MD5 but different name/path is detected as DUPLICATE_CONTENTS."""
    caplog.set_level(logging.INFO)
    
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    file_path = test_dir / "new_name.txt"
    file_path.write_text("content")
    md5 = get_md5(file_path)

    api_url = "https://api.example.com/files"
    
    with requests_mock.Mocker() as m:
        m.get(api_url, json=[{
            "name": "old_name.txt",
            "parent_dir": "old_dir",
            "full_path": "/some/old/path/old_name.txt",
            "md5": md5
        }])
        mock_post = m.post(api_url, status_code=201)

        process_directory(str(test_dir), api_url, token="test-token", dry_run=False, force=False, excludes=[])

    assert "Duplicate Contents Found:   1" in caplog.text
    assert "New Files Posted:           0" in caplog.text
    assert mock_post.called
    assert mock_post.last_request.json()["duplicate_status"] == "DUPLICATE_CONTENTS"


def test_duplicate_file_detection(tmp_path, caplog):
    """Test that a file with same MD5, name and parent_dir is detected as DUPLICATE."""
    caplog.set_level(logging.INFO)
    
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    file_path = test_dir / "file.txt"
    file_path.write_text("content")
    md5 = get_md5(file_path)

    api_url = "https://api.example.com/files"
    
    with requests_mock.Mocker() as m:
        m.get(api_url, json=[{
            "name": "file.txt",
            "parent_dir": "test_dir",
            "full_path": "/some/other/path/file.txt", # Different full_path
            "md5": md5
        }])
        mock_post = m.post(api_url, status_code=201)

        process_directory(str(test_dir), api_url, token="test-token", dry_run=False, force=False, excludes=[])

    assert "Duplicate Files Found:      1" in caplog.text
    assert "New Files Posted:           0" in caplog.text
    assert not mock_post.called

# @patch('builtins.input', return_value='y')
# def test_previously_scanned_detection_skip(mock_input, tmp_path, caplog):
#     """Test that a file with same MD5 and full_path is detected as PREVIOUSLY_SCANNED and skips the directory."""
#     caplog.set_level(logging.DEBUG) # Use DEBUG level to see more logs
    
#     test_dir = tmp_path / "test_dir"
#     test_dir.mkdir()
#     file_path = test_dir / "file.txt"
#     file_path.write_text("content")
#     (test_dir / "another_file.txt").write_text("more content")
#     md5 = get_md5(file_path)

#     api_url = "https://api.example.com/files"
    
#     with requests_mock.Mocker() as m:
#         m.get(f"{api_url}?md5_eq={md5}", json=[{
#             "name": "file.txt",
#             "parent_dir": "test_dir",
#             "full_path": str(file_path),
#             "md5": md5
#         }])
#         # This second get should not be called if skipping works
#         mock_get2 = m.get(f"{api_url}?md5_eq={get_md5(test_dir / 'another_file.txt')}", json=[])
#         mock_post = m.post(api_url, status_code=201)

#         print(f"Processing directory: {test_dir}")
#         process_directory(str(test_dir), api_url, token="test-token", dry_run=False, force=False, excludes=[])
#         print(f"Finished processing directory. Log content:\n{caplog.text}")


#     assert "Previously Scanned Files:   1" in caplog.text
#     assert f"Skipping directory: {test_dir}" in caplog.text
#     assert not mock_post.called
#     assert not mock_get2.called

@patch('builtins.input', return_value='n')
def test_previously_scanned_detection_no_skip(mock_input, tmp_path, caplog):
    """Test that a file with same MD5 and full_path is detected as PREVIOUSLY_SCANNED but does not skip the directory."""
    caplog.set_level(logging.INFO)
    
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    file_path = test_dir / "file.txt"
    file_path.write_text("content")
    another_file_path = test_dir / "another_file.txt"
    another_file_path.write_text("more content")
    md5 = get_md5(file_path)
    md5_2 = get_md5(another_file_path)

    api_url = "https://api.example.com/files"
    
    with requests_mock.Mocker() as m:
        m.get(f"{api_url}?md5_eq={md5}", json=[{
            "name": "file.txt",
            "parent_dir": "test_dir",
            "full_path": str(file_path),
            "md5": md5
        }])
        m.get(f"{api_url}?md5_eq={md5_2}", json=[]) # For the second file
        mock_post = m.post(api_url, status_code=201)

        process_directory(str(test_dir), api_url, token="test-token", dry_run=False, force=False, excludes=[])

    assert "Previously Scanned Files:   1" in caplog.text
    assert f"Skipping directory: {test_dir}" not in caplog.text
    assert "New Files Posted:           1" in caplog.text
    assert mock_post.called
    assert mock_post.last_request.json()["name"] == "another_file.txt"


# def test_server_unreachable(tmp_path, caplog):
#     """Test that the script logs an error and continues when the server is down."""
#     test_dir = tmp_path / "test_dir"
#     test_dir.mkdir()
#     (test_dir / "file.txt").write_text("content")

#     api_url = "https://api.example.com/files"

#     with requests_mock.Mocker() as m:
#         m.get(api_url, exc=requests.exceptions.ConnectTimeout)
#         try:
#             process_directory(str(test_dir), api_url, token="test-token", dry_run=False, force=False, excludes=[])
#         finally:
#             assert "Network error during validation" in caplog.text
#             assert "Failed Operations:          1" in caplog.text


def test_md5_calculation(tmp_path):
    """Test that MD5 hashing works correctly on a dummy file."""
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text("hello world")
    
    assert get_md5(p) == "5eb63bbbe01eeed093cb22bb8f5acdc3"

def test_config_loading(tmp_path):
    """Test that load_config handles missing files gracefully."""
    config_dir = tmp_path / ".config" / "filizer"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "cli-conf.toml"

    # Test with no config file
    with patch('file_sync.CONFIG_FILE', config_file):
        config = load_config()
        assert config == {}

    # Test with a config file
    config_content = """
url = "https://example.com/api"
token = "test-token"
"""
    config_file.write_text(config_content)
    with patch('file_sync.CONFIG_FILE', config_file):
        config = load_config()
        assert config["url"] == "https://example.com/api"
        assert config["token"] == "test-token"

@patch('builtins.input', return_value='y')
def test_marked_for_deletion_logic(mock_input, tmp_path, caplog):
    """Test MARKED_FOR_DELETION action creates marker, and subsequent scan prompts for removal."""
    caplog.set_level(logging.INFO)
    
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    file_path = test_dir / "file.txt"
    file_path.write_text("content")
    md5 = get_md5(file_path)

    api_url = "https://api.example.com/files"
    
    # 1. First scan: server returns MARKED_FOR_DELETION action
    with requests_mock.Mocker() as m:
        m.get(api_url, json=[{
            "name": "file.txt",
            "parent_dir": "test_dir",
            "full_path": str(file_path),
            "md5": md5,
            "action": "marked_for_deletion"
        }])
        
        process_directory(str(test_dir), api_url, token="test-token", dry_run=False, force=False, excludes=[])

    assert "ACTION: Created marker file" in caplog.text
    marker_file = test_dir / "MARKED_FOR_DELETION"
    assert marker_file.exists()

    # 2. Second scan: marker file exists, should prompt for removal
    caplog.clear()
    with requests_mock.Mocker() as m:
        # Mock GET to return something so it continues
        m.get(api_url, json=[]) 
        m.post(api_url, status_code=201)
        
        process_directory(str(test_dir), api_url, token="test-token", dry_run=False, force=False, excludes=[])

    assert f"Removed marker file: {marker_file}" in caplog.text
    assert not marker_file.exists()

@patch('builtins.input', return_value='n')
def test_marked_for_deletion_skip(mock_input, tmp_path, caplog):
    """Test that declining to delete MARKED_FOR_DELETION marker skips directory processing."""
    caplog.set_level(logging.INFO)
    
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "MARKED_FOR_DELETION").touch()
    (test_dir / "file.txt").write_text("content")

    api_url = "https://api.example.com/files"
    
    with requests_mock.Mocker() as m:
        m.get(api_url, json=[])
        process_directory(str(test_dir), api_url, token="test-token", dry_run=False, force=False, excludes=[])

    assert f"Skipping processing for directory {test_dir}" in caplog.text
    assert "New Files Posted:           0" in caplog.text
    # Ensure marker file still exists
    assert (test_dir / "MARKED_FOR_DELETION").exists()
