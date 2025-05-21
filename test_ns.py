import unittest
from datetime import datetime, timedelta
import json
import gzip
from unittest.mock import patch
from ns import get_trips, get_amsterdam_time, Trip

class TestGetTrips(unittest.TestCase):
    def setUp(self):
        # Load sample data from gzipped file
        with gzip.open("sample-trips.json.gz", "rt", encoding="utf-8") as f:
            self.sample_data = json.load(f)

    @patch('ns.fetch_trips')
    def test_get_trips_home(self, mock_fetch_trips):
        # Mock the fetch_trips function to return appropriate sample data
        def mock_fetch(origin, destination, date_time=None):
            key = f"{origin}-{destination}"
            return self.sample_data.get(key, {"trips": []})
        mock_fetch_trips.side_effect = mock_fetch
        
        # Test getting trips to home
        trips = get_trips(where_to="home")
        self.assertIsInstance(trips, list)
        for trip in trips:
            self.assertEqual(trip.transfers, 0)
            self.assertIn(trip.origin, ["asdz"])
            self.assertIn(trip.destination, ["laa", "gvc"])

    @patch('ns.fetch_trips')
    def test_get_trips_work(self, mock_fetch_trips):
        # Mock the fetch_trips function to return appropriate sample data
        def mock_fetch(origin, destination, date_time=None):
            key = f"{origin}-{destination}"
            return self.sample_data.get(key, {"trips": []})
        mock_fetch_trips.side_effect = mock_fetch
        
        # Test getting trips to work
        trips = get_trips(where_to="work")
        self.assertIsInstance(trips, list)
        for trip in trips:
            self.assertEqual(trip.transfers, 0)
            self.assertIn(trip.origin, ["laa", "gvc"])
            self.assertIn(trip.destination, ["asdz"])

    @patch('ns.fetch_trips')
    def test_get_trips_with_datetime(self, mock_fetch_trips):
        # Mock the fetch_trips function to return appropriate sample data
        def mock_fetch(origin, destination, date_time=None):
            key = f"{origin}-{destination}"
            return self.sample_data.get(key, {"trips": []})
        mock_fetch_trips.side_effect = mock_fetch
        
        # Test getting trips with a specific datetime
        test_time = get_amsterdam_time() + timedelta(hours=1)
        trips = get_trips(where_to="home", date_time=test_time)
        self.assertIsInstance(trips, list)
        for trip in trips:
            self.assertEqual(trip.transfers, 0)
            self.assertIn(trip.origin, ["asdz"])
            self.assertIn(trip.destination, ["laa", "gvc"])

    def test_get_trips_other_destination(self):
        # Test getting trips with a non-standard destination
        trips = get_trips(where_to="other")
        self.assertIsInstance(trips, list)
        # Should use sample data from sample_trip.json
        self.assertTrue(len(trips) > 0)
        for trip in trips:
            self.assertEqual(trip.transfers, 0)

    @patch('ns.fetch_trips')
    def test_trips_sorted_by_departure(self, mock_fetch_trips):
        # Mock the fetch_trips function to return appropriate sample data
        def mock_fetch(origin, destination, date_time=None):
            key = f"{origin}-{destination}"
            return self.sample_data.get(key, {"trips": []})
        mock_fetch_trips.side_effect = mock_fetch
        
        # Test that trips are sorted by departure time
        trips = get_trips(where_to="home")
        for i in range(len(trips) - 1):
            self.assertLessEqual(trips[i].departure_time, trips[i + 1].departure_time)

if __name__ == '__main__':
    unittest.main() 