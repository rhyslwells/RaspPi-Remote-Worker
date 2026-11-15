"""Small shared UI pieces: stat tiles, empty-state message, chart defaults."""

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import html

NOTE_METERED = (
    "Metered generation only: transmission-connected plants and interconnectors. "
    "Solar and embedded wind are not included, so this is less than total demand."
)


def tile(label: str, value: str, sub: str = "", colour: str = "") -> dbc.Col:
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.Div(label, className="tile-label"),
                    html.Div(value, className="tile-value", style={"color": colour} if colour else {}),
                    html.Div(sub, className="tile-sub"),
                ]
            ),
            className="h-100",
        ),
        xs=6,
        md=4,
        lg=2,
        className="mb-3",
    )


def empty(message: str) -> html.Div:
    return html.Div(message, className="text-muted p-4 text-center")


def style(fig: go.Figure, height: int = 380, ytitle: str = "") -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=48, r=12, t=28, b=36),
        legend=dict(orientation="h", y=-0.2),
        yaxis_title=ytitle,
        hovermode="x unified",
        font=dict(size=12),
    )
    return fig


def fmt(value, digits: int = 1, suffix: str = "") -> str:
    return "n/a" if value is None else f"{value:,.{digits}f}{suffix}"
