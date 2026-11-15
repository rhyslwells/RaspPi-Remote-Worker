"""Regional: metered output per GSP group (Southern and Northern Scotland)."""

from datetime import date, timedelta

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate

from grid.collector import config
from grid.dashboard import colours, components, queries

dash.register_page(__name__, path="/regional", name="Regional", order=3)

DEFAULT_DAYS = 7  # the range shown first: the newest week of data

INFO = (
    "Half-hourly metered output for the selected region, from Elexon's actual output per "
    "BM unit (B1610), summed by fuel. The letters of the regions match the GSP groups it is settled in.\n\n"
    "**What is in it:** distribution-connected generation and batteries, the large transmission-connected "
    "plants (for example Torness and Whitelee in Southern Scotland, Peterhead and Foyers in Northern Scotland), "
    "and the suppliers' aggregated meter volumes. Suppliers' volumes are shown below zero as "
    "*Supplier (net demand)*: electricity taken from the grid.\n\n"
    "**Plant assignment:** Elexon gives transmission-connected plants no GSP group, so each one is assigned to "
    "Southern or Northern Scotland by where it connects (list in `config.py`). Rooftop solar is outside the data.\n\n"
    "**Delay and window:** Elexon publishes this about a week after the day, and the last 30 days are kept. "
    "Batteries and pumped storage show negative while charging."
)

layout = html.Div(
    [
        html.Div(
            [
                components.region_select("Region", "rg-region", regions=list(config.GSP_GROUPS), className=""),
                html.Div(
                    [
                        html.Label("Dates", className="small text-muted me-2 mb-0"),
                        html.Div(
                            dcc.DatePickerRange(
                                id="rg-range",
                                display_format="DD MMM YYYY",
                                minimum_nights=0,  # a single day is allowed
                                start_date_placeholder_text="From",
                                end_date_placeholder_text="To",
                            ),
                            className="control-box",
                        ),
                    ],
                    className="d-flex align-items-center",
                ),
            ],
            className="mb-2 d-flex flex-wrap align-items-center gap-2",
        ),
        components.info(INFO),
        html.Div(id="rg-message"),
        dbc.Row(id="rg-tiles"),
        dcc.Graph(id="rg-chart", config={"displayModeBar": False}),
    ]
)


def _blank(fig):
    """Empty chart with no axes, for the 'nothing to show' messages."""
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return components.style(fig, 60)


@dash.callback(
    Output("rg-range", "min_date_allowed"),
    Output("rg-range", "max_date_allowed"),
    Output("rg-range", "start_date"),
    Output("rg-range", "end_date"),
    Input("rg-region", "value"),
    Input("latest", "data"),
    State("rg-range", "start_date"),
    State("rg-range", "end_date"),
)
def range_bounds(region, _marker, start, end):
    """Limit the picker to the days stored. Keeps the chosen range if it still fits, else the newest week."""
    lo, hi = queries.gsp_dates(region)
    if not hi:
        return None, None, None, None
    # Elexon publishes about a week late, so the newest stored day is the end of the default range.
    if start and end and lo <= start[:10] <= end[:10] <= hi:
        return lo, hi, start, end
    default_start = max(date.fromisoformat(lo), date.fromisoformat(hi) - timedelta(days=DEFAULT_DAYS - 1))
    return lo, hi, default_start.isoformat(), hi


@dash.callback(
    Output("rg-chart", "figure"),
    Output("rg-tiles", "children"),
    Output("rg-message", "children"),
    Input("rg-region", "value"),
    Input("rg-range", "start_date"),
    Input("rg-range", "end_date"),
    Input("latest", "data"),
)
def chart(region, start_date, end_date, _marker):
    fig = go.Figure()
    lo, hi = queries.gsp_dates(region)
    if not hi:
        return _blank(fig), "", components.empty(
            "No regional data collected yet. Run: python scripts/grid/collect.py gsp"
        )
    if not start_date or not end_date:
        raise PreventUpdate  # the user is part-way through picking a range
    # The picker is limited to the stored days when the region changes; clamp anyway.
    start = min(max(date.fromisoformat(start_date[:10]), date.fromisoformat(lo)), date.fromisoformat(hi))
    end = min(max(date.fromisoformat(end_date[:10]), start), date.fromisoformat(hi))
    data = queries.gsp_range(region, start.isoformat(), end.isoformat())
    net = {}
    rows = []
    for name in colours.REGIONAL_ORDER:
        points = data.get(name)
        if not points:
            continue
        fig.add_trace(
            go.Bar(
                x=[t for t, _ in points], y=[mw for _, mw in points], name=name,
                marker_color=colours.COLOURS[name], marker_line_width=0, hovertemplate="%{y:.0f} MW",
            )
        )
        for t, mw in points:
            net[t] = net.get(t, 0.0) + mw
        rows.append((name, sum(mw for _, mw in points) / len(points)))
    if net:
        times = sorted(net)
        fig.add_trace(
            go.Scatter(
                x=times, y=[net[t] for t in times], name="Net", mode="lines",
                line=dict(color="#78909c", width=2, dash="dot"), hovertemplate="%{y:.0f} MW",
            )
        )
    fig.update_layout(barmode="relative", bargap=0)
    components.style(fig, 460, "MW")

    tiles = [
        components.tile(name.replace(" (net demand)", " demand"), f"{avg:,.0f} MW", "average", colours.COLOURS[name])
        for name, avg in rows
    ]
    if rows:
        tiles.append(components.tile("Net", f"{sum(avg for _, avg in rows):,.0f} MW", "average"))
    return fig, tiles, ""
