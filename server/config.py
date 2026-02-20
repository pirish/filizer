import os
import tomllib
from pathlib import Path
from pydantic import BaseModel

class AuthConfig(BaseModel):
    enabled: bool = False
    username: str = "admin"
    password: str = "secret"

class Settings(BaseModel):
    auth: AuthConfig = AuthConfig()
    mongodb_url: str = "mongodb://localhost:27017"
    db_name: str = "files_db"

def load_settings() -> Settings:
    # 1. Defaults
    config_data = {}
    
    # 2. TOML Config File
    config_path = Path.home() / ".config" / "filizer" / "server-conf.toml"
    if config_path.exists():
        try:
            with open(config_path, "rb") as f:
                toml_data = tomllib.load(f)
                # Deep merge logic for simple structure
                if "auth" in toml_data:
                    config_data["auth"] = toml_data["auth"]
                if "mongodb" in toml_data:
                    config_data["mongodb_url"] = toml_data["mongodb"].get("url")
                    config_data["db_name"] = toml_data["mongodb"].get("db_name")
        except Exception as e:
            print(f"Warning: Failed to parse config file at {config_path}: {e}")

    # 3. Environment Variables (Override)
    # We construct a dict to update the config_data
    auth_env = {}
    if os.getenv("API_AUTH_ENABLED") is not None:
        auth_env["enabled"] = os.getenv("API_AUTH_ENABLED").lower() == "true"
    if os.getenv("API_USERNAME") is not None:
        auth_env["username"] = os.getenv("API_USERNAME")
    if os.getenv("API_PASSWORD") is not None:
        auth_env["password"] = os.getenv("API_PASSWORD")
    
    if auth_env:
        # Ensure 'auth' key exists if we are overriding it
        if "auth" not in config_data:
            config_data["auth"] = {}
        config_data["auth"].update(auth_env)

    if os.getenv("MONGODB_URL") is not None:
        config_data["mongodb_url"] = os.getenv("MONGODB_URL")
    if os.getenv("MONGODB_DB_NAME") is not None:
        config_data["db_name"] = os.getenv("MONGODB_DB_NAME")

    return Settings(**config_data)

settings = load_settings()
