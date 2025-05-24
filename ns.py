#!/usr/bin/env python

import os
import json
import itertools
import dateutil.parser
import dateutil.tz
import requests
import logging
from datetime import datetime, timedelta
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class Station(super):

    def __init__(self, station_data):
        self.full_name = station_data["full_name"]
        self.short_name = station_data["short_name"]
        d = datetime.strptime(station_data["biking_time"], "%H:%M")
        d = timedelta(hours=d.hour, minutes=d.minute)
        self.biking_time = d


stations = {
    "asd": Station(
        {
            "full_name": "Amsterdam Centraal",
            "short_name": "asd",
            "biking_time": "00:21",
        }
    ),
    "asdz": Station(
        {
            "full_name": "Amsterdam Zuid",
            "short_name": "asdz",
            "biking_time": "00:06",
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
        self.departure_track = o.get(
            "actualTrack", o.get("plannedTrack", None))
        departure_time = o.get(
            "actualDateTime", o.get("plannedDateTime", None))
        self.departure_time = dateutil.parser.isoparse(departure_time)
        self.direction = self.leg.get("direction", None)

        d = self.leg.get("destination", {})
        self.destination = d["stationCode"].lower()
        self.arrival_track = d.get("actualTrack", d.get("plannedTrack", None))
        arrival_time = d.get("actualDateTime", d.get("plannedDateTime", None))
        self.arrival_time = dateutil.parser.isoparse(arrival_time)

        self.leave_by = self._leave_by()
        self.arrive_by = self._arrive_by()
        self.biking_time = self._biking_time()
        self.train_time = self._train_time()
        self.travel_time = self.biking_time + self.train_time

    def _leg(self):
        legs = self.trip_data.get("legs", [])

        if legs:
            return legs[0]

        return {}

    def _leave_by(self):
        origin_station = stations.get(self.origin, None)
        biking_time = origin_station.biking_time if origin_station else timedelta(0)
        return self.departure_time - biking_time

    def _arrive_by(self):
        destination_station = stations.get(self.destination, None)
        biking_time = destination_station.biking_time if destination_station else timedelta(0)
        return self.arrival_time + biking_time

    def _biking_time(self):
        origin_station = stations.get(self.origin, None)
        destination_station = stations.get(self.destination, None)
        if destination_station and origin_station:
            return destination_station.biking_time + origin_station.biking_time
        elif origin_station:
            return origin_station.biking_time
        elif destination_station:
            return destination_station.biking_time

        return timedelta(0)

    def _train_time(self):
        departure_delta = timedelta(
            hours=self.departure_time.hour,
            minutes=self.departure_time.minute
        )
        return self.arrival_time - departure_delta

    def __str__(self):
        return f"""{
            self.departure_time.strftime("%H:%M")}, {
            self.arrival_time.strftime("%H:%M")}, {
            self.origin}, {
            self.destination}, {
            self.transfers}, {
            self.status}, {
            self.leave_by.strftime("%H:%M")}, {
            self.arrive_by.strftime("%H:%M")}, {
            self.biking_time.strftime("%H:%M")}, {
            self.train_time.strftime("%H:%M")}, {
            self.travel_time.strftime("%H:%M")},
        """

    def json(self):
        return json.dumps(vars(self), default=str, sort_keys=True, indent=2)


def get_amsterdam_time(hour=-1, round_to_hour=True):
    dt = datetime.now(dateutil.tz.gettz("Europe/Amsterdam"))

    if hour >= 0 and hour < 24:
        dt = dt.replace(hour=hour)

    if round_to_hour:
        dt = dt.replace(minute=0, second=0, microsecond=0)

    return dt


@lru_cache
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
        "Ocp-Apim-Subscription-Key": api_key,
    }

    logger.info(f"Fetching trips from {origin} to {destination} at {date_time}")
    data = {}
    try:
        r = requests.get(url, params=params, headers=headers)
        if r.status_code != 200:
            logger.error(f"Failed to fetch trips: {r.status_code} {r.reason}")
            raise Exception(r.status_code, r.reason, r.json())
        data = r.json()
        logger.info(f"Successfully fetched {len(data.get('trips', []))} trips")
    except Exception as e:
        logger.error(f"Exception while fetching trips: {e}")

    return data


def get_trips(where_to="home", date_time=None):
    ams_time = get_amsterdam_time(round_to_hour=False)
    logger.info(f"Getting trips to {where_to}")
    
    if where_to == "work":
        stations = [("laa", "asdz"), ("gvc", "asdz")]
        trips_data = itertools.chain.from_iterable(
            ([fetch_trips(o, d, date_time)["trips"] for o, d in stations])
        )
    elif where_to == "home":
        stations = [("asdz", "laa"), ("asdz", "gvc")]
        trips_data = itertools.chain.from_iterable(
            ([fetch_trips(o, d, date_time)["trips"] for o, d in stations])
        )
    else:
        logger.info("Using sample trip data")
        with open("./sample_trip.json", "r") as f:
            trips_data = json.load(f)["trips"]

    trips = [Trip(t) for t in trips_data if Trip(t).transfers == 0]
    trips = sorted(trips, key=lambda t: t.departure_time)
    logger.info(f"Found {len(trips)} direct trips to {where_to}")
    return trips
