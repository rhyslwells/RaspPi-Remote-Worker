"""Glossary: plain-English meaning of every term used on the dashboard."""

import dash
from dash import dcc, html

dash.register_page(__name__, path="/glossary", name="Glossary", order=6)

TEXT = """
## Prices

**Agile (Octopus Agile)**
A half-hourly variable electricity tariff from Octopus Energy. Prices for the next day are published
in the afternoon and track the wholesale market, with a cap and a surcharge in the evening peak.
Shown in **p/kWh including VAT**. Agile prices are set per distribution region (the letter A to P).

**Region (A to P)**
One of the 14 electricity distribution regions in Great Britain. It only affects **Agile prices**
(the region selector on the Overview, Prices, Regional and History pages). Generation, demand and system price are the same for all of GB.

**System price (imbalance price)**
The price at which Elexon settles imbalances: the cost of balancing supply and demand
in each half hour, calculated after the event. Since 2015 there is a single price in GB (the
sell and buy prices are equal). Published in £/MWh; the dashboard divides by 10 to show **p/kWh**
(£1/MWh = 0.1 p/kWh). It is a wholesale-level signal for balancing the grid.
Very spiky: it can be hundreds of £/MWh when the system is short, or negative when it is long.

**Negative price**
A half hour where the price is below zero: oversupply, so users are paid to consume.
Typical on windy, sunny, low-demand days.

**Cheapest 2 hours**
The cheapest run of four consecutive half-hour Agile slots among the published, upcoming prices.

## Generation and demand

**Metered generation**
Output from large, transmission-connected power stations and interconnectors, as reported
to Elexon (the FUELHH dataset). Rooftop solar and plants on local networks sit outside it.
Total generation is higher.

**GB-wide**
These figures cover Great Britain as a whole.

**GSP group**
A Grid Supply Point group: one of the 14 areas that electricity settlement is split into. The letters
match the Agile regions (N is Southern Scotland, P is Northern Scotland).

**Supplier (net demand)**
The metered volumes of suppliers' aggregated meter units in a GSP group. They are negative because
they are electricity taken from the grid, so they track the area's demand (net of generation behind those meters).

**Fuel groups**
Wind, Gas (CCGT and OCGT), Nuclear, Biomass, Hydro (natural flow), Pumped storage, Other
(coal, oil, other), and Interconnectors.

**Interconnector (net)**
Cables to other countries (France, Netherlands, Belgium, Norway, Ireland and others).
Above zero is importing power into GB, below zero is exporting.

**Pumped storage**
Reservoirs used as a battery. Positive when generating, negative when pumping water uphill.

**Demand (INDO)**
Initial National Demand Outturn: the first published estimate of GB demand, in GW.
It includes the effect of embedded generation, so it is usually higher than metered generation.

**Settlement period**
Half-hour slot of the trading day (48 per day, 46 or 50 when the clocks change).
All times on the dashboard are UK local time.

## Other terms

**Net imbalance volume (NIV)**
How much the system operator had to buy or sell to balance the grid in a half hour.
A large positive or negative NIV tends to push the system price up or down.

**Elexon / BMRS**
Elexon runs GB electricity settlement. BMRS is its public data service, where generation,
demand and system prices come from.
"""

layout = html.Div([dcc.Markdown(TEXT, className="glossary")])
