import threading


def sleep(delay):
    event = threading.Event()
    event.wait(delay)
    event.clear()
