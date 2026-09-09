# Examples

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
