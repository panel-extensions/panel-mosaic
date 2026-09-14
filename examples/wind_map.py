"""An interactive Mosaic wind map embedded in a Panel application."""

import duckdb
import panel as pn

from panel_mosaic import Mosaic

pn.extension(sizing_mode="stretch_width")

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

spec = {
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

pn.Column(
    "# Interactive wind map",
    "Drag over the map or legend to select wind speeds, then adjust vector length.",
    Mosaic(spec, con=con),
).servable()
