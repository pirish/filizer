# Filizer Monorepo

This monorepo contains both the Filizer Client and Server applications.

## Structure

- `client/`: The CLI application for syncing files.
- `server/`: The FastAPI server for managing file data.

## Setup

This project uses `uv` for dependency management. Dependencies are managed at the root level.

To install dependencies:
```bash
uv sync
```

## Testing

To run all tests:
```bash
uv run pytest
```

Individual application READMEs can be found in their respective directories:
- [Client README](client/README.md)
- [Server README](server/README.md)

## Versioning Policy

Filizer follows Semantic Versioning (SemVer) for both the client and server.

- **Client-to-Server Compatibility**: The client verifies the server version before starting a scan.
- **Server-to-Client Compatibility**: The server checks the `X-Client-Version` header in every request and will reject clients that are below the minimum required version.
- **Minimum Versions**: `MIN_CLIENT_VERSION` and `MIN_SERVER_VERSION` are defined in `common/models.py`.

Upgrading to a new major version may require updating both the client and server.
