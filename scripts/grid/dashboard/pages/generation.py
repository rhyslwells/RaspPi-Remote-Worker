"""Generation mix (GB-wide) by fuel group for a chosen day or range."""

from datetime import date, timedelta

import dash
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from grid.dashboard import colours, components, queries

dash.register_page(__name__, path="/generation", name="Generation", order=1)

RANGES = {"1": "Day", "3": "3 days", "7": "7 days"}


def layout():
    lo, hi = queries.available_dates()
    return html.Div(
        [
            html.Div(
                [
                    dcc.DatePickerSingle(
                        id="gen-date",
                        min_date_allowed=lo,
                        max_date_allowed=hi,
                        date=hi,
                        display_format="DD MMM YYYY",
                    ),
                    dcc.RadioItems(
                        id="gen-days",
                        options=[{"label": v, "value": k} for k, v in RANGES.items()],
                        value="1",
                        inline=True,
                        inputClassName="ms-3 me-1",
                    ),
                ],
                className="mb-2",
            ),
            components.info(
                "**What this shows:** half-hourly electricity generation for the whole of Great Britain, "
                "stacked by fuel type, from Elexon (the BMRS FUELHH dataset). The grey line is national demand."
                "\n\n"
                "**GB-wide:** Elexon publishes generation as one national total, so the region selector "
                "only applies to Agile prices."
                "\n\n"
                "**Metered:** transmission-connected power stations and interconnectors. Rooftop solar and "
                "wind on local networks sit outside it, which is why the stack falls below the demand line, "
                "especially on sunny days."
                "\n\n"
                "Interconnectors show net flow: above zero is importing, below zero is exporting. "
                "Pumped storage is positive when generating and negative when pumping."
            ),
            dcc.Graph(id="gen-chart", config={"displayModeBar": False}),
            html.Div(components.NOTE_METERED, className="small text-muted"),
        ]
    )


@dash.callback(
    Output("gen-chart", "figure"),
    Input("gen-date", "date"),
    Input("gen-days", "value"),
    Input("latest", "data"),
)
def chart(day, days, _marker):
    fig = go.Figure()
    if not day:
        return components.style(fig)
    end = date.fromisoformat(day[:10])
    start = end - timedelta(days=int(days) - 1)
    groups = queries.generation_range(start.isoformat(), end.isoformat())
    for name in colours.ORDER:
        points = groups.get(name)
        if not points:
            continue
        fig.add_trace(
            go.Bar(
                x=[t for t, _ in points],
                y=[mw / 1000 for _, mw in points],
                name=name,
                marker_color=colours.COLOURS[name],
                marker_line_width=0,
                hovertemplate="%{y:.1f} GW",
            )
        )
    demand = queries.demand_range(start.isoformat(), end.isoformat())
    if demand:
        fig.add_trace(
            go.Scatter(
                x=[t for t, _ in demand],
                y=[v / 1000 for _, v in demand],
                name="GB demand (INDO)",
                mode="lines",
                line=dict(color="#78909c", width=2.5),
                hovertemplate="%{y:.1f} GW",
            )
        )
    fig.update_layout(barmode="relative", bargap=0)
    return components.style(fig, 460, "GW")
