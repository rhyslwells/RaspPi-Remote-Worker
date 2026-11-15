"""Overview: headline tiles for the latest day, upcoming Agile prices, freshness."""

from datetime import datetime, timezone

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from grid.collector import config
from grid.dashboard import colours, components, queries

dash.register_page(__name__, path="/", name="Overview", order=0)

layout = html.Div(
    [
        components.region_select("Agile region"),
        dbc.Row(id="ov-tiles"),
        html.H5(id="ov-agile-title", className="mt-2"),
        components.info(
            "Half-hourly **Octopus Agile** unit prices for the region selected above, "
            "including VAT, for every slot Octopus has published (usually until tomorrow night)."
            "\n\n"
            "- **Green bars**: the cheapest 2 hours in a row (4 slots).\n"
            "- **Red bars**: negative prices, where you are paid to use electricity.\n"
            "- See the Glossary page for what Agile is and how it is set."
        ),
        dcc.Graph(id="ov-agile", config={"displayModeBar": False}),
        html.Div(id="ov-fresh", className="small text-muted mb-4"),
    ]
)


@dash.callback(Output("ov-tiles", "children"), Input("region", "value"), Input("latest", "data"))
def tiles(region, _marker):
    s, prev = queries.last_complete_summary()
    slots = queries.agile_upcoming(region)
    now = datetime.now(timezone.utc).strftime(queries.FMT)
    current = next((x for x in slots if x["valid_from_utc"] <= now < x["valid_to_utc"]), None)
    window = queries.cheapest_window(slots)
    out = []
    if s:
        total = s["gen_total_mwh"] or 0
        share = lambda k: (s[k] / total * 100) if total and s.get(k) is not None else None  # noqa: E731
        out += [
            components.tile("Metered generation", components.fmt(total / 1000, 0, " GWh"), f"GB-wide, {s['date']}"),
            components.tile("Wind", components.fmt(share("gen_wind_mwh"), 0, "%"), "of metered", colours.COLOURS["Wind"]),
            components.tile("Gas", components.fmt(share("gen_gas_mwh"), 0, "%"), "of metered", colours.COLOURS["Gas"]),
            components.tile("Peak demand", components.fmt((s["demand_peak_mw"] or 0) / 1000, 1, " GW"), s["date"]),
            components.tile(
                "System price (avg)",
                components.fmt((s["sys_avg_gbp_mwh"] or 0) / 10, 1, " p/kWh") if s["sys_avg_gbp_mwh"] is not None else "n/a",
                f"{s['sys_neg_periods'] or 0} negative periods",
                colours.SYSTEM_PRICE,
            ),
        ]
    else:
        out.append(dbc.Col(components.empty("No complete day summarised yet."), width=12))
    out.append(
        components.tile(
            f"Agile now ({region})",
            components.fmt(current["inc_vat_p_kwh"] if current else None, 1, " p/kWh"),
            config.REGION_NAMES.get(region, ""),
            colours.AGILE,
        )
    )
    if window:
        out.append(
            components.tile(
                "Cheapest 2 hours",
                f"{queries.to_local(window[0]):%a %H:%M}–{queries.to_local(window[1]):%H:%M}",
                f"avg {window[2]:.1f} p/kWh",
                colours.AGILE,
            )
        )
    return out


@dash.callback(
    Output("ov-agile", "figure"),
    Output("ov-agile-title", "children"),
    Input("region", "value"),
    Input("latest", "data"),
)
def agile_chart(region, _marker):
    slots = queries.agile_upcoming(region)
    title = f"Agile prices, {config.REGION_NAMES.get(region, region)}"
    if not slots:
        return components.style(go.Figure()), title + " (no upcoming prices)"
    window = queries.cheapest_window(slots)
    cheap = set()
    if window:
        cheap = {x["valid_from_utc"] for x in slots if window[0] <= x["valid_from_utc"] < window[1]}
    x = [queries.to_local(s["valid_from_utc"]) for s in slots]
    y = [s["inc_vat_p_kwh"] for s in slots]
    colour = [
        colours.NEGATIVE if v < 0 else ("#2e7d32" if s["valid_from_utc"] in cheap else colours.AGILE)
        for s, v in zip(slots, y)
    ]
    fig = go.Figure(go.Bar(x=x, y=y, marker_color=colour, hovertemplate="%{x|%a %H:%M}: %{y:.1f} p/kWh<extra></extra>"))
    components.date_axis(fig)
    return components.style(fig, 340, "p/kWh inc VAT"), title + " (cheapest 2 hours in green)"


@dash.callback(Output("ov-fresh", "children"), Input("latest", "data"))
def fresh_text(_marker):
    f = queries.freshness()
    parts = []
    if f["generation"]:
        parts.append(f"Generation data up to {queries.to_local(f['generation']):%a %d %b %H:%M} UK time.")
    if f["agile_to"]:
        parts.append(f"Agile prices published to {queries.to_local(f['agile_to']):%a %d %b %H:%M}.")
    return " ".join(parts)
