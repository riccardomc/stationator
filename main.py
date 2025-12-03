#!/usr/bin/env python3
from datetime import timedelta
from nicegui import ui, app
import ns
import asyncio
import storage

# import is necessary to make pages work
import v1
import v2
import v3


@ui.page("/")
async def root():
    storage.init_storage()
    ui.navigate.to("/trains")


@ui.page("/trains")
async def trains_index():
    storage.init_storage()
    ui.link("🏠", "trains/home")
    ui.link("💼", "trains/work")
    ui.link("📈 v3", "/v3/trains")
    ui.link("📋 v2", "/v2/trains")
    ui.link("📊 v1", "/v1/trains")


@ui.page("/trains/{where}")
async def trains_where(where: str):
    storage.init_storage()
    hour = int(ns.get_amsterdam_time().hour)
    ui.navigate.to(f"/trains/{where}/{hour}")


@ui.page("/trains/{where}/{hour}")
async def trains_where_hour(where: str, hour: int):
    storage.init_storage()
    # Redirect to v3 implementation
    ui.navigate.to(f"/v3/trains/{where}/{hour}")


async def get_trips():
    hour = int(ns.get_amsterdam_time().hour)
    date_time = ns.get_amsterdam_time(hour)
    ns.fetch_trips.cache_clear()

    #cache trips home now, and +1 -1 hour
    await ns.get_trips(where_to="home", date_time=date_time)
    await ns.get_trips(where_to="home", date_time=date_time + timedelta(hours=1))

    #cache trips work now, and +1 -1 hour
    await ns.get_trips(where_to="work", date_time=date_time)
    await ns.get_trips(where_to="work", date_time=date_time + timedelta(hours=1))


@app.on_startup
async def startup():
    """Set up background tasks on app startup."""
    async def periodic_trips():
        """Periodically fetch trips every 5 minutes."""
        while True:
            await get_trips()
            await asyncio.sleep(300)  # 5 minutes

    asyncio.create_task(periodic_trips())


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(host="0.0.0.0", favicon="🚂", title="Stationator", show=False, storage_secret="stationator_secret_key")
