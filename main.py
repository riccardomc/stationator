#!/usr/bin/env python3
from datetime import datetime, timedelta
from nicegui import ui, run
import ns


columns_order = [
    "departure_time",
    "direction",
    "arrival_time",
    "origin",
    "departure_track",
    "destination",
    "status",
    "travel_time",
    "leave_by",
    "arrive_by",
    "train_time",
    "biking_time",
]

labels = [
    "🕗",
    "🏁",
    "🕓",
    "🛫",
    "🚉",
    "🛬",
    "☠️",
    "⏱️",
    "🚀",
    "😰",
    "💺",
    "🚴",
]

columns = [{"name": c, "label": l, "field": c}
           for c, l in zip(columns_order, labels)]


@ui.page("/")
def root():
    ui.navigate.to("/trains")


@ui.page("/trains")
def trains_index():
    ui.link("🏠", "trains/home")
    ui.link("💼", "trains/work")


@ui.page("/trains/{where}")
async def trains_where(where: str):
    hour = int(ns.get_amsterdam_time().hour)
    ui.navigate.to(f"/trains/{where}/{hour}")


@ui.page("/trains/{where}/{hour}")
async def trains_where_hour(where: str, hour: int):
    # already display page once client websocket is connected
    await ui.context.client.connected()
    with ui.row():
        label = ui.label(f"Fetching trips to {where}...")
        spinner = ui.spinner()

    # set time
    date_time = ns.get_amsterdam_time(hour)
    print(f"going to fetch {date_time}")

    # get trips async
    trips = await run.io_bound(ns.get_trips, where, date_time)
    spinner.visible = False

    # serialize trips, format datetimes
    rows = [
        {
            k: v.strftime("%H:%M") if isinstance(v, datetime) else (datetime.min + v).strftime("%H:%M") if isinstance(v, timedelta) else str(v)
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
    now = date_time.strftime("%H:%M")
    label.bind_text_from(
        table,
        "rows",
        lambda rows: f"Found {len(rows)} trips at {now}",
    )

    # add back link
    with ui.row():
        ui.link("🫵", "/trains")
        ui.link("➖", f"/trains/{where}/{hour - 1}")
        ui.link("➕", f"/trains/{where}/{hour + 1}")


def get_trips():
    hour = int(ns.get_amsterdam_time().hour)
    date_time = ns.get_amsterdam_time(hour)
    ns.fetch_trips.cache_clear()

    #cache trips home now, and +1 -1 hour
    ns.get_trips(where_to="home", date_time=date_time)
    ns.get_trips(where_to="home", date_time=date_time + timedelta(hours=1))

    #cache trips work now, and +1 -1 hour
    ns.get_trips(where_to="work", date_time=date_time)
    ns.get_trips(where_to="work", date_time=date_time + timedelta(hours=1))


ui.timer(300, get_trips)
ui.run(host="0.0.0.0", favicon="🚂", title="Stationator", show=False)
