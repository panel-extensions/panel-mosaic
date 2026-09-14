"""Browser tests for interactive Mosaic specifications."""

import duckdb
import pytest

pytest.importorskip("playwright")

from panel.tests.util import serve_component
from playwright.sync_api import expect

from panel_mosaic import Mosaic

pytestmark = pytest.mark.ui


WIND_MAP_SPEC = {
    "params": {"selected": {"select": "union"}, "length": 2},
    "vconcat": [
        {"legend": "color", "for": "wind-map", "label": "Speed (m/s)", "as": "$selected"},
        {
            "name": "wind-map",
            "plot": [
                {
                    "mark": "vector",
                    "data": {"from": "wind"},
                    "x": "longitude",
                    "y": "latitude",
                    "rotate": {"sql": "degrees(atan2(u, v))"},
                    "length": {"sql": "$length * sqrt(u * u + v * v)"},
                    "stroke": {"sql": "sqrt(u * u + v * v)"},
                    "channels": {"id": "id"},
                },
                {"select": "region", "as": "$selected", "channels": ["id"]},
                {"select": "highlight", "by": "$selected"},
            ],
            "lengthScale": "identity",
            "colorZero": True,
            "inset": 10,
            "aspectRatio": 1,
            "width": 680,
        },
        {"input": "slider", "min": 1, "max": 7, "step": 0.1, "as": "$length", "label": "Vector Length"},
    ],
}


def test_renders_interactive_wind_map(page):
    """Render Mosaic's linked vector-map, legend, and slider composition."""
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE wind AS
        SELECT
            row_number() OVER () AS id,
            longitude,
            latitude,
            sin(radians(longitude * 3)) AS u,
            cos(radians(latitude * 4)) AS v
        FROM range(-125, -114) AS x(longitude)
        CROSS JOIN range(32, 43) AS y(latitude)
    """)

    serve_component(page, Mosaic(WIND_MAP_SPEC, con=con))

    expect(page.locator(".mosaic-pane svg").first).to_be_visible(timeout=15_000)
    expect(page.locator(".mosaic-pane input[type=range]")).to_have_count(1)
    expect(page.locator(".mosaic-pane-error")).to_have_count(0)
