"""Panel components for Mosaic visualizations."""

import importlib.metadata
import warnings

from panel_mosaic.mosaic import Mosaic

try:
    __version__ = importlib.metadata.version("panel-mosaic-viz")
except importlib.metadata.PackageNotFoundError as e:  # pragma: no cover
    warnings.warn(f"Could not determine version of {__name__}\n{e!s}", stacklevel=2)
    __version__ = "unknown"

__all__: list[str] = [
    "__version__",
    "Mosaic",
]
