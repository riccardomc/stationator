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


@ui.page("/v3/trains")
async def v3_trains_index():
    logger.info("Rendering v3 trains index page")
    ui.link("🏠", "trains/home").classes('no-underline')
    ui.link("💼", "trains/work").classes('no-underline')
    ui.link("⬅️ back", "/trains").classes('no-underline')


@ui.page("/v3/trains/{where}")
async def v3_trains_where(where: str):
    logger.info(f"Navigating to v3 trains for destination: {where}")
    hour = int(ns.get_amsterdam_time().hour)
    ui.navigate.to(f"/v3/trains/{where}/{hour}")


@ui.page("/v3/trains/{where}/{hour}")
async def v3_trains_where_hour(where: str, hour: int):
    logger.info(f"Rendering v3 trains page for {where} at hour {hour}")
    # already display page once client websocket is connected
    await ui.context.client.connected()

    # Initialize storage
    storage.init_storage()

    # Create a container for the page
    container = ui.column().classes('w-full items-center gap-2 px-2 sm:px-4')

    async def refresh_trips():
        """Fetch and display trips as Gantt chart."""
        container.clear()

        # Show loading state
        with container:
            # Top bar - stack on mobile, row on desktop
            with ui.column().classes('w-full max-w-6xl mb-2 gap-2'):
                # First row: Navigation and refresh/status
                with ui.row().classes('w-full justify-between items-center flex-wrap gap-2'):
                    # Left: Navigation
                    with ui.row().classes('items-center gap-2'):
                        ui.link("🫵", "/v3/trains").classes('text-lg sm:text-xl no-underline')
                        ui.link("➖", f"/v3/trains/{where}/{hour - 1}").classes('text-lg sm:text-xl no-underline')
                        ui.link("➕", f"/v3/trains/{where}/{hour + 1}").classes('text-lg sm:text-xl no-underline')
                    
                    # Right: Trip count, home, refresh and status
                    with ui.row().classes('items-center gap-2'):
                        trip_count_label = ui.label("").classes('text-sm sm:text-base')
                        home_emoji = ui.label(f"{'🏠' if where == 'home' else '💼'}").classes('text-xl sm:text-2xl')
                        refresh_link = ui.link('🔄', '#').classes('text-xl sm:text-2xl no-underline')
                        async def on_refresh():
                            await refresh_trips()
                        refresh_link.on('click', on_refresh)
                        spinner = ui.spinner()
                
                # Second row: Station selection - wrap on mobile
                with ui.row().classes('w-full items-center gap-1 sm:gap-2 flex-wrap justify-center sm:justify-start'):
                    station_selection = app.storage.user['station_selection']
                    for station_code, station in ns.stations.items():
                        checkbox = ui.checkbox(
                            station_code.upper(),
                            value=station_selection[station_code]
                        ).classes('text-xs scale-90 sm:scale-100')
                        checkbox.bind_value(station_selection, station_code)

        # set time
        date_time = ns.get_amsterdam_time(hour)
        logger.info(f"Fetching trips for {date_time}")

        # get trips async
        trips = await ns.get_trips(where, date_time)
        spinner.visible = False
        logger.info(f"Retrieved {len(trips)} trips")

        # Filter trips based on station selection
        station_selection = app.storage.user['station_selection']
        filtered_trips = [
            trip for trip in trips
            if station_selection[trip.origin] and 
               station_selection[trip.destination]
        ]

        # Sort trips by arrival_time
        filtered_trips.sort(key=lambda t: t.arrival_time)

        # Update trip count label
        now = date_time.strftime("%H:%M")
        trip_count_label.set_text(f"{len(filtered_trips)} trips at {now}")

        if not filtered_trips:
            with container:
                ui.label("No trips available").classes('text-lg text-gray-500 mt-4')
            return

        # Calculate time range for the chart
        min_time = min(trip.leave_by for trip in filtered_trips)
        max_time = max(trip.arrive_by for trip in filtered_trips)
        total_duration = max_time - min_time

        # Create Gantt chart container
        with container:
            # Create scrollable container for the chart
            chart_container = ui.column().classes('w-full max-w-6xl overflow-x-auto')
            
            with chart_container:
                # Calculate chart width
                chart_width = max(800, int(total_duration.total_seconds() * 2))  # 2px per second, minimum 800px

                # Calculate current time position
                current_time = ns.get_amsterdam_time(round_to_hour=False)
                now_position_percent = 0
                if min_time <= current_time <= max_time:
                    now_offset = (current_time - min_time).total_seconds()
                    now_position_percent = (now_offset / total_duration.total_seconds()) * 100 if total_duration.total_seconds() > 0 else 0

                # Gantt chart rows
                row_height = 35
                for idx, trip in enumerate(filtered_trips):
                    with ui.row().classes('w-full mb-1 items-center'):
                        # Trip label (left side) - all info on one line
                        with ui.row().classes('w-[320px] flex-shrink-0 pr-2 items-center gap-1 sm:gap-2 flex-nowrap'):
                            # Calculate minutes until departure
                            minutes_until_departure = int((trip.departure_time - current_time).total_seconds() / 60)
                            # Color logic: green if >= 15, red if < 15, gray if past
                            if minutes_until_departure < 0:
                                minutes_label_color = 'text-gray-500'
                            elif minutes_until_departure >= 15:
                                minutes_label_color = 'text-green-600 font-semibold'
                            else:
                                minutes_label_color = 'text-red-600 font-semibold'
                            minutes_display = f"-{abs(minutes_until_departure)}" if minutes_until_departure >= 0 else f"+{abs(minutes_until_departure)}"
                            
                            # Order: origin -> destination, status, direction, track number, travel_time, minutes_to_go (right justified)
                            ui.label(f"{trip.origin.upper()} → {trip.destination.upper()}").classes('text-[10px] sm:text-xs font-bold whitespace-nowrap')
                            # Status with color coding - always shown
                            status_color = {
                                'NORMAL': 'text-green-600 font-semibold',
                                'CANCELLED': 'text-red-600 font-semibold',
                                'DELAYED': 'text-yellow-600 font-semibold'
                            }.get(trip.status, 'text-gray-600')
                            ui.label(f"{trip.status}").classes(f'text-[10px] sm:text-xs {status_color} whitespace-nowrap')
                            if trip.direction:
                                ui.label(f"{trip.direction}").classes('text-[10px] sm:text-xs text-gray-600 whitespace-nowrap')
                            if trip.departure_track:
                                ui.label(f"{trip.departure_track}").classes('text-[10px] sm:text-xs text-gray-500 whitespace-nowrap')
                            ui.label(f"{format_timedelta(trip.travel_time)}").classes('text-[10px] sm:text-xs text-gray-500 whitespace-nowrap')
                            # Minutes to go - right justified
                            ui.label(minutes_display).classes(f'text-[10px] sm:text-xs {minutes_label_color} whitespace-nowrap ml-auto')
                        
                        # Gantt bar container
                        gantt_bar = ui.html('', sanitize=False).style(f'width: {chart_width}px; position: relative;')
                        
                        # Calculate positions and widths
                        trip_start_offset = (trip.leave_by - min_time).total_seconds()
                        trip_end_offset = (trip.arrive_by - min_time).total_seconds()
                        total_trip_duration = (trip.arrive_by - trip.leave_by).total_seconds()
                        
                        start_percent = (trip_start_offset / total_duration.total_seconds()) * 100 if total_duration.total_seconds() > 0 else 0
                        width_percent = (total_trip_duration / total_duration.total_seconds()) * 100 if total_duration.total_seconds() > 0 else 0
                        
                        # Calculate segments using actual time differences
                        biking_before_seconds = (trip.departure_time - trip.leave_by).total_seconds()
                        train_time_seconds = (trip.arrival_time - trip.departure_time).total_seconds()
                        biking_after_seconds = (trip.arrive_by - trip.arrival_time).total_seconds()
                        
                        biking_before_percent = (biking_before_seconds / total_trip_duration) * 100 if total_trip_duration > 0 else 0
                        train_percent = (train_time_seconds / total_trip_duration) * 100 if total_trip_duration > 0 else 0
                        biking_after_percent = (biking_after_seconds / total_trip_duration) * 100 if total_trip_duration > 0 else 0
                        
                        # Format times for display
                        dep_time_str = format_timedelta(trip.departure_time)
                        arr_time_str = format_timedelta(trip.arrival_time)
                        leave_by_str = format_timedelta(trip.leave_by)
                        arrive_by_str = format_timedelta(trip.arrive_by)
                        
                        # Create Gantt bar HTML
                        # Add "now" line if current time is within the chart range
                        now_line_html = ''
                        if min_time <= current_time <= max_time:
                            now_line_html = f'<div style="position: absolute; left: {now_position_percent}%; top: 0; width: 2px; height: 100%; background-color: #f44336; z-index: 10;" title="Now"></div>'
                        
                        gantt_html = f'''
                            <div style="position: relative; width: 100%; height: {row_height}px; background-color: #f5f5f5; border: 1px solid #ddd; overflow: visible;">
                                {now_line_html}
                                <div style="position: absolute; left: {start_percent}%; width: {width_percent}%; height: 100%; display: flex; border-radius: 3px; overflow: visible;">
                                    <!-- Leave by label at the beginning -->
                                    <div style="position: absolute; left: 0; top: 50%; transform: translateY(-50%) translateX(-100%); padding-right: 4px; font-size: 9px; color: #333; font-weight: bold; white-space: nowrap; background-color: rgba(255,255,255,0.9);">{leave_by_str}</div>
                                    <!-- Biking before (to station) -->
                                    <div style="width: {biking_before_percent}%; background-color: #4CAF50; border-right: 1px solid #2E7D32; position: relative;" title="Biking to station"></div>
                                    <!-- Train time -->
                                    <div style="position: relative; width: {train_percent}%; background-color: #2196F3; border-right: 1px solid #1565C0;" title="Train time">
                                        <div style="position: absolute; left: 2px; top: 2px; font-size: 9px; color: white; font-weight: bold; white-space: nowrap; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">{dep_time_str}</div>
                                        <div style="position: absolute; right: 2px; bottom: 2px; font-size: 9px; color: white; font-weight: bold; white-space: nowrap; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">{arr_time_str}</div>
                                    </div>
                                    <!-- Biking after (from station) -->
                                    <div style="width: {biking_after_percent}%; background-color: #4CAF50; position: relative;" title="Biking from station"></div>
                                    <!-- Arrive by label at the end -->
                                    <div style="position: absolute; right: 0; top: 50%; transform: translateY(-50%) translateX(100%); padding-left: 4px; font-size: 9px; color: #333; font-weight: bold; white-space: nowrap; background-color: rgba(255,255,255,0.9);">{arrive_by_str}</div>
                                </div>
                            </div>
                        '''
                        gantt_bar.set_content(gantt_html)

    # Initial load of trips
    await refresh_trips()

