#!/usr/bin/env python3
"""Allow running PulseDeck as ``python -m pulsedeck``."""

import sys

import psutil

# Pre-warm psutil CPU measurement (first call always returns 0.0)
psutil.cpu_percent(interval=0)

from pulsedeck.app import PulseDeckApp


def main():
    """Entry point for the PulseDeck application."""
    app = PulseDeckApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
