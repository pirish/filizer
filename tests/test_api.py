import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import main
from main import app, get_current_username, FileModel

# Override auth for tests
def override_auth():
    return "admin"

app.dependency_overrides[get_current_username] = override_auth

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert "Filizer Dashboard" in response.text

@patch("main.engine")
def test_crud_file(mock_engine):
    # Setup mocks
    mock_engine.save = AsyncMock()
    mock_engine.find_many = AsyncMock()
    mock_engine.find_one = AsyncMock()
    mock_engine.delete = AsyncMock()
    
    unique_name = "test_file.txt"
    file_id = "507f1f77bcf86cd799439011"
    
    # Mock find_many return
    # Create model instance. DbModel typically allows id/_id.
    # We will set it after creation if needed or assume it works.
    mock_file = FileModel(
        name=unique_name,
        size=100,
        kind="text",
        md5="abc",
        parent_dir="/tmp",
        full_path="/tmp/test_file.txt",
        duplicate=False
    )
    # Manually set id as if it came from DB
    mock_file.id = file_id 
    
    mock_engine.find_many.return_value = [mock_file]
    mock_engine.find_one.return_value = mock_file
    
    # Create
    file_data = {
        "name": unique_name,
        "size": 100,
        "kind": "text",
        "md5": "abc",
        "parent_dir": "/tmp",
        "full_path": "/tmp/test_file.txt",
        "duplicate": False
    }
    response = client.post("/api/v1/files/", json=file_data)
    assert response.status_code == 200
    
    # List
    response = client.get(f"/api/v1/files/?name={unique_name}")
    assert response.status_code == 200
    files = response.json()
    assert len(files) == 1
    assert files[0]["name"] == unique_name
    
    # Get by ID
    response = client.get(f"/api/v1/files/{file_id}")
    assert response.status_code == 200
    
    # Update
    mock_engine.save.reset_mock()
    action_data = {"action": "archive"}
    response = client.put(f"/api/v1/files/{file_id}/action", json=action_data)
    assert response.status_code == 200
    
    # Delete
    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 1
    mock_engine.delete.return_value = mock_delete_result
    
    response = client.delete(f"/api/v1/files/{file_id}")
    assert response.status_code == 200


@patch("main.engine")
def test_reports(mock_engine):
    # Mock aggregation
    mock_collection = MagicMock()
    # Mock dictionary access for collection
    mock_engine._db.__getitem__.return_value = mock_collection
    
    mock_cursor = AsyncMock()
    mock_collection.aggregate.return_value = mock_cursor
    
    mock_cursor.to_list.return_value = [
        {
            "_id": "md5hash",
            "count": 2,
            "files": [
                {"name": "f1", "_id": "id1", "size": 10, "full_path": "p1"},
                {"name": "f2", "_id": "id2", "size": 10, "full_path": "p2"}
            ],
            "total_size": 20
        }
    ]
    
    response = client.get("/reports")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["_id"] == "md5hash"