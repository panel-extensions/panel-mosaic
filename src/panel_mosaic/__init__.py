"""Accessible imports for the panel_mosaic package."""

import importlib.metadata
import warnings

from panel_mosaic.main import create_app

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError as e:  # pragma: no cover
    warnings.warn(f"Could not determine version of {__name__}\n{e!s}", stacklevel=2)
    __version__ = "unknown"

__all__: list[str] = [
    "__version__",
    "create_app",
]
