# ✨ panel-mosaic

[![CI](https://img.shields.io/github/actions/workflow/status/panel-extensions/panel-mosaic/ci.yml?style=flat-square&branch=main)](https://github.com/panel-extensions/panel-mosaic/actions/workflows/ci.yml)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/panel-mosaic?logoColor=white&logo=conda-forge&style=flat-square)](https://prefix.dev/channels/conda-forge/packages/panel-mosaic)
[![pypi-version](https://img.shields.io/pypi/v/panel-mosaic-viz.svg?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/panel-mosaic-viz)
[![python-version](https://img.shields.io/pypi/pyversions/panel-mosaic-viz?logoColor=white&logo=python&style=flat-square)](https://pypi.org/project/panel-mosaic-viz)


A Panel extension for Mosaic visualizations backed by DuckDB.

## Features

- Render declarative [Mosaic](https://idl.uw.edu/mosaic/) and vgplot specifications in Panel.
- Query data in DuckDB from the browser, returning only aggregate results instead of embedding full tables in the page.
- Support linked views and cross-filtering through Mosaic selections.

## Pin your version!

This project is **in its early stages**, so if you find a version that suits your needs, it’s recommended to **pin your version**, as updates may introduce changes.

## Installation

Install it via `pip`:

```bash
pip install panel-mosaic-viz
```

## Usage

```python
import duckdb
import panel as pn

from panel_mosaic import Mosaic

pn.extension()

con = duckdb.connect()
con.execute("CREATE TABLE points AS SELECT * FROM (VALUES (1, 2), (2, 4), (3, 3)) AS t(x, y)")

Mosaic(
    {
        "plot": [
            {"mark": "dot", "data": {"from": "points"}, "x": "x", "y": "y"},
        ]
    },
    con=con,
).servable()
```

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
