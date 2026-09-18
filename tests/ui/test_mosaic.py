"""Browser tests for interactive Mosaic specifications."""

import duckdb
import panel as pn
import pytest

pytest.importorskip("playwright")

from panel.tests.util import serve_component
from panel.tests.util import wait_until
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

    pane = Mosaic(WIND_MAP_SPEC, con=con)
    serve_component(page, pane)

    expect(page.locator(".mosaic-pane svg").first).to_be_visible(timeout=15_000)
    expect(page.locator(".mosaic-pane input[type=range]")).to_have_count(1)
    expect(page.locator(".mosaic-pane-error")).to_have_count(0)
    wait_until(lambda: pane.ready, page, timeout=15_000)
    assert pane.error == ""


def test_reports_browser_render_errors(page):
    """Synchronize Mosaic parser failures back to the Python component."""
    pane = Mosaic({"plot": [{"mark": "not-a-mosaic-mark"}]})

    serve_component(page, pane)

    expect(page.locator(".mosaic-pane-error")).to_be_visible(timeout=15_000)
    wait_until(lambda: bool(pane.error), page, timeout=15_000)
    assert pane.ready is False

    pane.spec = {"plot": [{"mark": "ruleY", "data": [0]}]}

    expect(page.locator(".mosaic-pane svg")).to_be_visible(timeout=15_000)
    wait_until(lambda: pane.ready, page, timeout=15_000)
    assert pane.error == ""


def test_reports_query_errors(page):
    """Synchronize DuckDB query failures back to the Python component."""
    pane = Mosaic({"plot": [{"mark": "dot", "data": {"from": "missing"}, "x": "x", "y": "y"}]})

    serve_component(page, pane)

    wait_until(lambda: bool(pane.error), page, timeout=15_000)
    assert "missing" in pane.error
    assert pane.ready is False


def test_stretch_both_fills_the_available_space(page):
    """Resize Mosaic plots to match a stretching Panel layout."""
    spec = {
        "params": {"threshold": 1},
        "vconcat": [
            {"input": "slider", "min": 0, "max": 5, "step": 1, "as": "$threshold"},
            {
                "plot": [{"mark": "ruleY", "data": [0]}],
                "width": 320,
                "height": 180,
            },
        ],
    }
    pane = Mosaic(spec, responsive=True, sizing_mode="stretch_both")
    layout = pn.Column(pane, width=800, height=600, sizing_mode="fixed")

    serve_component(page, layout)

    mosaic = page.locator(".mosaic-pane")
    chart = mosaic.locator("svg")
    expect(chart).to_be_visible(timeout=15_000)
    wait_until(lambda: pane.ready, page, timeout=15_000)
    wait_until(
        lambda: chart.bounding_box()["height"] >= 0.9 * mosaic.bounding_box()["height"],
        page,
        timeout=15_000,
    )

    mosaic_box = mosaic.bounding_box()
    chart_box = chart.bounding_box()
    assert chart_box["width"] >= 0.9 * mosaic_box["width"]
    assert chart_box["height"] >= 0.9 * mosaic_box["height"]

    slider = mosaic.locator("input[type=range]")
    slider.evaluate("el => { el.value = 4; el.dispatchEvent(new Event('input', {bubbles: true})) }")
    wait_until(lambda: pane.params["threshold"]["value"] == 4, page, timeout=15_000)


def test_linked_dashboard_fills_the_available_space(page):
    """Fit a multi-view layout like the dashboards embedded by Lumen."""
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE points AS
        SELECT i AS id, i % 10 AS x, (i * 7) % 13 AS y
        FROM range(100) AS t(i)
    """)
    spec = {
        "hconcat": [
            {
                "plot": [{"mark": "dot", "data": {"from": "points"}, "x": "x", "y": "y"}],
                "width": 420,
                "height": 300,
            },
            {
                "vconcat": [
                    {
                        "plot": [
                            {
                                "mark": "rectY",
                                "data": {"from": "points"},
                                "x": {"bin": "x"},
                                "y": {"count": None},
                            }
                        ],
                        "width": 260,
                        "height": 140,
                    },
                    {
                        "input": "table",
                        "from": "points",
                        "columns": ["id", "x", "y"],
                        "width": 260,
                        "height": 140,
                    },
                ]
            },
        ]
    }
    pane = Mosaic(spec, con=con, responsive=True, sizing_mode="stretch_both")
    layout = pn.Column(pane, width=900, height=600, sizing_mode="fixed")

    serve_component(page, layout)

    mosaic = page.locator(".mosaic-pane")
    expect(mosaic.locator("svg")).to_have_count(2, timeout=15_000)
    expect(mosaic.locator("table")).to_be_visible(timeout=15_000)
    wait_until(lambda: pane.ready, page, timeout=15_000)

    def coverage():
        return mosaic.evaluate("""
            el => {
              const nodes = [...el.querySelectorAll('.plot > svg, [id^="table-"]')]
              const rects = nodes.map(node => node.getBoundingClientRect())
              const box = el.getBoundingClientRect()
              return {
                width: (Math.max(...rects.map(r => r.right)) - Math.min(...rects.map(r => r.left))) / box.width,
                height: (Math.max(...rects.map(r => r.bottom)) - Math.min(...rects.map(r => r.top))) / box.height,
              }
            }
        """)

    wait_until(lambda: coverage()["width"] >= 0.85, page, timeout=15_000)
    wait_until(lambda: coverage()["height"] >= 0.85, page, timeout=15_000)
