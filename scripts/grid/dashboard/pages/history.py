"""History: daily metrics over time and wind against price."""

import dash
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from grid.dashboard import colours, components, queries

dash.register_page(__name__, path="/history", name="History", order=3)

RANGES = {"14": "14 days", "30": "30 days", "90": "90 days", "365": "1 year"}

layout = html.Div(
    [
        dcc.RadioItems(
            id="hi-days",
            options=[{"label": v, "value": k} for k, v in RANGES.items()],
            value="30",
            inline=True,
            inputClassName="ms-3 me-1",
            className="mb-2",
        ),
        html.H5("Daily metered generation by source"),
        dcc.Graph(id="hi-gen", config={"displayModeBar": False}),
        html.H5("Daily average price", className="mt-3"),
        dcc.Graph(id="hi-price", config={"displayModeBar": False}),
        html.H5("Wind share against system price", className="mt-3"),
        dcc.Graph(id="hi-scatter", config={"displayModeBar": False}),
        html.Div(components.NOTE_METERED, className="small text-muted"),
    ]
)


@dash.callback(Output("hi-gen", "figure"), Input("hi-days", "value"), Input("latest", "data"))
def gen(days, _marker):
    rows = queries.daily_summaries(int(days))
    fig = go.Figure()
    for label, key in (("Nuclear", "gen_nuclear_mwh"), ("Biomass", "gen_biomass_mwh"),
                       ("Wind", "gen_wind_mwh"), ("Gas", "gen_gas_mwh")):
        fig.add_trace(go.Bar(x=[r["date"] for r in rows], y=[(r[key] or 0) / 1000 for r in rows],
                             name=label, marker_color=colours.COLOURS[label]))
    fig.add_trace(go.Bar(x=[r["date"] for r in rows], y=[(r["gen_imports_mwh"] or 0) / 1000 for r in rows],
                         name=colours.IMPORTS, marker_color=colours.COLOURS[colours.IMPORTS]))
    fig.update_layout(barmode="relative")
    return components.style(fig, 360, "GWh per day")


@dash.callback(Output("hi-price", "figure"), Input("hi-days", "value"),
               Input("region", "value"), Input("latest", "data"))
def price(days, region, _marker):
    sy = queries.daily_summaries(int(days))
    ag = queries.agile_dailies(region, int(days))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[r["date"] for r in ag], y=[r["avg_p_kwh"] for r in ag],
                             name=f"Agile average ({region})", line=dict(color=colours.AGILE)))
    fig.add_trace(go.Scatter(x=[r["date"] for r in ag], y=[r["cheapest2h_avg_p_kwh"] for r in ag],
                             name="Agile cheapest 2 hours", line=dict(color="#2e7d32", dash="dot")))
    fig.add_trace(go.Scatter(x=[r["date"] for r in sy],
                             y=[(r["sys_avg_gbp_mwh"] / 10) if r["sys_avg_gbp_mwh"] is not None else None for r in sy],
                             name="System price average", line=dict(color=colours.SYSTEM_PRICE)))
    return components.style(fig, 340, "p/kWh")


@dash.callback(Output("hi-scatter", "figure"), Input("hi-days", "value"), Input("latest", "data"))
def scatter(days, _marker):
    rows = [r for r in queries.daily_summaries(int(days))
            if r["gen_total_mwh"] and r["sys_avg_gbp_mwh"] is not None]
    fig = go.Figure(
        go.Scatter(
            x=[r["gen_wind_mwh"] / r["gen_total_mwh"] * 100 for r in rows],
            y=[r["sys_avg_gbp_mwh"] / 10 for r in rows],
            mode="markers", text=[r["date"] for r in rows],
            marker=dict(color=colours.COLOURS["Wind"], size=9),
            hovertemplate="%{text}<br>wind %{x:.0f}% of metered, price %{y:.1f} p/kWh<extra></extra>",
        )
    )
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(title="Wind share of metered generation (%)")
    return components.style(fig, 340, "System price p/kWh")
