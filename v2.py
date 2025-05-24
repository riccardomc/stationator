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
    ui.link("🏠", "trains/home")
    ui.link("💼", "trains/work")
    ui.link("⬅️ back", "/trains")


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
    with ui.column().classes('w-full items-center gap-4 p-4'):
        # Add navigation controls at the top
        with ui.row().classes('w-full max-w-3xl justify-between items-center mb-4'):
            ui.link("🫵", "/v2/trains").classes('text-2xl')
            with ui.row().classes('gap-2'):
                ui.link("➖", f"/v2/trains/{where}/{hour - 1}").classes('text-2xl')
                ui.link("➕", f"/v2/trains/{where}/{hour + 1}").classes('text-2xl')

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
        with ui.row().classes('w-full max-w-3xl gap-8 justify-center'):
            for station in sorted_stations:
                with ui.column().classes('items-center'):
                    # Station header
                    station_type = "🛬" if where == "home" else "🛫"
                    ui.label(f"{station_type} {station.upper()}").classes('text-xl font-bold mb-2')
                    
                    # Cards for this station
                    for trip in trips_by_station[station]:
                        with ui.card().classes('w-fit mb-4'):
                            with ui.card_section().classes('flex flex-col gap-2'):
                                # Main journey info
                                with ui.row().classes('justify-between items-center gap-4'):
                                    with ui.column().classes('items-start'):
                                        ui.label(f"🕗 {format_timedelta(trip.departure_time)}").classes('text-xl font-bold')
                                        ui.label(f"🛫 {trip.origin.upper()}").classes('text-lg')
                                        if trip.departure_track:
                                            ui.label(f"🚉 Track {trip.departure_track}").classes('text-sm text-gray-600')
                                    with ui.column().classes('items-center'):
                                        with ui.column().classes('items-center gap-1'):
                                            ui.label("→").classes('text-2xl')
                                            ui.label(f"⏱️ {format_timedelta(trip.travel_time)}").classes('text-sm text-gray-600')
                                    with ui.column().classes('items-end'):
                                        ui.label(f"🕓 {format_timedelta(trip.arrival_time)}").classes('text-xl font-bold')
                                        ui.label(f"🛬 {trip.destination.upper()}").classes('text-lg')
                                        if trip.arrival_track:
                                            ui.label(f"🚉 Track {trip.arrival_track}").classes('text-sm text-gray-600')

                                # Additional journey details
                                with ui.row().classes('justify-between items-center mt-2 pt-2 border-t gap-4'):
                                    with ui.column().classes('items-start'):
                                        ui.label(f"🚀 Leave by: {format_timedelta(trip.leave_by)}").classes('text-sm')
                                        ui.label(f"🚴 Biking: {format_timedelta(trip.biking_time)}").classes('text-sm')
                                    with ui.column().classes('items-end'):
                                        ui.label(f"😰 Arrive by: {format_timedelta(trip.arrive_by)}").classes('text-sm')
                                        ui.label(f"💺 Train: {format_timedelta(trip.train_time)}").classes('text-sm')

                                # Status and direction indicator
                                with ui.row().classes('justify-between items-center mt-2 pt-2 border-t gap-4'):
                                    with ui.column().classes('items-start'):
                                        if trip.direction:
                                            ui.label(f"🏁 {trip.direction}").classes('text-sm text-gray-600')
                                    with ui.column().classes('items-end'):
                                        status_color = {
                                            'NORMAL': 'text-green-600',
                                            'CANCELLED': 'text-red-600',
                                            'DELAYED': 'text-yellow-600'
                                        }.get(trip.status, 'text-gray-600')
                                        ui.label(f"☠️ {trip.status}").classes(f'text-sm {status_color}') 