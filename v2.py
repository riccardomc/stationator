#!/usr/bin/env python3
from datetime import datetime, timedelta
from nicegui import ui, run, app
import ns
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def format_timedelta(td) -> str:
    """Convert timedelta or datetime to HH:MM format string."""
    if isinstance(td, datetime):
        return td.strftime("%H:%M")
    elif isinstance(td, timedelta):
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    return str(td)


@ui.page("/v2/trains")
def v2_trains_index():
    logger.info("Rendering v2 trains index page")
    ui.link("🏠", "trains/home").classes('no-underline')
    ui.link("💼", "trains/work").classes('no-underline')
    ui.link("⬅️ back", "/trains").classes('no-underline')


@ui.page("/v2/trains/{where}")
async def v2_trains_where(where: str):
    logger.info(f"Navigating to v2 trains for destination: {where}")
    hour = int(ns.get_amsterdam_time().hour)
    ui.navigate.to(f"/v2/trains/{where}/{hour}")


@ui.page("/v2/trains/{where}/{hour}")
async def v2_trains_where_hour(where: str, hour: int):
    logger.info(f"Rendering v2 trains page for {where} at hour {hour}")
    # already display page once client websocket is connected
    await ui.context.client.connected()

    # Initialize storage
    import storage
    storage.init_storage()

    # Create a container for the cards
    container = ui.column().classes('w-full items-center gap-1 sm:gap-2 px-1 sm:px-4')

    # Create a container for the trips
    trips_container = ui.column().classes('w-full items-center gap-1 sm:gap-2')

    async def refresh_trips():
        """Fetch and display trips."""
        # Clear existing trips
        trips_container.clear()
        container.clear()

        # Show loading state at the top
        with container:
            with ui.row().classes('w-full max-w-3xl justify-between items-center mb-1 sm:mb-2'):
                # Left side: Navigation
                with ui.row().classes('items-center gap-2'):
                    ui.link("🫵", "/v2/trains").classes('text-xl sm:text-2xl no-underline')
                    ui.link("➖", f"/v2/trains/{where}/{hour - 1}").classes('text-xl sm:text-2xl no-underline')
                    ui.link("➕", f"/v2/trains/{where}/{hour + 1}").classes('text-xl sm:text-2xl no-underline')

                # Center: Station selection
                with ui.row().classes('items-center gap-2 sm:gap-3'):
                    for station_code, station in ns.stations.items():
                        checkbox = ui.checkbox(
                            station_code.upper(),
                            value=app.storage.user['station_selection'][station_code]
                        ).classes('text-sm')
                        checkbox.bind_value(app.storage.user['station_selection'], station_code)

                # Right side: Refresh and status
                with ui.row().classes('items-center gap-2'):
                    refresh_link = ui.link('🔄', '#').classes('text-xl sm:text-2xl no-underline')
                    async def on_refresh():
                        await refresh_trips()
                    refresh_link.on('click', on_refresh)
                    label = ui.label(f"{'🏠' if where == 'home' else '💼'}").classes('text-xl sm:text-2xl')
                    spinner = ui.spinner()

        # set time
        date_time = ns.get_amsterdam_time(hour)
        logger.info(f"Fetching trips for {date_time}")

    # get trips async
    trips = await ns.get_trips(where, date_time)
    spinner.visible = False
    logger.info(f"Retrieved {len(trips)} trips")

        # Update label
        now = date_time.strftime("%H:%M")
        label.bind_text_from(
            trips,
            "length",
            lambda length: f"{'🏠' if where == 'home' else '💼'} {length} trips at {now}",
        )

        # Group trips by station (origin for work, destination for home)
        trips_by_station = {}
        for trip in trips:
            # Skip trips where either origin or destination is not selected
            if not app.storage.user['station_selection'][trip.origin] or not app.storage.user['station_selection'][trip.destination]:
                continue

            station = trip.destination if where == "home" else trip.origin
            if station not in trips_by_station:
                trips_by_station[station] = []
            trips_by_station[station].append(trip)

        # Sort stations alphabetically
        sorted_stations = sorted(trips_by_station.keys())
        logger.info(f"Grouped trips by {len(sorted_stations)} stations: {sorted_stations}")

        # Create columns for each station
        with trips_container:
            with ui.row().classes('w-full max-w-3xl gap-2 sm:gap-4 justify-center flex-wrap'):
                for station in sorted_stations:
                    # Skip stations that are not selected
                    if not app.storage.user['station_selection'][station]:
                        continue

                    with ui.column().classes('items-center'):
                        # Station header
                        station_type = "🛬" if where == "home" else "🛫"
                        ui.label(f"{station_type} {station.upper()}").classes('text-base sm:text-lg font-bold mb-1')

                        # Cards for this station
                        for trip in trips_by_station[station]:
                            with ui.card().classes('mb-1 sm:mb-2'):
                                with ui.card_section().classes('flex flex-col gap-1 p-2 sm:p-3'):
                                    # Main journey info
                                    with ui.row().classes('justify-between items-center gap-1 sm:gap-2'):
                                        # Departure info
                                        with ui.column().classes('items-start w-[100px] sm:w-[120px]'):
                                            ui.label(f"🕗 {format_timedelta(trip.departure_time)}").classes('text-base sm:text-lg font-bold')
                                            ui.label(f"🛫 {trip.origin.upper()}").classes('text-sm sm:text-base')
                                            if trip.departure_track:
                                                ui.label(f"🚉 {trip.departure_track}").classes('text-xs text-gray-600')

                                        # Journey info
                                        with ui.column().classes('items-center hidden sm:flex w-[60px]'):
                                            with ui.column().classes('items-center gap-1'):
                                                ui.label("→").classes('text-lg sm:text-xl')
                                                ui.label(f"⏱️ {format_timedelta(trip.travel_time)}").classes('text-xs text-gray-600')

                                        # Arrival info
                                        with ui.column().classes('items-end w-[100px] sm:w-[120px]'):
                                            ui.label(f"{format_timedelta(trip.arrival_time)} 🕓").classes('text-base sm:text-lg font-bold')
                                            ui.label(f"{trip.destination.upper()} 🛬").classes('text-sm sm:text-base')
                                            if trip.arrival_track:
                                                ui.label(f"{trip.arrival_track} ��").classes('text-xs text-gray-600')

                                    # Travel time for mobile
                                    with ui.row().classes('sm:hidden justify-center items-center gap-1 mt-1 pt-1 border-t'):
                                        ui.label("→").classes('text-lg')
                                        ui.label(f"⏱️ {format_timedelta(trip.travel_time)}").classes('text-xs text-gray-600')

                                    # Additional journey details
                                    with ui.row().classes('justify-between items-center mt-1 pt-1 border-t gap-1 sm:gap-2'):
                                        with ui.column().classes('items-start w-[120px] sm:w-[140px]'):
                                            ui.label(f"🚀 {format_timedelta(trip.leave_by)}").classes('text-xs')
                                            ui.label(f"🚴 {format_timedelta(trip.biking_time)}").classes('text-xs')
                                        with ui.column().classes('items-end w-[120px] sm:w-[140px]'):
                                            ui.label(f"{format_timedelta(trip.arrive_by)} 😰").classes('text-xs')
                                            ui.label(f"{format_timedelta(trip.train_time)} 💺").classes('text-xs')

                                    # Status and direction indicator
                                    with ui.row().classes('justify-between items-center mt-1 pt-1 border-t gap-1 sm:gap-2'):
                                        with ui.column().classes('items-start w-[120px] sm:w-[140px]'):
                                            if trip.direction:
                                                ui.label(f"🏁 {trip.direction}").classes('text-xs text-gray-600')
                                        with ui.column().classes('items-end w-[120px] sm:w-[140px]'):
                                            status_color = {
                                                'NORMAL': 'text-green-600',
                                                'CANCELLED': 'text-red-600',
                                                'DELAYED': 'text-yellow-600'
                                            }.get(trip.status, 'text-gray-600')
                                            ui.label(f"{trip.status} ☠️").classes(f'text-xs {status_color}')

    # Initial load of trips
    await refresh_trips()