# Filizer

Filizer is a web-based tool and API for managing file records and detecting duplicate files and directories. It provides a clean dashboard to visualize your file system state, search for specific files, and generate reports on duplicates.

## Features

- **Web Dashboard:** A simple UI to view file statistics, search for files, and manage actions.
- **Duplicate File Detection:** Identify duplicate files across your system based on MD5 hashes.
- **Duplicate Directory Detection:** Identify duplicate directories based on their file contents and names.
- **File Management API:** A full REST API to create, read, update, and delete file records.
- **Action Tracking:** Set and track actions (like `delete` or `archive`) on specific files.
- **Configurable Authentication:** Optional Basic Auth support via environment variables or TOML configuration.

## Requirements

- **Python:** 3.13 or higher.
- **Database:** MongoDB instance.

## Installation

Filizer uses `uv` for dependency management.

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd filizer
    ```

2.  **Install dependencies:**
    ```bash
    uv sync
    ```

3.  **Ensure MongoDB is running:**
    By default, Filizer connects to `mongodb://localhost:27017/files_db`.

## Configuration

Filizer can be configured using environment variables or a TOML file located at `~/.config/filizer/server-conf.toml`.

### Environment Variables

- `API_AUTH_ENABLED`: Set to `true` to enable Basic Authentication (default: `false`).
- `API_USERNAME`: The username for Basic Auth (default: `admin`).
- `API_PASSWORD`: The password for Basic Auth (default: `secret`).
- `MONGODB_URL`: The MongoDB connection string (default: `mongodb://localhost:27017`).
- `MONGODB_DB_NAME`: The MongoDB database name (default: `files_db`).

### TOML Configuration

Example `~/.config/filizer/server-conf.toml`:

```toml
[auth]
enabled = true
username = "myuser"
password = "mypassword"

[mongodb]
url = "mongodb://localhost:27017"
db_name = "files_db"
```

## Running the Application

To start the Filizer server:

```bash
uv run uvicorn server.main:app --host 0.0.0.0 --port 8000
```

The web dashboard will be available at `http://localhost:8000`.

## Deployment

### Helm

The server application can be deployed using Helm:

```bash
helm install filizer-server ./charts/filizer-server
```

See the [Helm chart directory](../charts/filizer-server) for more configuration options.

## API Documentation

The API is served under `/api/v1`.

- `GET /api/v1/files/`: List and search file records.
- `POST /api/v1/files/`: Add a new file record.
- `GET /api/v1/files/{id}`: Get details for a specific file.
- `DELETE /api/v1/files/{id}`: Delete a file record.
- `PUT /api/v1/files/{id}/action`: Set an action and arguments for a file.
- `GET /api/v1/stats`: Get global statistics (total files, total size).
- `GET /reports`: Generate duplicate file and directory reports.

## Testing

Run the test suite using `pytest`:

```bash
uv run pytest
```
