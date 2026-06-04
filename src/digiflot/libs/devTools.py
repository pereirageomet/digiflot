""" Development tools and functions
"""

from functools import wraps
import time
import logging
logger = logging.getLogger(__name__)


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.perf_counter() - start:.6f}s")
        return result
    return wrapper



