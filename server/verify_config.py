import os
import secrets
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import config

# Mock DB calls globally before import main (though we import main inside test to allow reloading?)
# For this test, we need to reload config to test different scenarios.
# We'll use 'importlib.reload' to reload the config module.

import importlib
import main
from main import app

main.engine.find_many = AsyncMock(return_value=[])
main.engine.save = AsyncMock(return_value=None)
main.engine.find_one = AsyncMock(return_value=None)

client = TestClient(app)

def setup_config_file(content: str):
    config_dir = Path.home() / ".config" / "filizer"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "server-conf.toml"
    with open(config_file, "w") as f:
        f.write(content)
    return config_file

def cleanup_config_file():
    config_file = Path.home() / ".config" / "filizer" / "server-conf.toml"
    if config_file.exists():
        config_file.unlink()

def reload_app():
    importlib.reload(config)
    importlib.reload(main)
    # Re-apply mocks after reload
    main.engine.find_many = AsyncMock(return_value=[])
    main.engine.save = AsyncMock(return_value=None)
    main.engine.find_one = AsyncMock(return_value=None)
    return TestClient(main.app)

def test_config():
    print("--- Starting Config Verification ---")
    
    # Clean env vars
    os.environ.pop("API_AUTH_ENABLED", None)
    os.environ.pop("API_USERNAME", None)
    os.environ.pop("API_PASSWORD", None)
    cleanup_config_file()

    # 1. Test Defaults (Auth Disabled)
    print("\n[TEST 1] Defaults")
    client = reload_app()
    res = client.get("/files/")
    if res.status_code == 200:
        print("PASS: Access granted (Default: Auth Disabled).")
    else:
        print(f"FAIL: Expected 200, got {res.status_code}.")

    # 2. Test TOML Config (Auth Enabled)
    print("\n[TEST 2] TOML Config (Auth Enabled)")
    toml_content = """
[auth]
enabled = true
username = "tomluser"
password = "tomlpassword"
"""
    setup_config_file(toml_content)
    
    client = reload_app()
    
    # Should fail without credentials
    res = client.get("/files/")
    if res.status_code == 401:
        print("PASS: Auth enforced by TOML.")
    else:
        print(f"FAIL: Expected 401, got {res.status_code}.")
    
    # Should succeed with TOML credentials
    res = client.get("/files/", auth=("tomluser", "tomlpassword"))
    if res.status_code == 200:
        print("PASS: Access granted with TOML credentials.")
    else:
        print(f"FAIL: Expected 200 with toml creds, got {res.status_code}.")

    # 3. Test Env Var Override (Env > TOML)
    print("\n[TEST 3] Env Var Override (Env > TOML)")
    os.environ["API_AUTH_ENABLED"] = "true"
    os.environ["API_USERNAME"] = "envuser"
    os.environ["API_PASSWORD"] = "envpassword"
    
    client = reload_app()
    
    # Should fail with TOML credentials now
    res = client.get("/files/", auth=("tomluser", "tomlpassword"))
    if res.status_code == 401:
        print("PASS: TOML credentials rejected when overridden.")
    else:
        print(f"FAIL: Expected 401 for valid TOML creds (should be overridden), got {res.status_code}.")

    # Should succeed with Env credentials
    res = client.get("/files/", auth=("envuser", "envpassword"))
    if res.status_code == 200:
        print("PASS: Access granted with Env credentials.")
    else:
        print(f"FAIL: Expected 200 with env creds, got {res.status_code}.")

    # Cleanup
    cleanup_config_file()
    os.environ.pop("API_AUTH_ENABLED", None)
    os.environ.pop("API_USERNAME", None)
    os.environ.pop("API_PASSWORD", None)
    print("\nModification verification complete.")

if __name__ == "__main__":
    try:
        test_config()
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
