#!/usr/bin/env python3
from nicegui import app


def init_storage():
    """Initialize storage for the current user."""
    if not app.storage.user.get('station_selection'):
        app.storage.user['station_selection'] = {
            "asd": False,  # Amsterdam Centraal
            "asdz": True,  # Amsterdam Zuid
            "gvc": True,  # Den Haag Centraal
            "laa": True,  # Den Haag Laan van NOI
        }