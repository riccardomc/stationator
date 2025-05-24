#!/usr/bin/env python3
from datetime import datetime, timedelta
from nicegui import ui, run
import ns
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


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


@ui.page("/v1/trains")
def v1_trains_index():
    logger.info("Rendering v1 trains index page")
    ui.link("🏠", "trains/home")
    ui.link("💼", "trains/work")
    ui.link("⬅️ back", "/trains")


@ui.page("/v1/trains/{where}")
async def v1_trains_where(where: str):
    logger.info(f"Navigating to v1 trains for destination: {where}")
    hour = int(ns.get_amsterdam_time().hour)
    ui.navigate.to(f"/v1/trains/{where}/{hour}")


@ui.page("/v1/trains/{where}/{hour}")
async def v1_trains_where_hour(where: str, hour: int):
    logger.info(f"Rendering v1 trains page for {where} at hour {hour}")
    # already display page once client websocket is connected
    await ui.context.client.connected()
    with ui.row():
        label = ui.label(f"Fetching trips to {where}...")
        spinner = ui.spinner()

    # set time
    date_time = ns.get_amsterdam_time(hour)
    logger.info(f"Fetching trips for {date_time}")

    # get trips async
    trips = await run.io_bound(ns.get_trips, where, date_time)
    spinner.visible = False
    logger.info(f"Retrieved {len(trips)} trips")

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
        ui.link("🫵", "/v1/trains")
        ui.link("➖", f"/v1/trains/{where}/{hour - 1}")
        ui.link("➕", f"/v1/trains/{where}/{hour + 1}")