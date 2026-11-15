"""Regional: metered output per GSP group (Southern and Northern Scotland)."""

from datetime import date, timedelta

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from grid.collector import config
from grid.dashboard import colours, components, queries

dash.register_page(__name__, path="/regional", name="Regional", order=3)

RANGES = {"1": "Day", "3": "3 days", "7": "7 days"}
GROUP_OPTIONS = [{"label": name, "value": code} for code, name in config.GSP_GROUPS.items()]

INFO = (
    "Half-hourly metered output for one **GSP group** (a settlement area; the letters match the Agile regions), "
    "from Elexon's actual output per BM unit (B1610), summed by fuel.\n\n"
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
                dcc.RadioItems(
                    id="rg-group",
                    options=GROUP_OPTIONS,
                    value=config.DEFAULT_REGION if config.DEFAULT_REGION in config.GSP_GROUPS else next(iter(config.GSP_GROUPS)),
                    inline=True,
                    inputClassName="me-1",
                    labelClassName="me-3",
                ),
                dcc.RadioItems(
                    id="rg-days",
                    options=[{"label": v, "value": k} for k, v in RANGES.items()],
                    value="1",
                    inline=True,
                    inputClassName="ms-3 me-1",
                ),
            ],
            className="mb-2 d-flex flex-wrap align-items-center gap-2",
        ),
        html.Div(id="rg-date-box"),
        components.info(INFO),
        dcc.Graph(id="rg-chart", config={"displayModeBar": False}),
        html.H5("Average over the selected period", className="mt-3"),
        html.Div(id="rg-table"),
    ]
)


def _bounds(group):
    lo, hi = queries.gsp_dates(group)
    return lo, hi


@dash.callback(Output("rg-date-box", "children"), Input("rg-group", "value"), Input("latest", "data"))
def date_picker(group, _marker):
    lo, hi = _bounds(group)
    if not hi:
        return components.empty("No regional data collected yet. Run: python scripts/grid/collect.py gsp")
    return dcc.DatePickerSingle(
        id="rg-date", min_date_allowed=lo, max_date_allowed=hi, date=hi, display_format="DD MMM YYYY"
    )


@dash.callback(
    Output("rg-chart", "figure"),
    Output("rg-table", "children"),
    Input("rg-group", "value"),
    Input("rg-days", "value"),
    Input("rg-date", "date"),
    Input("latest", "data"),
)
def chart(group, days, day, _marker):
    fig = go.Figure()
    lo, hi = _bounds(group)
    if not day or not hi:
        return components.style(fig), ""
    # The picker is rebuilt when the group changes; keep the date inside that group's data.
    end = min(max(date.fromisoformat(day[:10]), date.fromisoformat(lo)), date.fromisoformat(hi))
    start = end - timedelta(days=int(days) - 1)
    data = queries.gsp_range(group, start.isoformat(), end.isoformat())
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

    table = ""
    if rows:
        table = dbc.Table(
            [
                html.Thead(html.Tr([html.Th("Category"), html.Th("Average MW", className="text-end")])),
                html.Tbody([html.Tr([html.Td(n), html.Td(f"{v:,.0f}", className="text-end")]) for n, v in rows]),
            ],
            size="sm", striped=True, className="w-auto",
        )
    return fig, table
