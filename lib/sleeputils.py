import ctypes
import platform
import os
import sys
import time

libc = None

# Determine whether or not to use libc
os_name = platform.system()
try:
    if os_name == "Linux":
        libc = ctypes.cdll.LoadLibrary("libc.so.6")
    elif os_name == "Darwin":
        libc = ctypes.cdll.LoadLibrary("libSystem.dylib")
    else:
        raise RuntimeError("Incompatible OS")

except Exception as e:
    sys.stderr.write("Warning: failed to load libc usleep() function.\n" +
                        "Falling back to Python implementation.\n")
    sys.stderr.write(str(e) + "\n")


def precisesleep_py(seconds):
    """
    A precise version of time.sleep() implemented in pure Python.
    Should only be used as a fallback when the C version is unavailable.
    """
    dest_time = time.perf_counter() + seconds
    while time.perf_counter() < dest_time:
        pass


def precisesleep_c(seconds):
    """
    Wrapper for precise sleep function implemented in C.
    """
    microseconds = int(seconds * 1000000)
    libc.usleep(microseconds)


def precisesleep(seconds):
    if libc is None:
        precisesleep_py(seconds)
    else:
        precisesleep_c(seconds)
