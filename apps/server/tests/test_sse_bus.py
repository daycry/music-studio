"""Bus real: replay, hilos, límites y liberación sin transporte HTTP."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from app.queue.events import EventBus
from app.sse import StreamClosed, TrustedScope

SCOPE = TrustedScope(owner_id="local", job_ids=frozenset({"job"}))


def message(n=0):
    return {
        "job_id": "job",
        "type": "job.progress",
        "ts": "2026-10-08T02:00:00Z",
        "data": {"fraction": n / 1000},
    }


def test_retained_replay_and_native_handoff():
    async def run():
        bus = EventBus()
        original = message(1)
        bus.publish(original)
        original["data"]["fraction"] = 999
        cursor = bus.cursor
        barrier = Barrier(3)

        def publish(start):
            barrier.wait()
            for n in range(start, start + 20):
                bus.publish(message(n))

        with ThreadPoolExecutor(2) as pool:
            futures = [pool.submit(publish, n) for n in (2, 22)]
            barrier.wait()
            subscriber = bus.subscribe(SCOPE, cursor)
            values = [await asyncio.wait_for(subscriber.next(), 3) for _ in range(40)]
            for future in futures:
                future.result()
        assert [v.seq for v in values] == list(range(3, 43))
        replay = bus.subscribe(SCOPE, f"{bus.epoch}:1")
        records = [await replay.next() for _ in range(41)]
        assert records[0].envelope["data"]["fraction"] == 0.001
        assert len({v.seq for v in records}) == 41
        records[0].envelope["data"]["fraction"] = 7
        again = bus.subscribe(SCOPE, f"{bus.epoch}:1")
        assert (await again.next()).envelope["data"]["fraction"] == 0.001
        subscriber.close()
        replay.close()
        again.close()
        assert bus.subscriber_count == 0

    asyncio.run(run())


def test_expired_old_ahead_and_gap_are_reset_plans():
    async def run():
        bus = EventBus(2)
        cursor = bus.cursor
        for n in range(3):
            bus.publish(message(n))
        for value, reason in (
            (cursor, "expired"),
            ("0" * 32 + ":1", "epoch"),
            (f"{bus.epoch}:999", "ahead"),
        ):
            sub = bus.subscribe(SCOPE, value)
            assert sub.reset.reason == reason
            assert sub.reset.cursor == bus.cursor
            sub.close()
        sub = bus.subscribe(SCOPE, bus.cursor)
        old = bus.epoch
        bus.mark_gap()
        assert old != bus.epoch
        with pytest.raises(StreamClosed, match="gap"):
            await sub.next()
        assert bus.subscriber_count == 0

    asyncio.run(run())


def test_slow_overflow_and_cancelled_wait_unsubscribe():
    async def run():
        bus = EventBus()
        slow = bus.subscribe(SCOPE, bus.cursor)
        with ThreadPoolExecutor(1) as pool:
            future = pool.submit(lambda: [bus.publish(message(n)) for n in range(200)])
            future.result(timeout=3)
        with pytest.raises(StreamClosed, match="overflow"):
            await slow.next()
        assert bus.subscriber_count == 0
        waiting = bus.subscribe(SCOPE, bus.cursor)
        task = asyncio.create_task(waiting.next())
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert bus.subscriber_count == 0

    asyncio.run(run())


def test_native_shutdown_close_and_subscriber_bound():
    async def run():
        bus = EventBus()
        subscribers = [bus.subscribe(SCOPE, bus.cursor) for _ in range(32)]
        with pytest.raises(StreamClosed, match="limit"):
            bus.subscribe(SCOPE, bus.cursor)
        task = asyncio.create_task(subscribers[0].next())
        await asyncio.sleep(0)
        with ThreadPoolExecutor(2) as pool:
            list(
                pool.map(lambda action: action(), [bus.shutdown, subscribers[1].close])
            )
        with pytest.raises(StreamClosed, match="shutdown"):
            await task
        for sub in subscribers:
            sub.close()
        bus.shutdown()
        assert bus.subscriber_count == 0
        bus.publish(message())
        assert len(bus.buffer) == 1  # El buffer interno conserva su contrato.
        with pytest.raises(StreamClosed, match="shutdown"):
            bus.subscribe(SCOPE)

    asyncio.run(run())


def test_invalid_publication_marks_gap_preserving_legacy_history():
    async def run():
        bus = EventBus()
        for bad in (
            {**message(), "type": "job.log"},
            {**message(), "data": {"fraction": float("inf")}},
            {**message(), "ts": "not-a-date"},
            {**message(), "data": {"secret": object()}},
            {**message(), "data": {"text": "x" * 70000}},
        ):
            sub = bus.subscribe(SCOPE, bus.cursor)
            epoch = bus.epoch
            bus.publish(bad)
            assert bus.buffer[-1] is bad
            assert epoch != bus.epoch
            with pytest.raises(StreamClosed, match="gap"):
                await sub.next()
        with pytest.raises(ValueError):
            EventBus(0)
        with pytest.raises(ValueError, match="INVALID_SCOPE"):
            bus.subscribe(object())
        with pytest.raises(ValueError, match="INVALID_CURSOR"):
            bus.subscribe(SCOPE, "bad")
        bootstrap = bus.subscribe(SCOPE)
        assert bootstrap.reset.reason == "bootstrap"
        bootstrap.close()
        sub = bus.subscribe(SCOPE, bus.cursor)
        waiting = asyncio.create_task(sub.next())
        await asyncio.sleep(0)
        with pytest.raises(StreamClosed, match="concurrent_reader"):
            await sub.next()
        # Publicación async mientras un lector espera: wake, después close nativo.
        bus.publish(message())
        assert (await asyncio.wait_for(waiting, 3)).seq == 2
        waiting = asyncio.create_task(sub.next())
        await asyncio.sleep(0)
        with ThreadPoolExecutor(1) as pool:
            pool.submit(sub.close).result()
        with pytest.raises(StreamClosed, match="closed"):
            await waiting
        await asyncio.sleep(0)
        assert bus.subscriber_count == 0
        assert len(bus._notifications) == 0

    asyncio.run(run())


def test_full_retained_replay_is_separate_from_live_pending_limit():
    async def run():
        bus = EventBus()
        start = bus.cursor
        for n in range(256):
            bus.publish(message(n))
        sub = bus.subscribe(SCOPE, start)
        assert sub.reset is None
        bus.publish(message(256))
        records = [await sub.next() for _ in range(257)]
        assert [r.seq for r in records] == list(range(2, 259))
        sub.close()
        # Límite JS: nueva época, sin publicar cero ni entero inseguro.
        epoch = bus.epoch
        bus._seq = 9007199254740991
        bus.publish(message())
        assert bus.epoch != epoch
        assert bus.cursor.endswith(":2")

    asyncio.run(run())
