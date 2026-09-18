"""Tests for the Mosaic Panel component."""

import base64
import io
from pathlib import Path

import duckdb
import pyarrow as pa
import pytest

from panel_mosaic import Mosaic

SPEC = {"plot": [{"mark": "dot", "data": {"from": "points"}, "x": "x", "y": "y"}]}


@pytest.fixture
def pane():
    """Mosaic pane over a small DuckDB table, with browser replies captured."""
    con = duckdb.connect()
    con.execute("CREATE TABLE points AS SELECT * FROM (VALUES (1, 10.0), (2, 20.0), (3, 30.0)) AS t(x, y)")
    pane = Mosaic(SPEC, con=con)
    pane._sent = []
    pane._send_msg = pane._sent.append
    return pane


def test_holds_spec_and_uses_supplied_connection(pane):
    assert pane.spec == SPEC
    assert pane.ready is False
    assert pane.responsive is False
    assert pane.error == ""
    assert pane.connection.query("SELECT count(*) FROM points").fetchone()[0] == 3


def test_can_opt_in_to_responsive_layout():
    pane = Mosaic(SPEC, responsive=True)

    assert pane.responsive is True


def test_registers_data_on_a_new_connection():
    table = pa.table({"x": [1, 2], "y": [3, 4]})
    pane = Mosaic(SPEC, data={"points": table})

    assert pane.connection.query("SELECT sum(y) FROM points").fetchone()[0] == 7


def test_arrow_query_round_trips_as_base64_ipc(pane):
    pane._handle_msg({"type": "arrow", "uuid": "q1", "sql": "SELECT * FROM points ORDER BY x"})

    msg = pane._sent[-1]
    assert msg["type"] == "arrow"
    assert msg["uuid"] == "q1"
    table = pa.ipc.open_stream(io.BytesIO(base64.b64decode(msg["data"]))).read_all()
    assert table.to_pydict() == {"x": [1, 2, 3], "y": [10.0, 20.0, 30.0]}


def test_json_query_returns_records(pane):
    pane._handle_msg({"type": "json", "uuid": "q2", "sql": "SELECT count(*) AS n FROM points"})

    assert pane._sent[-1] == {"type": "json", "uuid": "q2", "result": [{"n": 3}]}


def test_exec_query_runs_statement(pane):
    pane._handle_msg({"type": "exec", "uuid": "q3", "sql": "CREATE TABLE derived AS SELECT 1 AS value"})

    assert pane._sent[-1] == {"type": "exec", "uuid": "q3"}
    assert pane.connection.query("SELECT value FROM derived").fetchone()[0] == 1


@pytest.mark.parametrize(
    "msg",
    [
        {"type": "arrow", "uuid": "bad-sql", "sql": "SELECT * FROM does_not_exist"},
        {"type": "nonsense", "uuid": "bad-type", "sql": "SELECT 1"},
    ],
)
def test_failed_query_replies_with_an_error_and_uuid(pane, msg):
    pane._handle_msg(msg)

    reply = pane._sent[-1]
    assert reply["uuid"] == msg["uuid"]
    assert reply["error"]


def test_esm_module_is_packaged():
    esm = Mosaic._esm_path(compiled=False)

    assert esm is not None and esm.is_file()
    assert "@uwdata/mosaic-spec" in esm.read_text()


def test_stylesheet_is_packaged():
    stylesheet = Path(__file__).parents[1] / "src" / "panel_mosaic" / Mosaic._stylesheets[0]

    assert stylesheet.is_file()


def test_importmap_uses_a_single_mosaic_entry_point():
    imports = Mosaic._process_importmap()["imports"]

    mosaic_imports = {name for name in imports if name.startswith("@uwdata/")}
    assert mosaic_imports == {"@uwdata/mosaic-spec", "@uwdata/flechette"}
