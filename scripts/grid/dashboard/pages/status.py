"""Status: collector health, freshness, database size and free disk."""

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, html

from grid.dashboard import components, queries

dash.register_page(__name__, path="/status", name="Status", order=5)

layout = html.Div([html.Div(id="st-body")])


def _local(ts):
    return f"{queries.to_local(ts):%a %d %b %H:%M}" if ts else "never"


@dash.callback(Output("st-body", "children"), Input("latest", "data"), Input("tick", "n_intervals"))
def body(_marker, _n):
    f = queries.freshness()
    info = queries.system_info()
    counts = queries.table_counts()
    runs = queries.recent_runs(30)

    tiles = [
        components.tile("Generation data", _local(f["generation"]), "latest half-hour"),
        components.tile("System prices", _local(f["system_price"]), "latest half-hour"),
        components.tile("Agile prices to", _local(f["agile_to"]), "UK time"),
        components.tile("Database", components.fmt(info["db_mb"], 1, " MB")),
        components.tile("Disk free", components.fmt(info["disk_free_pct"], 0, "%")),
    ]
    last_ok = [
        html.Li(f"{job}: last success {_local(ts)} UK time") for job, ts in sorted(f["jobs"].items())
    ] or [html.Li("No successful runs recorded.")]
    run_rows = [
        html.Tr(
            [
                html.Td(r["job"]),
                html.Td(_local(r["started_at"])),
                html.Td(f"{r['duration_s']:.1f}s" if r["duration_s"] is not None else ""),
                html.Td("ok" if r["success"] else "FAILED", className="" if r["success"] else "text-danger fw-bold"),
                html.Td(r["rows_written"]),
                html.Td((r["error"] or "")[:120]),
            ]
        )
        for r in runs
    ]
    return [
        dbc.Row(tiles),
        html.H5("Last successful run"),
        html.Ul(last_ok),
        html.H5("Recent runs", className="mt-3"),
        dbc.Table(
            [html.Thead(html.Tr([html.Th(h) for h in ("Job", "Started", "Took", "Result", "Rows", "Error")])),
             html.Tbody(run_rows)],
            size="sm", striped=True, responsive=True,
        ),
        html.H5("Rows stored", className="mt-3"),
        html.Ul([html.Li(f"{t}: {n:,}") for t, n in counts.items()]),
    ]
