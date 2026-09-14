"""Browser tests for interactive Mosaic specifications."""

import duckdb
import pytest

pytest.importorskip("playwright")

from panel.tests.util import serve_component
from playwright.sync_api import expect

from panel_mosaic import Mosaic

pytestmark = pytest.mark.ui


AXES_SPEC = {
    "plot": [
        {"mark": "gridY", "strokeDasharray": "0.75 2", "strokeOpacity": 1},
        {"mark": "axisY", "anchor": "left", "tickSize": 0, "dx": 38, "dy": -4, "lineAnchor": "bottom"},
        {"mark": "axisY", "anchor": "right", "tickSize": 0, "tickPadding": 5, "label": "y-axis", "labelAnchor": "center"},
        {"mark": "axisX", "label": "x-axis", "labelAnchor": "center"},
        {"mark": "gridX"},
        {"mark": "ruleY", "data": [0]},
    ],
    "xDomain": [0, 100],
    "yDomain": [0, 100],
    "xInsetLeft": 36,
    "marginLeft": 0,
    "marginRight": 35,
    "width": 680,
}


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


def test_renders_axis_and_grid_marks(page):
    """Render Mosaic's standalone axis and grid marks."""
    serve_component(page, Mosaic(AXES_SPEC))

    expect(page.locator(".mosaic-pane svg")).to_have_count(1, timeout=15_000)
    expect(page.locator(".mosaic-pane-error")).to_have_count(0)


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
