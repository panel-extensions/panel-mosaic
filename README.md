# ✨ panel-mosaic

[![CI](https://img.shields.io/github/actions/workflow/status/panel-extensions/panel-mosaic/ci.yml?style=flat-square&branch=main)](https://github.com/panel-extensions/panel-mosaic/actions/workflows/ci.yml)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/panel-mosaic?logoColor=white&logo=conda-forge&style=flat-square)](https://prefix.dev/channels/conda-forge/packages/panel-mosaic)
[![pypi-version](https://img.shields.io/pypi/v/panel-mosaic-viz.svg?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/panel-mosaic-viz)
[![python-version](https://img.shields.io/pypi/pyversions/panel-mosaic-viz?logoColor=white&logo=python&style=flat-square)](https://pypi.org/project/panel-mosaic-viz)


**Interactive, DuckDB-powered [Mosaic](https://idl.uw.edu/mosaic/) visualizations for [Panel](https://panel.holoviz.org/).**

Build linked, browser-interactive charts without embedding an entire dataset in the page. Mosaic sends SQL to DuckDB and returns only the results each view needs.

![Monthly revenue chart rendered with panel-mosaic](docs/assets/revenue-dashboard.jpg)

## Why panel-mosaic?

- **Declarative charts:** Render Mosaic and vgplot specifications directly in a Panel app.
- **DuckDB pushdown:** Keep large tables in DuckDB; only query results travel to the browser.
- **Linked exploration:** Coordinate multiple charts with selections and cross-filtering.

## Installation

The PyPI distribution is named `panel-mosaic-viz`:

```bash
pip install panel-mosaic-viz
```

## Quick start

Create `app.py` with a small DuckDB table and a stacked bar chart:

```python
import duckdb
import panel as pn

from panel_mosaic import Mosaic

pn.extension(sizing_mode="stretch_width")

con = duckdb.connect()
con.execute("""
    CREATE TABLE monthly_revenue AS
    SELECT * FROM (
        VALUES
            ('Jan', 'North', 48), ('Jan', 'Central', 39), ('Jan', 'South', 42),
            ('Feb', 'North', 55), ('Feb', 'Central', 45), ('Feb', 'South', 49),
            ('Mar', 'North', 46), ('Mar', 'Central', 40), ('Mar', 'South', 44),
            ('Apr', 'North', 61), ('Apr', 'Central', 48), ('Apr', 'South', 52),
            ('May', 'North', 65), ('May', 'Central', 52), ('May', 'South', 56),
            ('Jun', 'North', 58), ('Jun', 'Central', 47), ('Jun', 'South', 50),
            ('Jul', 'North', 72), ('Jul', 'Central', 55), ('Jul', 'South', 58),
            ('Aug', 'North', 66), ('Aug', 'Central', 52), ('Aug', 'South', 54),
            ('Sep', 'North', 79), ('Sep', 'Central', 60), ('Sep', 'South', 64),
            ('Oct', 'North', 89), ('Oct', 'Central', 69), ('Oct', 'South', 70),
            ('Nov', 'North', 74), ('Nov', 'Central', 58), ('Nov', 'South', 60),
            ('Dec', 'North', 85), ('Dec', 'Central', 66), ('Dec', 'South', 69)
    ) AS t(month, region, revenue)
""")

spec = {
    "width": 900,
    "height": 480,
    "marginLeft": 72,
    "marginBottom": 48,
    "xLabel": "Month",
    "yLabel": "Revenue (USD thousands)",
    "yGrid": "#e5e7eb",
    "colorScheme": "Tableau10",
    "plot": [{
        "mark": "barY",
        "data": {"from": "monthly_revenue"},
        "x": "month",
        "y": "revenue",
        "fill": "region",
        "stroke": "white",
        "strokeWidth": 1,
    }],
}

pn.Column(
    "# Monthly revenue dashboard",
    "Explore regional revenue with a Mosaic chart backed by DuckDB.",
    Mosaic(spec, con=con),
).servable()
```

Run the app:

```bash
panel serve app.py --show
```

## How it works

`Mosaic` is a Panel `JSComponent`. It renders the declarative chart specification in the browser and services Mosaic's SQL requests through its DuckDB connection. You can either pass an existing DuckDB connection with `con=` or register in-memory frames with `data={"table_name": dataframe}`.

See the [documentation](https://panel-extensions.github.io/panel-mosaic/) for API details and more examples.

## Development

```bash
git clone https://github.com/panel-extensions/panel-mosaic
cd panel-mosaic
```

For a simple setup use [`uv`](https://docs.astral.sh/uv/):

```bash
uv venv
source .venv/bin/activate # on linux. Similar commands for windows and osx
uv pip install -e .[dev]
pre-commit run install
pytest tests
```

For the full Github Actions setup use [pixi](https://pixi.sh):

```bash
pixi run pre-commit-install
pixi run postinstall
pixi run test
```

This repository is based on [copier-template-panel-extension](https://github.com/panel-extensions/copier-template-panel-extension) (you can create your own Panel extension with it)!

To update to the latest template version run:

```bash
pixi exec --spec copier --spec ruamel.yaml -- copier update --defaults --trust
```

Note: `copier` will show `Conflict` for files with manual changes during an update. This is normal. As long as there are no merge conflict markers, all patches applied cleanly.

## ❤️ Contributing

Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/YourFeature`.
3. Make your changes and commit them: `git commit -m 'Add some feature'`.
4. Push to the branch: `git push origin feature/YourFeature`.
5. Open a pull request.

Please ensure your code adheres to the project's coding standards and passes all tests.
