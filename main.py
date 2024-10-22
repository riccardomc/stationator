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
def trains(where: str):
    trips = ns.get_trips(where)
    rows = [vars(t) for t in trips]
    for r in rows:
        for k, v in r.items():
            if isinstance(v, datetime):
                r[k] = v.strftime("%H:%M")

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
    ui.link("Back", "/trains")


ui.run(host="0.0.0.0", favicon="☠️", title="Stationator", show=False)
