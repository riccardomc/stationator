#!/usr/bin/env python3
from datetime import timedelta
from nicegui import ui
import ns
import asyncio
import storage

# import is necessary to make pages work
import v1
import v2


@ui.page("/")
def root():
    storage.init_storage()
    ui.navigate.to("/trains")


@ui.page("/trains")
def trains_index():
    storage.init_storage()
    ui.link("🏠", "trains/home")
    ui.link("💼", "trains/work")
    ui.link("📊 v1", "/v1/trains")


@ui.page("/trains/{where}")
async def trains_where(where: str):
    storage.init_storage()
    hour = int(ns.get_amsterdam_time().hour)
    ui.navigate.to(f"/trains/{where}/{hour}")


@ui.page("/trains/{where}/{hour}")
async def trains_where_hour(where: str, hour: int):
    storage.init_storage()
    # Redirect to v2 implementation
    ui.navigate.to(f"/v2/trains/{where}/{hour}")


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


ui.timer(300, lambda: asyncio.create_task(get_trips()))
ui.run(host="0.0.0.0", favicon="🚂", title="Stationator", show=False, storage_secret="stationator_secret_key")
