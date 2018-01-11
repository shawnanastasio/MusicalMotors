import time

def precisesleep(seconds):
    """
    A precise version of time.sleep() implemented in pure Python.
    """
    dest_time = time.perf_counter() + seconds
    while time.perf_counter() < dest_time:
        time.sleep(0.00001)
