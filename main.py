#!/usr/bin/env python3
from datetime import datetime, timezone
from nicegui import ui, run
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
    ui.link("Trains to Work (Den Haag - Amsterdam)", "/trains/work/0")
    ui.link("Trains to Home (Amsterdam - Den Haag)", "/trains/home/0")


@ui.page("/trains/{where}")
async def trains_where(where: str):
    await trains_where_delta(where, 0)


@ui.page("/trains/{where}/{delta}")
async def trains_where_delta(where: str, delta: int):

    # already display page once client websocket is connected
    await ui.context.client.connected()
    with ui.row():
        label = ui.label(f"Fetching trips to {where}...")
        spinner = ui.spinner()

    # set time
    if delta is None or delta == "" or type(delta) is not int:
        delta = 0
    date_time = ns.get_amsterdam_time(delta)
    print(f"going to fetch {date_time}")

    # get trips async
    trips = await run.io_bound(ns.get_trips, where, date_time)
    spinner.visible = False

    # serialize trips, format datetimes
    rows = [
        {
            k: v.strftime("%H:%M") if isinstance(v, datetime) else str(v)
            for k, v in vars(t).items()
        }
        for t in trips
    ]

    # build and display table
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
    now_utc = datetime.now(timezone.utc)
    now = now_utc.astimezone().strftime("%H:%M")
    label.bind_text_from(
        table,
        "rows",
        lambda rows: f"Found {len(rows)} trips at {now}",
    )

    # add back link
    with ui.row():
        ui.link("Index", "/trains")
        ui.link("Less", f"/trains/{where}/{delta - 1}")
        ui.link("Plus", f"/trains/{where}/{delta + 1}")


ui.run(host="0.0.0.0", favicon="☠️", title="Stationator", show=False)
