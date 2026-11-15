"""Prices: Agile against system price, typical day, negative-price counts."""

from datetime import timedelta

import dash
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from grid.collector import config
from grid.dashboard import colours, components, queries

dash.register_page(__name__, path="/prices", name="Prices", order=2)

layout = html.Div(
    [
        html.H5("Agile and system price, last 3 days"),
        components.info(
            "Two prices on the same axis, both in p/kWh:\n\n"
            "- **Agile** (green): what a customer on Octopus Agile pays per unit in the region chosen at the "
            "top right, including VAT. Set a day ahead.\n"
            "- **System price** (blue): the Elexon imbalance price, the cost of balancing the grid "
            "in each half hour. GB-wide, set after the fact, before supplier costs, taxes and VAT.\n\n"
            "They tend to move together because both reflect scarcity and surplus. "
            "The system price is far spikier. See the Glossary."
        ),
        dcc.Graph(id="pr-lines", config={"displayModeBar": False}),
        html.H5("Typical Agile price through the day (last 28 days)", className="mt-3"),
        components.info(
            "The average Agile price for each half hour of the day over the last 28 days, "
            "for weekdays (Mon to Fri) and weekends (Sat and Sun). "
            "The low points are the usual cheap times to run things; the peak is typically 16:00 to 19:00."
        ),
        dcc.Graph(id="pr-heat", config={"displayModeBar": False}),
        html.H5("Negative prices per day", className="mt-3"),
        components.info(
            "How many half-hour slots each day had a price below zero, for Agile in your region (green) "
            "and for the GB system price (blue). Negative prices mean generation outstrips demand "
            "(usually windy and sunny) and users are paid to take power. "
            "A day has 48 half-hours."
        ),
        dcc.Graph(id="pr-neg", config={"displayModeBar": False}),
        html.Div(
            "System price is the Elexon imbalance price converted from £/MWh to p/kWh, "
            "shown for comparison with Agile.",
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
    components.date_axis(fig, 6)
    return components.style(fig, 380, "p/kWh")


@dash.callback(Output("pr-heat", "figure"), Input("region", "value"), Input("latest", "data"))
def typical_day(region, _marker):
    cells = queries.agile_heatmap(region)  # {(weekday 0=Mon, half-hour 0..47): average p/kWh}
    labels = [f"{h // 2:02d}:{'30' if h % 2 else '00'}" for h in range(48)]
    fig = go.Figure()
    for name, days, colour in (("Weekdays", range(5), colours.AGILE), ("Weekends", range(5, 7), "#f57c00")):
        y = []
        for h in range(48):
            vals = [cells[(d, h)] for d in days if (d, h) in cells]
            y.append(sum(vals) / len(vals) if vals else None)
        fig.add_trace(go.Scatter(x=labels, y=y, name=name, line=dict(color=colour, shape="hv"),
                                 hovertemplate="%{y:.1f} p/kWh"))
    fig.update_xaxes(nticks=12)
    return components.style(fig, 320, "p/kWh")


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
