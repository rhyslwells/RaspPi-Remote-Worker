#!/usr/bin/env python3
"""
GB grid dashboard (Dash). Read-only: it only ever opens grid.db with mode=ro.

Local test:
    python scripts/grid/seed_demo.py
    GRID_DB=data/grid_demo.db python scripts/grid/dashboard/app.py
    (PowerShell: $env:GRID_DB="data/grid_demo.db"; python scripts/grid/dashboard/app.py)

On the Pi it is served by gunicorn (``grid.dashboard.app:server``), never by the
development server below.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import dash_bootstrap_components as dbc  # noqa: E402
from dash import Dash, Input, Output, State, dcc, html, no_update, page_container, page_registry  # noqa: E402
from dash.exceptions import PreventUpdate  # noqa: E402

from grid.collector import config, db  # noqa: E402
from grid.dashboard import colours, queries  # noqa: E402

HERE = Path(__file__).resolve().parent

app = Dash(
    __name__,
    use_pages=True,
    pages_folder=str(HERE / "pages"),
    assets_folder=str(HERE / "assets"),
    external_stylesheets=[dbc.themes.FLATLY],
    title="GB grid",
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server  # gunicorn entry point

REGION_OPTIONS = [
    {"label": f"{code} · {name}", "value": code} for code, name in config.REGION_NAMES.items()
]


def _navbar():
    links = [
        dbc.NavLink(p["name"], href=p["path"], active="exact")
        for p in sorted(page_registry.values(), key=lambda p: p["order"])
    ]
    return dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarBrand("GB grid", href="/"),
                dbc.Nav(links, navbar=True, className="me-auto flex-wrap"),
                html.Div(
                    [
                        html.Span(id="freshness", className="me-3 small"),
                        dcc.Dropdown(
                            id="region",
                            options=REGION_OPTIONS,
                            value=config.DEFAULT_REGION,
                            clearable=False,
                            persistence=True,
                            persistence_type="local",
                            className="region-select",
                        ),
                    ],
                    className="d-flex align-items-center flex-wrap gap-2",
                ),
            ],
            fluid=True,
            className="flex-wrap",
        ),
        color="light",
        className="border-bottom mb-3",
    )


def serve_layout():
    if not queries.database_available():
        body = dbc.Alert(
            f"No database found at {db.DB_PATH}. Run the collector or seed_demo.py.", color="warning"
        )
    else:
        body = page_container
    return html.Div(
        [
            dcc.Location(id="url"),
            dcc.Store(id="latest"),
            dcc.Interval(id="tick", interval=60_000),
            _navbar(),
            dbc.Container(body, fluid=True),
            dbc.Container(html.Div(colours.ATTRIBUTION, className="footer"), fluid=True),
        ]
    )


app.layout = serve_layout


@app.callback(Output("latest", "data"), Input("tick", "n_intervals"), State("latest", "data"))
def poll_marker(_n, current):
    """Cheap check every minute; panels refresh only when the marker changes."""
    if not queries.database_available():
        raise PreventUpdate
    marker = queries.data_marker()
    return no_update if marker == current else marker


@app.callback(Output("freshness", "children"), Input("tick", "n_intervals"), Input("latest", "data"))
def freshness_badge(_n, _marker):
    if not queries.database_available():
        return ""
    f = queries.freshness()
    age = queries.minutes_since(f["generation"])
    if age is None:
        return dbc.Badge("no data", color="secondary")
    if age < 90:
        return dbc.Badge(f"updated {age:.0f} min ago", color="success")
    if age < 24 * 60:
        return dbc.Badge(f"stale: {age / 60:.0f} h old", color="warning")
    return dbc.Badge(f"stale: {age / 1440:.0f} d old", color="danger")


if __name__ == "__main__":
    # Development server for local testing only (never on the Pi).
    app.run(debug=False, host="127.0.0.1", port=8050)
