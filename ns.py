#!/usr/bin/env python

import os
import json
import itertools
import dateutil.parser
import dateutil.tz
import requests
from datetime import datetime, timedelta


class Station(super):

    def __init__(self, station_data):
        self.full_name = station_data["full_name"]
        self.short_name = station_data["short_name"]
        d = datetime.strptime(station_data["biking_time"], "%H:%M")
        d = timedelta(hours=d.hour, minutes=d.minute, seconds=d.second)
        self.biking_time = d


stations = {
    "asd": Station(
        {
            "full_name": "Amsterdam Centraal",
            "short_name": "asd",
            "biking_time": "00:10",
        }
    ),
    "asdz": Station(
        {
            "full_name": "Amsterdam Zuid",
            "short_name": "asdz",
            "biking_time": "00:14",
        }
    ),
    "gvc": Station(
        {
            "full_name": "Den Haag Centraal",
            "short_name": "gvc",
            "biking_time": "00:11",
        }
    ),
    "laa": Station(
        {
            "full_name": "Den Haag Laan van NOI",
            "short_name": "laa",
            "biking_time": "00:14",
        }
    ),
}


class Trip(super):

    def __init__(self, trip_data):

        self.trip_data = trip_data
        self.leg = self._leg()

        self.status = trip_data["status"]
        self.transfers = trip_data["transfers"]

        o = self.leg.get("origin", {})
        self.origin = o["stationCode"].lower()
        self.departure_track = o["plannedTrack"]
        self.departure_time = dateutil.parser.isoparse(o["plannedDateTime"])

        d = self.leg.get("destination", {})
        self.destination = d["stationCode"].lower()
        self.arrival_time = dateutil.parser.isoparse(d["plannedDateTime"])
        self.arrival_track = d["plannedTrack"]

        self.leave_by = self._leave_by()
        self.arrive_by = self._arrive_by()
        # self.biking_time = self._biking_time()

    def _leg(self):
        legs = self.trip_data.get("legs", [])

        if legs:
            return legs[0]

        return {}

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


def get_amsterdam_time(delta=0):
    return datetime.now(dateutil.tz.gettz("Europe/Amsterdam")) + timedelta(hours=delta)


def fetch_trips(origin="laa", destination="asdz", date_time=None):
    url = "https://gateway.apiportal.ns.nl/reisinformatie-api/api/v3/trips"
    api_key = os.getenv("NS_API_KEY")

    if not date_time:
        date_time = get_amsterdam_time()

    params = {
        "fromStation": origin,
        "toStation": destination,
        "dateTime": date_time.strftime("%Y-%m-%dT%H:%M"),
    }

    headers = {
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": api_key,
    }

    try:
        r = requests.get(url, params=params, headers=headers)
        data = r.json()
    except Exception as e:
        print(e)

    return data


def get_trips(where_to="home", date_time=None):

    if where_to == "work":
        stations = [("laa", "asdz"), ("gvc", "asdz"),
                    ("laa", "asd"), ("gvc", "asd")]
        trips_data = itertools.chain.from_iterable(
            ([fetch_trips(o, d, date_time)["trips"] for o, d in stations])
        )
    elif where_to == "home":
        stations = [("asdz", "laa"), ("asdz", "gvc"),
                    ("asd", "laa"), ("asd", "gvc")]
        trips_data = itertools.chain.from_iterable(
            ([fetch_trips(o, d, date_time)["trips"] for o, d in stations])
        )
    else:
        with open("./sample_trip.json", "r") as f:
            trips_data = json.load(f)["trips"]

    trips = [Trip(t) for t in trips_data if Trip(t).transfers == 0]
    trips = sorted(trips, key=lambda t: t.departure_time)
    return trips
