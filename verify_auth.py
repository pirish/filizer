import os
import secrets
from fastapi.testclient import TestClient
from main import app

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
import main

# Mock DB calls to avoid Event Loop issues with global AsyncDbEngine
main.engine.find_many = AsyncMock(return_value=[])
main.engine.save = AsyncMock(return_value=None)
main.engine.find_one = AsyncMock(return_value=None)

client = TestClient(main.app)

def test_auth():
    print("--- Starting Verification ---")
    
    # 1. Test: Auth Disabled (Default) - Should succeed without headers
    # Note: Environment variables are read inside the dependency, so we can mock os.environ or just set it here if the server runs in process.
    # Since TestClient runs the app in the same process, modifying os.environ works if the app reads it dynamically.
    
    print("\n[TEST 1] Auth Disabled (API_AUTH_ENABLED='false')")
    os.environ["API_AUTH_ENABLED"] = "false"
    res = client.get("/files/")
    if res.status_code == 200:
        print("PASS: Access granted without auth.")
    else:
        print(f"FAIL: Expected 200, got {res.status_code}. Detail: {res.text}")

    # 2. Test: Auth Enabled, No Credentials
    print("\n[TEST 2] Auth Enabled (API_AUTH_ENABLED='true'), No Credentials")
    os.environ["API_AUTH_ENABLED"] = "true"
    # Resetting other vars to default for control
    os.environ.pop("API_USERNAME", None)
    os.environ.pop("API_PASSWORD", None)
    
    res = client.get("/files/")
    if res.status_code == 401:
        print("PASS: Access denied without credentials.")
    else:
        print(f"FAIL: Expected 401, got {res.status_code}. Detail: {res.text}")

    # 3. Test: Auth Enabled, Wrong Credentials
    print("\n[TEST 3] Auth Enabled, Wrong Credentials")
    res = client.get("/files/", auth=("wrong", "wrong"))
    if res.status_code == 401:
        print("PASS: Access denied with wrong credentials.")
    else:
        print(f"FAIL: Expected 401, got {res.status_code}. Detail: {res.text}")
        
    # 4. Test: Auth Enabled, Correct Credentials
    print("\n[TEST 4] Auth Enabled, Correct Credentials")
    # Defaults are admin/secret in code
    res = client.get("/files/", auth=("admin", "secret"))
    if res.status_code == 200:
        print("PASS: Access granted with correct credentials.")
    else:
        print(f"FAIL: Expected 200, got {res.status_code}. Detail: {res.text}")

if __name__ == "__main__":
    try:
        test_auth()
    except Exception as e:
        print(f"An error occurred: {e}")
