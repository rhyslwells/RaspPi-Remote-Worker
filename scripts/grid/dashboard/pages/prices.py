"""Prices: Agile against system price, weekday heatmap, negative-price counts."""

from datetime import timedelta

import dash
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from grid.collector import config
from grid.dashboard import colours, components, queries

dash.register_page(__name__, path="/prices", name="Prices", order=2)

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

layout = html.Div(
    [
        html.H5("Agile and system price, last 3 days"),
        dcc.Graph(id="pr-lines", config={"displayModeBar": False}),
        html.H5("Average Agile price by weekday and time (last 28 days)", className="mt-3"),
        dcc.Graph(id="pr-heat", config={"displayModeBar": False}),
        html.H5("Negative prices per day", className="mt-3"),
        dcc.Graph(id="pr-neg", config={"displayModeBar": False}),
        html.Div(
            "System price is the Elexon imbalance price converted from £/MWh to p/kWh. "
            "It is not a price you pay; it is shown for comparison with Agile.",
            className="small text-muted",
        ),
    ]
)


@dash.callback(Output("pr-lines", "figure"), Input("region", "value"), Input("latest", "data"))
def lines(region, _marker):
    end = queries.uk_today() + timedelta(days=1)
    start = end - timedelta(days=4)
    agile = queries.agile_range(region, start.isoformat(), end.isoformat())
    system = queries.system_price_range(start.isoformat(), end.isoformat())
    fig = go.Figure()
    if agile:
        fig.add_trace(
            go.Scatter(
                x=[t for t, _ in agile], y=[p for _, p in agile], name=f"Agile ({region})",
                line=dict(color=colours.AGILE, shape="hv"), hovertemplate="%{y:.1f} p/kWh",
            )
        )
    if system:
        fig.add_trace(
            go.Scatter(
                x=[t for t, _ in system], y=[p for _, p in system], name="System price",
                line=dict(color=colours.SYSTEM_PRICE, shape="hv"), hovertemplate="%{y:.1f} p/kWh",
            )
        )
    return components.style(fig, 380, "p/kWh")


@dash.callback(Output("pr-heat", "figure"), Input("region", "value"), Input("latest", "data"))
def heat(region, _marker):
    cells = queries.agile_heatmap(region)
    z = [[cells.get((d, h)) for h in range(48)] for d in range(7)]
    labels = [f"{h // 2:02d}:{'30' if h % 2 else '00'}" for h in range(48)]
    fig = go.Figure(
        go.Heatmap(
            z=z, x=labels, y=DAYS, colorscale="RdYlGn_r", colorbar=dict(title="p/kWh"),
            hovertemplate="%{y} %{x}: %{z:.1f} p/kWh<extra></extra>",
        )
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(nticks=12)
    return components.style(fig, 300)


@dash.callback(Output("pr-neg", "figure"), Input("region", "value"), Input("latest", "data"))
def negatives(region, _marker):
    ag = queries.agile_dailies(region, 60)
    sy = queries.daily_summaries(60)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[r["date"] for r in ag], y=[r["neg_slots"] for r in ag],
                         name=f"Agile slots below 0 ({region})", marker_color=colours.AGILE))
    fig.add_trace(go.Bar(x=[r["date"] for r in sy], y=[r["sys_neg_periods"] for r in sy],
                         name="System price periods below 0", marker_color=colours.SYSTEM_PRICE))
    fig.update_layout(barmode="group")
    return components.style(fig, 300, "half-hours")
