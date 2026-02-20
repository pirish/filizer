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
