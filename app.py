#!/usr/bin/env python3
from datetime import datetime
from nicegui import ui
import ns


def strf(d):
    return d.strftime("%H:%F")


columns = [
    {
        "name": "departure_time",
        "label": "departure_time",
        "field": "departure_time",
    },
    {
        "name": "arrival_time",
        "label": "arrival_time",
        "field": "arrival_time",
    },
    {
        "name": "origin",
        "label": "origin",
        "field": "origin",
    },
    {
        "name": "destination",
        "label": "destination",
        "field": "destination",
    },
    {
        "name": "status",
        "label": "status",
        "field": "status",
    },
    {
        "name": "leave_by",
        "label": "leave_by",
        "field": "leave_by",
    },
    {
        "name": "arrive_by",
        "label": "arrive_by",
        "field": "arrive_by",
    },
]


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


ui.run(host="0.0.0.0", favicon="☠️", title="Stationator")
