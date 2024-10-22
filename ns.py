#!/usr/bin/env python

import os
import json
import dateutil.parser
import urllib.request
from datetime import datetime, timedelta

stations = {
    "asd": {
        "full_name": "Amsterdam Centraal",
        "short_name": "asd",
        "biking_time": "00:10",
    },
    "asdz": {
        "full_name": "Amsterdam Zuid",
        "short_name": "asdz",
        "biking_time": "00:14",
    },
    "gvc": {
        "full_name": "Den Haag Centraal",
        "short_name": "gvc",
        "biking_time": "00:11",
    },
    "laa": {
        "full_name": "Den Haag Laan van NOI",
        "short_name": "laa",
        "biking_time": "00:14",
    },
}


class Station(super):

    def __init__(self, station_data):
        self.full_name = station_data["full_name"]
        self.short_name = station_data["short_name"]
        d = datetime.strptime(station_data["biking_time"], "%H:%M")
        d = timedelta(hours=d.hour, minutes=d.minute, seconds=d.second)
        self.biking_time = d


# Generate Stations map
for k, v in stations.items():
    stations[k] = Station(v)


class Trip(super):

    def __init__(self, trip_data):
        self.transfers = trip_data["transfers"]
        self.destination = trip_data["legs"][0]["destination"]["stationCode"].lower(
        )
        self.origin = trip_data["legs"][0]["origin"]["stationCode"].lower()
        self.departure_time = dateutil.parser.isoparse(
            trip_data["legs"][0]["origin"]["plannedDateTime"]
        )
        self.arrival_time = dateutil.parser.isoparse(
            trip_data["legs"][0]["destination"]["plannedDateTime"]
        )
        self.status = trip_data["status"]
        self.leave_by = self._leave_by()
        self.arrive_by = self._arrive_by()
        # self.biking_time = self._biking_time()

    def _leave_by(self):
        origin_station = stations.get(self.origin, None)
        if origin_station:
            return self.departure_time - origin_station.biking_time

    def _arrive_by(self):
        destination_station = stations.get(self.destination, None)
        if destination_station:
            return self.arrival_time + destination_station.biking_time

    def _biking_time(self):
        origin_station = stations.get(self.origin, None)
        destination_station = stations.get(self.destination, None)
        if destination_station and origin_station:
            return destination_station.biking_time + origin_station.biking_time
        elif origin_station:
            return origin_station.biking_time
        elif destination_station:
            return destination_station.biking_time

        return None

    def __str__(self):
        return f"""{
            self.departure_time.strftime("%H:%M")}, {
            self.arrival_time.strftime("%H:%M")}, {
            self.origin}, {
            self.destination}, {
            self.transfers}, {
            self.status}, {
            self.leave_by.strftime("%H:%M")}, {
            self.arrive_by.strftime("%H:%M")}"""

    def json(self):
        return json.dumps(vars(self), default=str, sort_keys=True, indent=2)


def fetch_trips(origin="laa", destination="asdz"):
    api_key = os.getenv("NS_API_KEY")
    try:
        url = f"""
        https://gateway.apiportal.ns.nl/reisinformatie-api/api/v3/trips?fromStation={
            origin}&toStation={destination}"""

        hdr = {"Cache-Control": "no-cache",
               "Ocp-Apim-Subscription-Key": api_key}

        req = urllib.request.Request(url, headers=hdr)

        req.get_method = lambda: "GET"
        r = urllib.request.urlopen(req)
        data = json.loads(r.read().decode(
            r.info().get_param("charset") or "utf-8"))
    except Exception as e:
        print(e)

    return data


async def get_trips(where_to="home"):
    if where_to == "work":
        trips_data = (
            fetch_trips(origin="laa", destination="asdz")["trips"]
            + fetch_trips(origin="gvc", destination="asdz")["trips"]
            + fetch_trips(origin="laa", destination="asd")["trips"]
            + fetch_trips(origin="gvc", destination="asd")["trips"]
        )
    elif where_to == "home":
        trips_data = (
            fetch_trips(origin="asdz", destination="gvc")["trips"]
            + fetch_trips(origin="asdz", destination="laa")["trips"]
            + fetch_trips(origin="asd", destination="gvc")["trips"]
            + fetch_trips(origin="asd", destination="laa")["trips"]
        )
    else:
        with open("./sample_trip.json", "r") as f:
            trips_data = json.load(f)["trips"]

    trips = [Trip(t) for t in trips_data if Trip(t).transfers == 0]
    trips = sorted(trips, key=lambda t: t.departure_time)
    return trips


def get_trips_json(where_to="home", trips=None):
    if not trips:
        trips = get_trips(where_to)
    trips = [vars(t) for t in trips]
    return json.dumps(trips, indent=2, default=lambda d: d.strftime("%H:%M"))


if __name__ == "__main__":

    trips = get_trips("dev")

    for t in trips:
        print(f"{t}")

    print(get_trips_json(trips=trips))
