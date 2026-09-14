"""Panel component for interactive Mosaic and vgplot visualizations."""

from __future__ import annotations

import base64
import logging
from typing import Any

import duckdb
import param
import pyarrow as pa  # type: ignore[import-untyped]
from panel.custom import JSComponent

logger = logging.getLogger(__name__)

MOSAIC_VERSION = "0.31.0"
FLECHETTE_VERSION = "2.5.0"


class Mosaic(JSComponent):
    """Render a declarative Mosaic or vgplot specification in Panel.

    Mosaic sends SQL generated from ``spec`` to this component's DuckDB
    connection. The component returns only the query result, allowing linked,
    cross-filtered visualizations to operate on data too large to embed in the
    browser.

    Parameters
    ----------
    spec
        A Mosaic specification. Marks refer to tables with
        ``data: {from: <table_name>}``.
    con
        DuckDB connection used to run Mosaic queries. A new in-memory
        connection is created when omitted.
    data
        Frames to register on ``con``, keyed by the table names referenced by
        ``spec``.

    Examples
    --------
    >>> import duckdb
    >>> con = duckdb.connect()
    >>> _ = con.execute("CREATE TABLE points AS SELECT 1 AS x, 2 AS y")
    >>> pane = Mosaic(
    ...     {"plot": [{"mark": "dot", "data": {"from": "points"}, "x": "x", "y": "y"}]},
    ...     con=con,
    ... )
    >>> pane.connection is con
    True
    """

    params = param.Dict(
        default={},
        doc="""
        Live Mosaic parameters and selections, keyed by name. Each selection
        includes its current value and SQL predicate.
    """,
    )

    preagg_schema = param.String(
        default="",
        doc="""
        Schema where Mosaic may materialize pre-aggregated views. An empty
        value uses Mosaic's default schema.
    """,
    )

    spec = param.Dict(
        default={},
        doc="""
        Mosaic specification to render. Marks reference registered DuckDB
        tables through ``data: {from: <table_name>}``.
    """,
    )

    _esm = "mosaic.js"

    _importmap = {
        "imports": {
            "@uwdata/mosaic-spec": f"https://esm.sh/@uwdata/mosaic-spec@{MOSAIC_VERSION}",
            "@uwdata/flechette": f"https://esm.sh/@uwdata/flechette@{FLECHETTE_VERSION}",
        }
    }

    _stylesheets = ["mosaic.css"]

    def __init__(
        self,
        spec: dict[str, Any] | None = None,
        con: duckdb.DuckDBPyConnection | None = None,
        data: dict[str, Any] | None = None,
        **params: Any,
    ) -> None:
        if spec is not None:
            params["spec"] = spec
        super().__init__(**params)
        self._con = duckdb.connect() if con is None else con
        for name, frame in (data or {}).items():
            self._con.register(name, frame)

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """DuckDB connection queried by Mosaic."""
        return self._con

    def _handle_msg(self, msg: Any) -> None:
        """Answer a SQL request sent by Mosaic's browser runtime."""
        uuid = msg.get("uuid")
        command = msg.get("type")
        sql = msg.get("sql")
        try:
            if command == "arrow":
                self._send_msg({"type": "arrow", "uuid": uuid, "data": self._query_arrow(sql)})
            elif command == "exec":
                self._con.execute(sql)
                self._send_msg({"type": "exec", "uuid": uuid})
            elif command == "json":
                result = self._con.query(sql).df()
                self._send_msg({"type": "json", "uuid": uuid, "result": result.to_dict(orient="records")})
            else:
                raise ValueError(f"Unknown Mosaic query type {command!r}.")
        except Exception as exc:
            logger.exception("Mosaic query failed: %s", sql)
            self._send_msg({"error": str(exc), "uuid": uuid})

    def _query_arrow(self, sql: str) -> str:
        """Run ``sql`` and return its result as a base64 Arrow IPC stream."""
        result = self._con.query(sql).arrow()
        batches = result.to_batches() if isinstance(result, pa.Table) else result
        sink = pa.BufferOutputStream()
        with pa.ipc.new_stream(sink, result.schema) as writer:
            for batch in batches:
                writer.write_batch(batch)
        return base64.b64encode(sink.getvalue().to_pybytes()).decode("ascii")
