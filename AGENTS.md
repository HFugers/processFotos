# Repository guidance

## Current state
- The project is a Python application with `foto_sort.py` and `foto_wrapper.py`, external album assets under `web/`, a Pillow dependency, and `unittest` coverage.
- Read `README.md` before making changes and keep user-facing documentation in Dutch unless asked otherwise.

## Product requirements from the README
- The workflow has two parts: `FOTO_sort_app` organizes photos from a configurable parent directory (`raw_path`) into year-named folders, and `FOTO_wrapper_app` creates a browsable `index.html` in that parent directory.
- Determine a photo's year from a `yyyymmdd` date in its filename when available; otherwise use the photo's creation date.
- The generated album should show year tabs in descending year order and thumbnails around 250 px wide (a setting). Selecting a thumbnail opens a full-screen view with previous/next browsing and a Home button returning to the index.
- Keep generated links relative so the photo directory can be copied to another device or location. Keep CSS and JavaScript in separate files outside the generated index. Use styling suitable for a photo album.

## Development practices
- Preserve original photos and avoid destructive overwrite or deletion behavior unless explicitly requested.
- Handle malformed filenames, unreadable image metadata, and missing dates gracefully.
- Add or update tests when implementing functionality; document setup and execution commands in the README.

Use the most appropriate language available (golang or python)
uv is used as .venv and as package manager