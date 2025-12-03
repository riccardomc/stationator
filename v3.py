#!/usr/bin/env python3
from datetime import datetime, timedelta
from nicegui import ui, app
import ns
import logging
import storage
import icons
import asyncio

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


def format_minutes(minutes: int) -> str:
    """Format minutes as 'h:min' if >= 1 hour, or just 'min' if < 1 hour.

    Preserves original sign behavior: '-' prefix for future (>=0), '+' prefix for past (<0).
    """
    abs_minutes = abs(minutes)
    if abs_minutes >= 60:
        hours = abs_minutes // 60
        mins = abs_minutes % 60
        formatted = f"{hours}h {mins:02d}m"
    else:
        formatted = str(abs_minutes) + "m"

    # Preserve original sign behavior: '-' for future (>=0), '+' for past (<0)
    if minutes >= 0:
        return f"-{formatted}"
    else:
        return f"+{formatted}"


@ui.page("/v3/trains")
async def v3_trains_index():
    logger.info("Rendering v3 trains index page")
    with ui.link("", "trains/home").classes('no-underline'):
        ui.html(icons.ns_icon('home', 24), sanitize=False)
    with ui.link("", "trains/work").classes('no-underline'):
        ui.html(icons.ns_icon('work', 24), sanitize=False)
    with ui.link("", "/trains").classes('no-underline'):
        ui.html(icons.ns_icon('back', 20), sanitize=False)
        ui.label("back")


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

    # Track selected trip index
    selected_trip_index = {'value': None}

    def get_trip_id(trip) -> str:
        """Generate a unique, stable ID for a trip based on its key attributes."""
        dep_time_str = trip.departure_time.strftime("%H%M")
        return f"trip-{trip.origin}-{trip.destination}-{dep_time_str}"

    async def scroll_to_anchor_if_present():
        """Scroll to anchor in URL if present."""
        await asyncio.sleep(0.3)  # Wait for rendering
        ui.run_javascript('''
            const hash = window.location.hash.substring(1);
            if (hash) {
                const element = document.getElementById(hash);
                if (element) {
                    setTimeout(() => {
                        element.scrollIntoView({behavior: "smooth", block: "center"});
                        // Find the trip index and select it
                        const tripRows = document.querySelectorAll('[id^="trip-"]');
                        tripRows.forEach((row, idx) => {
                            if (row.id === hash) {
                                row.click();
                            }
                        });
                    }, 100);
                }
            }
        ''')

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
                        with ui.link("", "/v3/trains").classes('no-underline'):
                            ui.html(icons.ns_icon('menu', 24), sanitize=False)
                        with ui.link("", f"/v3/trains/{where}/{hour - 1}").classes('no-underline'):
                            ui.html(icons.ns_icon('prev', 24), sanitize=False)
                        with ui.link("", f"/v3/trains/{where}/{hour + 1}").classes('no-underline'):
                            ui.html(icons.ns_icon('next', 24), sanitize=False)

                    # Right: Trip count, home, refresh and status
                    with ui.row().classes('items-center gap-2'):
                        trip_count_label = ui.label("").classes('text-sm sm:text-base')
                        with ui.label("").classes('text-xl sm:text-2xl'):
                            ui.html(icons.ns_icon('home' if where == 'home' else 'work', 28), sanitize=False)
                        refresh_link = ui.link('', '#').classes('no-underline')
                        with refresh_link:
                            ui.html(icons.ns_icon('refresh', 28), sanitize=False)
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
                        ).classes('text-xs scale-90 sm:scale-100').style('--q-primary: #003082')
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
            # Create container for the chart (no horizontal scrolling)
            chart_container = ui.column().classes('w-full max-w-6xl overflow-x-hidden')

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
                    trip_id = get_trip_id(trip)
                    is_selected = selected_trip_index['value'] == idx
                    row_classes = 'w-full mb-1 items-center cursor-pointer transition-all'
                    if is_selected:
                        row_classes += ' bg-blue-50 rounded p-1'
                    trip_row = ui.row().classes(row_classes)
                    trip_row.props(f'id="{trip_id}"')

                    def make_click_handler(trip_idx, trip_anchor_id):
                        async def on_click():
                            if selected_trip_index['value'] == trip_idx:
                                selected_trip_index['value'] = None
                                # Remove anchor from URL
                                ui.run_javascript(f'history.replaceState(null, "", window.location.pathname)')
                            else:
                                selected_trip_index['value'] = trip_idx
                                # Update URL with anchor
                                ui.run_javascript(f'history.replaceState(null, "", window.location.pathname + "#{trip_anchor_id}")')
                                # Scroll to the trip
                                ui.run_javascript(f'document.getElementById("{trip_anchor_id}").scrollIntoView({{behavior: "smooth", block: "center"}})')
                            await refresh_trips()
                        return on_click

                    trip_row.on('click', make_click_handler(idx, trip_id))

                    with trip_row:
                        # Trip label (left side) - all info on one line
                        with ui.row().classes('w-[320px] flex-shrink-0 pr-2 items-center gap-1 sm:gap-2 flex-nowrap'):
                            # Calculate minutes until departure
                            minutes_until_departure = int((trip.departure_time - current_time).total_seconds() / 60)
                            # Get biking time for origin station
                            origin_station = ns.stations.get(trip.origin)
                            biking_time_minutes = int(origin_station.biking_time.total_seconds() / 60) if origin_station else 15
                            # Color logic: green if >= biking_time, red if < biking_time, gray if past
                            if minutes_until_departure < 0:
                                minutes_label_color = 'text-gray-500'
                            elif minutes_until_departure >= biking_time_minutes:
                                minutes_label_color = 'text-green-600 font-semibold'
                            else:
                                minutes_label_color = 'text-red-600 font-semibold'
                            minutes_display = format_minutes(minutes_until_departure)

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

                        border_color = '#003082' if is_selected else '#003082'
                        border_width = '3px' if is_selected else '1px'
                        gantt_html = f'''
                            <div style="position: relative; width: 100%; height: {row_height}px; background-color: #ffffff; border: {border_width} solid {border_color}; overflow: visible;">
                                {now_line_html}
                                <!-- Leave by label above the box -->
                                <div style="position: absolute; left: {start_percent}%; top: -18px; font-size: 9px; color: #333; font-weight: bold; white-space: nowrap; background-color: rgba(255,255,255,0.9); padding: 0 2px;">{leave_by_str}</div>
                                <!-- Arrive by label above the box -->
                                <div style="position: absolute; left: calc({start_percent}% + {width_percent}%); top: -18px; transform: translateX(-100%); font-size: 9px; color: #333; font-weight: bold; white-space: nowrap; background-color: rgba(255,255,255,0.9); padding: 0 2px;">{arrive_by_str}</div>
                                <div style="position: absolute; left: {start_percent}%; width: {width_percent}%; height: 100%; display: flex; border-radius: 3px; overflow: visible;">
                                    <!-- Biking before (to station) -->
                                    <div style="width: {biking_before_percent}%; background-color: #FFC917; border-right: 1px solid #E6B815; position: relative;" title="Biking to station"></div>
                                    <!-- Train time -->
                                    <div style="position: relative; width: {train_percent}%; background-color: #003082; border-right: 1px solid #002366;" title="Train time">
                                        <div style="position: absolute; left: 2px; top: 2px; font-size: 9px; color: white; font-weight: bold; white-space: nowrap; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">{dep_time_str}</div>
                                        <div style="position: absolute; right: 2px; bottom: 2px; font-size: 9px; color: white; font-weight: bold; white-space: nowrap; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">{arr_time_str}</div>
                                    </div>
                                    <!-- Biking after (from station) -->
                                    <div style="width: {biking_after_percent}%; background-color: #FFC917; position: relative;" title="Biking from station"></div>
                                </div>
                            </div>
                        '''
                        gantt_bar.set_content(gantt_html)

        # Check for anchor after trips are rendered
        await scroll_to_anchor_if_present()

    # Initial load of trips
    await refresh_trips()

