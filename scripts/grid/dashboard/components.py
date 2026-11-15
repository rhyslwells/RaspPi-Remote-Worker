"""Small shared UI pieces: stat tiles, empty-state message, chart defaults."""

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import dcc, html

from grid.collector import config

NOTE_METERED = (
    "Metered generation: transmission-connected plants and interconnectors "
    "(rooftop solar and embedded wind sit outside it)."
)


REGION_OPTIONS = [
    # "search" is the text the dropdown matches typed input against.
    {"label": name, "value": code, "search": f"{name} {code}"}
    for code, name in config.REGION_NAMES.items()
]


def region_select(
    label: str = "Region", component_id: str = "region", regions=None, className: str = "mb-2"
) -> html.Div:
    """
    In-page region dropdown. The Agile pages share the id "region" (only one page is shown at a
    time, and browser persistence under that id shares the choice between them). `regions` limits
    the choices to some region letters.
    """
    options = [o for o in REGION_OPTIONS if regions is None or o["value"] in regions]
    default = config.DEFAULT_REGION if config.DEFAULT_REGION in {o["value"] for o in options} else options[0]["value"]
    return html.Div(
        [
            html.Label(label, className="small text-muted me-2 mb-0"),
            dcc.Dropdown(
                id=component_id,
                options=options,
                value=default,
                clearable=False,
                searchable=True,
                placeholder="Search regions",
                persistence=True,
                persistence_type="local",
                className="region-select",
            ),
        ],
        className=f"d-flex align-items-center {className}".strip(),
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
        lg=True,  # equal-width columns: a full row of tiles stays on one line
        className="mb-3",
    )


def empty(message: str) -> html.Div:
    return html.Div(message, className="text-muted p-4 text-center")


def info(markdown: str, summary: str = "About this chart") -> html.Details:
    """Collapsed help box (closed by default) with a markdown explanation."""
    return html.Details(
        [html.Summary(summary), dcc.Markdown(markdown, className="info-body")],
        className="info-box mb-2",
    )


def date_axis(fig: go.Figure, every_hours: int = 4) -> go.Figure:
    """Time axis whose ticks show the time and the date, e.g. 14:00 / Sat 15 Nov."""
    fig.update_xaxes(tickformat="%H:%M<br>%a %d %b", dtick=every_hours * 3_600_000)
    return fig


def style(fig: go.Figure, height: int = 380, ytitle: str = "") -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",  # let the page (light or dark) show through;
        plot_bgcolor="rgba(0,0,0,0)",  # text/grid colours follow the theme via style.css
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
