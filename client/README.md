# Filizer CLI

**Filizer** is a robust, Python-based file synchronization and management tool. It recursively scans directories, calculates MD5 hashes, and interacts with a central API to manage duplicates and execute remote file operations.



## 🚀 Features

* **Smart Sync**: Uses MD5 hashing to identify content duplicates across different paths.
* **Remote Actions**: Supports server-instructed file operations: `cp` (copy), `mv` (move), and `rm` (remove).
* **Fast Traversals**: Uses directory pruning to skip excluded folders (e.g., `.git`, `node_modules`) instantly.
* **Safety First**: Built-in `--dry-run` mode and confirmation prompts for file deletions.
* **Robust Networking**: Automatic exponential backoff retries for 5xx server errors.
* **Modern Config**: Supports TOML configuration files and environment variable overrides.

---

## 🛠 Installation

### Using the Binary
Download the standalone executable for your OS from the [Releases](#) page. No Python installation is required.

### From Source (using `uv`)
If you have [uv](https://github.com/astral-sh/uv) installed:

```bash
# Clone the repository
git clone [https://github.com/youruser/filizer.git](https://github.com/youruser/filizer.git)
cd filizer

# Run directly (uv handles dependencies automatically)
uv run file_sync.py --help
```