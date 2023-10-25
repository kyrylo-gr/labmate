"""Async utilities."""
import threading


def sleep(delay):
    """Async sleep. Uses wait from threading.Event."""
    event = threading.Event()
    event.wait(delay)
    event.clear()
