#!/usr/bin/env python3
"""PulseDeck - Lightweight System Monitor & Assistant for Linux.

Launch with: python3 main.py
"""
import sys
import os

# Ensure the project root is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Pre-warm psutil CPU measurement (first call always returns 0)
import psutil
psutil.cpu_percent(interval=0)

from pulsedeck.app import PulseDeckApp


def main():
    app = PulseDeckApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
