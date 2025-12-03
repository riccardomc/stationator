#!/usr/bin/env python3
"""NS-style SVG icons for the Stationator application."""


def ns_icon(icon_name: str, size: int = 20) -> str:
    """Return NS-style SVG icon as HTML string.
    
    Args:
        icon_name: Name of the icon (home, work, back, prev, next, refresh, menu, v1, v2, v3)
        size: Size of the icon in pixels (default: 20)
    
    Returns:
        SVG icon as HTML string
    """
    icons = {
        'home': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="#003082" xmlns="http://www.w3.org/2000/svg"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>',
        'work': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="#003082" xmlns="http://www.w3.org/2000/svg"><path d="M20 6h-4V4c0-1.11-.89-2-2-2h-4c-1.11 0-2 .89-2 2v2H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-6 0h-4V4h4v2z"/></svg>',
        'back': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="#003082" xmlns="http://www.w3.org/2000/svg"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>',
        'prev': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="#003082" xmlns="http://www.w3.org/2000/svg"><path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/></svg>',
        'next': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="#003082" xmlns="http://www.w3.org/2000/svg"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>',
        'refresh': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="#003082" xmlns="http://www.w3.org/2000/svg"><path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>',
        'menu': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="#003082" xmlns="http://www.w3.org/2000/svg"><path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>',
        'v1': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="#003082" xmlns="http://www.w3.org/2000/svg"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg>',
        'v2': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="#003082" xmlns="http://www.w3.org/2000/svg"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg>',
        'v3': f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="#003082" xmlns="http://www.w3.org/2000/svg"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg>',
    }
    return icons.get(icon_name, '')

