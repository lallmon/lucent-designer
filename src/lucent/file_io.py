"""File I/O for .lucent document format.

Handles saving and loading Lucent documents to/from JSON files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Union

# Current file format version - increment when format changes
LUCENT_VERSION = 1


class FileVersionError(Exception):
    """Raised when file version is incompatible with this version of Lucent."""

    def __init__(self, file_version: int, supported_version: int) -> None:
        self.file_version = file_version
        self.supported_version = supported_version
        super().__init__(
            f"File version {file_version} is not supported. "
            f"Maximum supported version is {supported_version}. "
            f"Please update Lucent to open this file."
        )


def save_document(
    path: Union[str, Path],
    items: List[Dict[str, Any]],
    viewport: Dict[str, Any],
    meta: Dict[str, Any],
) -> None:
    """Save a Lucent document to disk.

    Args:
        path: File path to save to (string or Path object)
        items: List of canvas item dictionaries
        viewport: Viewport state (zoomLevel, offsetX, offsetY)
        meta: Document metadata (name, created, modified timestamps)

    Raises:
        OSError: If file cannot be written
    """
    file_path = Path(path)

    document = {
        "version": LUCENT_VERSION,
        "meta": meta,
        "viewport": viewport,
        "items": items,
    }

    file_path.write_text(json.dumps(document, indent=2), encoding="utf-8")


def load_document(path: Union[str, Path]) -> Dict[str, Any]:
    """Load a Lucent document from disk.

    Args:
        path: File path to load from (string or Path object)

    Returns:
        Dictionary containing:
        - items: List of canvas item dictionaries
        - viewport: Viewport state dictionary
        - meta: Document metadata dictionary

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file contains invalid JSON or missing required fields
        FileVersionError: If file version is newer than supported
    """
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        content = file_path.read_text(encoding="utf-8")
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file: {e}") from e

    # Validate version
    if "version" not in data:
        raise ValueError("Missing version field in document")

    file_version = data["version"]
    if not isinstance(file_version, int):
        raise ValueError(f"Invalid version field: {file_version}")

    if file_version > LUCENT_VERSION:
        raise FileVersionError(file_version, LUCENT_VERSION)

    meta = data.get("meta", {"name": "Untitled"})
    # Default documentDPI to 72 if not present
    if "documentDPI" not in meta:
        meta["documentDPI"] = 72

    return {
        "items": data.get("items", []),
        "viewport": data.get(
            "viewport", {"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0}
        ),
        "meta": meta,
    }
