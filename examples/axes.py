"""Customized Mosaic axes and gridlines in a Panel application."""

import panel as pn

from panel_mosaic import Mosaic

pn.extension(sizing_mode="stretch_width")

spec = {
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

pn.Column(
    "# Axes and gridlines",
    "Mosaic axis and grid marks can be composed with a Panel application.",
    Mosaic(spec),
).servable()
