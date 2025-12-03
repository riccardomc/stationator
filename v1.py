#!/usr/bin/env python3
from datetime import datetime, timedelta
from nicegui import ui, app
import ns
import logging
import storage

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
async def v1_trains_index():
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

    # Initialize storage
    storage.init_storage()

    # Add label and spinner
    with ui.row().classes('w-full justify-left gap-2 mb-4'):
        label = ui.label(f"Fetching trips to {where}...")
        spinner = ui.spinner()

    # set time
    date_time = ns.get_amsterdam_time(hour)
    logger.info(f"Fetching trips for {date_time}")

    # get trips async
    trips = await ns.get_trips(where, date_time)
    spinner.visible = False
    logger.info(f"Retrieved {len(trips)} trips")

    # Hide spinner and update label
    spinner.visible = False
    label.set_text(f"Found {len(trips)} trips at {date_time.strftime('%H:%M')}")

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

    # Update label and filter rows
    now = date_time.strftime("%H:%M")
    station_selection = app.storage.user['station_selection']
    def update_label():
        filtered_rows = [
            row for row in rows
            if station_selection[row['origin']] and station_selection[row['destination']]
        ]
        table.rows = filtered_rows
        label.set_text(f"Found {len(filtered_rows)} trips at {now}")

    # Add station selection checkboxes
    with ui.row().classes('w-full justify-left gap-4 mb-4'):
        station_selection = app.storage.user['station_selection']
        for station_code, station in ns.stations.items():
            checkbox = ui.checkbox(
                station_code.upper(),
                value=station_selection[station_code]
            ).classes('text-base')
            checkbox.bind_value(app.storage.user['station_selection'], station_code)
            checkbox.on('change', update_label)

        # Add refresh link
        refresh_link = ui.link('🔄', '#').classes('text-base no-underline')
        refresh_link.on('click', lambda: ui.navigate.to(f"/v1/trains/{where}/{hour}"))

    # Initial label update
    update_label()

    # add back link
    with ui.row():
        ui.link("🫵", "/v1/trains")
        ui.link("➖", f"/v1/trains/{where}/{hour - 1}")
        ui.link("➕", f"/v1/trains/{where}/{hour + 1}")