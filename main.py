#!/usr/bin/env python3
from datetime import datetime
from nicegui import ui
import ns


columns_order = [
    "departure_time",
    "arrival_time",
    "origin",
    "destination",
    "status",
    "leave_by",
    "arrive_by",
]

columns = [{"name": c, "label": c, "field": c} for c in columns_order]


@ui.page("/")
def root():
    ui.navigate.to("/trains")


@ui.page("/trains")
def trains_index():
    ui.link("Trains to Work (Den Haag - Amsterdam)", "/trains/work")
    ui.link("Trains to Home (Amsterdam - Den Haag)", "/trains/home")


@ui.page("/trains/{where}")
async def trains(where: str):
    label = ui.label(f"fetching trips to {where}...")
    # get trips
    trips = await ns.get_trips(where)

    # serialize trips, format datetimes
    rows = [
        {
            k: v.strftime("%H:%M") if isinstance(v, datetime) else str(v)
            for k, v in vars(t).items()
        }
        for t in trips
    ]

    # build table
    table = ui.table(
        columns=columns,
        rows=rows,
        column_defaults={
            "align": "left",
            "headerClasses": "uppercase text-primary",
            "sortable": True,
        },
        row_key="name",
    )

    # add table header
    table.add_slot(
        "header",
        r"""
    <q-tr :props="props">
        <q-th v-for="col in props.cols" :key="col.name" :props="props">
            {{ col.label }}
        </q-th>
    </q-tr>
    """,
    )

    # update label
    now = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
    label.bind_text_from(
        table,
        "rows",
        lambda rows: f"Found {len(rows)} trips at {now}",
    )

    # add back link
    ui.link("Back", "/trains")


ui.run(host="0.0.0.0", favicon="☠️", title="Stationator", show=False)
