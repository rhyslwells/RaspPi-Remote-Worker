"""History: daily metrics over time and wind against price."""

from datetime import date

import dash
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from grid.dashboard import colours, components, queries

dash.register_page(__name__, path="/history", name="History", order=4)

STEPS = (14, 30, 90, 365)  # offered only when the stored history is longer than the step
ALL = "all"


def _days(value) -> int:
    return 3650 if value == ALL else int(value)


def _range_options():
    """Ranges that the stored daily history can actually fill, plus "All"."""
    rows = queries.daily_summaries(3650)
    span = (queries.uk_today() - date.fromisoformat(rows[0]["date"])).days if rows else 0
    options = [{"label": f"{d} days" if d < 365 else "1 year", "value": str(d)} for d in STEPS if d < span]
    options.append({"label": f"All ({span} days)" if span else "All", "value": ALL})
    return options


def layout():
    options = _range_options()
    values = [o["value"] for o in options]
    return _layout(options, "30" if "30" in values else ALL)


def _layout(options, default):
    return html.Div(
        [
            dcc.RadioItems(
                id="hi-days",
                options=options,
                value=default,
                inline=True,
                inputClassName="ms-3 me-1",
                className="mb-2",
            ),
            html.H5("Daily metered generation by source"),
            components.info(
                "GB-wide generation per day (GWh) from transmission-connected plants and interconnectors, "
                "by fuel. See the Glossary for what *metered* covers."
            ),
            dcc.Graph(id="hi-gen", config={"displayModeBar": False}),
            html.H5("Daily average price", className="mt-3"),
            components.region_select("Agile region"),
            components.info(
                "Daily average Agile price for your region (solid green), the average of the cheapest 2 hours "
                "of each day (dotted green) and the daily average GB system price (blue). "
                "The gap between the two green lines shows how much shifting use to the cheapest window can save."
            ),
            dcc.Graph(id="hi-price", config={"displayModeBar": False}),
            html.H5("Wind share against system price", className="mt-3"),
            components.info(
                "Each dot is one day: how much of that day's metered generation came from wind (x) "
                "against the daily average system price (y). The idea is that windy days mean "
                "cheaper power, so look for a downward slope.\n\n"
                "Wind is only one driver. Others include demand, gas prices, interconnector flows, "
                "plant outages and how short or long the system is overall (net imbalance volume). "
                "Daily averages also hide a lot: a windy night and a calm evening cancel out."
            ),
            dcc.Graph(id="hi-scatter", config={"displayModeBar": False}),
            html.Div(components.NOTE_METERED, className="small text-muted"),
        ]
    )


@dash.callback(Output("hi-gen", "figure"), Input("hi-days", "value"), Input("latest", "data"))
def gen(days, _marker):
    rows = queries.daily_summaries(_days(days))
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
    sy = queries.daily_summaries(_days(days))
    ag = queries.agile_dailies(region, _days(days))
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
    rows = [r for r in queries.daily_summaries(_days(days))
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
