#!/usr/bin/env python3
from datetime import datetime, timedelta
from nicegui import ui, run
import ns


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
    ui.link("🏠", "trains/home").classes('no-underline')
    ui.link("💼", "trains/work").classes('no-underline')
    ui.link("⬅️ back", "/trains").classes('no-underline')


@ui.page("/v2/trains/{where}")
async def v2_trains_where(where: str):
    hour = int(ns.get_amsterdam_time().hour)
    ui.navigate.to(f"/v2/trains/{where}/{hour}")


@ui.page("/v2/trains/{where}/{hour}")
async def v2_trains_where_hour(where: str, hour: int):
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

    # Create a container for the cards
    with ui.column().classes('w-full items-center gap-2 sm:gap-4 px-1 sm:px-4'):
        # Add navigation controls at the top
        with ui.row().classes('w-full max-w-3xl justify-between items-center mb-2 sm:mb-4'):
            ui.link("🫵", "/v2/trains").classes('text-xl sm:text-2xl no-underline')
            with ui.row().classes('gap-2'):
                ui.link("➖", f"/v2/trains/{where}/{hour - 1}").classes('text-xl sm:text-2xl no-underline')
                ui.link("➕", f"/v2/trains/{where}/{hour + 1}").classes('text-xl sm:text-2xl no-underline')

        # Update label
        now = date_time.strftime("%H:%M")
        label.bind_text_from(
            trips,
            "length",
            lambda length: f"Found {length} trips at {now}",
        )

        # Group trips by station (origin for work, destination for home)
        trips_by_station = {}
        for trip in trips:
            station = trip.destination if where == "home" else trip.origin
            if station not in trips_by_station:
                trips_by_station[station] = []
            trips_by_station[station].append(trip)

        # Sort stations alphabetically
        sorted_stations = sorted(trips_by_station.keys())

        # Create columns for each station
        with ui.row().classes('w-full max-w-3xl gap-2 sm:gap-8 justify-center flex-wrap'):
            for station in sorted_stations:
                with ui.column().classes('items-center'):
                    # Station header
                    station_type = "🛬" if where == "home" else "🛫"
                    ui.label(f"{station_type} {station.upper()}").classes('text-lg sm:text-xl font-bold mb-1 sm:mb-2')

                    # Cards for this station
                    for trip in trips_by_station[station]:
                        with ui.card().classes('mb-2 sm:mb-4'):
                            with ui.card_section().classes('flex flex-col gap-1 sm:gap-2 p-2 sm:p-4'):
                                # Main journey info
                                with ui.row().classes('justify-between items-center gap-1 sm:gap-4'):
                                    # Departure info
                                    with ui.column().classes('items-start w-[100px] sm:w-[120px]'):
                                        ui.label(f"🕗 {format_timedelta(trip.departure_time)}").classes('text-lg sm:text-xl font-bold')
                                        ui.label(f"🛫 {trip.origin.upper()}").classes('text-base sm:text-lg')
                                        if trip.departure_track:
                                            ui.label(f"🚉 {trip.departure_track}").classes('text-xs sm:text-sm text-gray-600')

                                    # Journey info
                                    with ui.column().classes('items-center hidden sm:flex w-[60px]'):
                                        with ui.column().classes('items-center gap-1'):
                                            ui.label("→").classes('text-xl sm:text-2xl')
                                            ui.label(f"⏱️ {format_timedelta(trip.travel_time)}").classes('text-xs sm:text-sm text-gray-600')

                                    # Arrival info
                                    with ui.column().classes('items-end w-[100px] sm:w-[120px]'):
                                        ui.label(f"{format_timedelta(trip.arrival_time)} 🕓").classes('text-lg sm:text-xl font-bold')
                                        ui.label(f"{trip.destination.upper()} 🛬").classes('text-base sm:text-lg')
                                        if trip.arrival_track:
                                            ui.label(f"{trip.arrival_track} 🚉").classes('text-xs sm:text-sm text-gray-600')

                                # Travel time for mobile
                                with ui.row().classes('sm:hidden justify-center items-center gap-1 mt-1 sm:mt-2 pt-1 sm:pt-2 border-t'):
                                    ui.label("→").classes('text-xl')
                                    ui.label(f"⏱️ {format_timedelta(trip.travel_time)}").classes('text-xs text-gray-600')

                                # Additional journey details
                                with ui.row().classes('justify-between items-center mt-1 sm:mt-2 pt-1 sm:pt-2 border-t gap-1 sm:gap-4'):
                                    with ui.column().classes('items-start w-[120px] sm:w-[140px]'):
                                        ui.label(f"🚀 {format_timedelta(trip.leave_by)}").classes('text-xs sm:text-sm')
                                        ui.label(f"🚴 {format_timedelta(trip.biking_time)}").classes('text-xs sm:text-sm')
                                    with ui.column().classes('items-end w-[120px] sm:w-[140px]'):
                                        ui.label(f"{format_timedelta(trip.arrive_by)} 😰").classes('text-xs sm:text-sm')
                                        ui.label(f"{format_timedelta(trip.train_time)} 💺").classes('text-xs sm:text-sm')

                                # Status and direction indicator
                                with ui.row().classes('justify-between items-center mt-1 sm:mt-2 pt-1 sm:pt-2 border-t gap-1 sm:gap-4'):
                                    with ui.column().classes('items-start w-[120px] sm:w-[140px]'):
                                        if trip.direction:
                                            ui.label(f"🏁 {trip.direction}").classes('text-xs sm:text-sm text-gray-600')
                                    with ui.column().classes('items-end w-[120px] sm:w-[140px]'):
                                        status_color = {
                                            'NORMAL': 'text-green-600',
                                            'CANCELLED': 'text-red-600',
                                            'DELAYED': 'text-yellow-600'
                                        }.get(trip.status, 'text-gray-600')
                                        ui.label(f"{trip.status} ☠️").classes(f'text-xs sm:text-sm {status_color}')