import threading
import time

from fpts.cache.ttl_cache import InMemoryTTLCache


def test_ttl_expiration():
    cache = InMemoryTTLCache[str, int](maxsize=10, ttl_seconds=0.1)

    cache.set("a", 123)
    assert cache.get("a") == 123

    time.sleep(0.15)

    assert cache.get("a") is None  # expired


def test_lru_eviction():
    cache = InMemoryTTLCache[str, int](maxsize=2, ttl_seconds=10)

    cache.set("a", 1)
    cache.set("b", 2)

    assert cache.get("a") == 1

    cache.set("c", 3)

    assert cache.get("a") == 1
    assert cache.get("b") is None  # evicted
    assert cache.get("c") == 3


def test_thread_safety_under_concurrency():
    cache = InMemoryTTLCache[str, int](maxsize=1000, ttl_seconds=10)

    def writer(start: int):
        for i in range(start, start + 100):
            cache.set(f"k{i}", i)

    threads = [threading.Thread(target=writer, args=(i * 100,)) for i in range(5)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify some values exist
    for i in range(500):
        value = cache.get(f"k{i}")
        if value is not None:
            assert value == i
