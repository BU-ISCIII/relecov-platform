"""Utility helpers to resolve lab codes to display information."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

try:
    from importlib import resources
except ImportError:  # pragma: no cover
    import importlib_resources as resources  # type: ignore


CATALOG_PACKAGE = "relecov_tools.conf"
CATALOG_FILENAME = "laboratory_address.json"


class LabCatalogError(RuntimeError):
    """Raised when the laboratory catalog cannot be loaded."""


def _resolve_catalog_path() -> Path:
    """Return the path to the catalog JSON, using multiple fallbacks."""

    custom_path = os.getenv("LABORATORY_ADDRESS_JSON")
    if custom_path:
        candidate = Path(custom_path)
        if candidate.exists():
            return candidate
        raise LabCatalogError(
            f"Laboratory catalog file defined in LABORATORY_ADDRESS_JSON not found: {candidate}"
        )

    try:
        file_ref = resources.files(CATALOG_PACKAGE).joinpath(CATALOG_FILENAME)
    except ModuleNotFoundError:
        repo_root = Path(__file__).resolve().parents[2]
        candidate = (
            repo_root / "relecov-tools" / "relecov_tools" / "conf" / CATALOG_FILENAME
        )
        if not candidate.exists():
            candidate = (
                repo_root.parent
                / "relecov-tools"
                / "relecov_tools"
                / "conf"
                / CATALOG_FILENAME
            )
    except (AttributeError, FileNotFoundError):  # pragma: no cover - Py<3.9
        try:
            file_ref = resources.files(CATALOG_PACKAGE) / CATALOG_FILENAME  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise LabCatalogError(
                "Unable to resolve laboratory catalog file from relecov_tools"
            ) from exc
        else:
            candidate = Path(file_ref)
    else:
        candidate = Path(file_ref)

    if candidate.exists():
        return candidate
    raise LabCatalogError(f"Laboratory catalog file not found: {candidate}")


@lru_cache(maxsize=1)
def _load_catalog() -> Dict[str, Dict[str, str]]:
    """Return the raw catalog keyed by collecting_institution_code_1."""

    path = _resolve_catalog_path()
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    catalog: Dict[str, Dict[str, str]] = {}
    for entry in payload.values():
        code = (entry.get("collecting_institution_code_1") or "").strip()
        if not code:
            continue
        catalog[code] = entry
    if not catalog:
        raise LabCatalogError("Laboratory catalog is empty")
    return catalog


def get_catalog() -> Dict[str, Dict[str, str]]:
    """Expose the raw catalog (cached)."""

    return _load_catalog().copy()


def get_lab_entry(code: Optional[str]) -> Optional[Dict[str, str]]:
    """Return the catalog entry for the given lab code."""

    if not code:
        return None
    return _load_catalog().get(code)


def get_lab_name(code: Optional[str], default: str = "") -> str:
    """Return the display name for the provided lab code."""

    entry = get_lab_entry(code)
    if not entry:
        return default
    name = entry.get("collecting_institution")
    return name or default


@lru_cache(maxsize=1)
def _build_name_index() -> Dict[str, str]:
    """Construct a case-insensitive index to resolve codes by name."""

    index: Dict[str, str] = {}
    for code, entry in _load_catalog().items():
        name = entry.get("collecting_institution")
        if not name:
            continue
        index[name.lower()] = code
    return index


def get_lab_code(name: Optional[str]) -> Optional[str]:
    """Resolve a lab code from a display name (case-insensitive)."""

    if not name:
        return None
    return _build_name_index().get(name.lower())


def ensure_lab_display(code: Optional[str], fallback_name: Optional[str] = None) -> str:
    """Return the preferred display name for a lab code."""

    if not code:
        return fallback_name or ""
    display = get_lab_name(code)
    if display:
        return display
    return fallback_name or code
