from __future__ import annotations
import time
import heapq
import threading
from dataclasses import dataclass, field
from typing import Callable, Any, Optional, Tuple

# TODO allow scheduler to create and run independant threading workers
# TODO create function for alarm style timing (everyday at 11:00, every monday at 8 etc) 

@dataclass(order=True)
class _ScheduledItem:
    run_at: float
    seq: int
    func: Callable[..., Any] = field(compare=False)
    args: Tuple[Any, ...] = field(default_factory=tuple, compare=False)
    kwargs: dict = field(default_factory=dict, compare=False)
    interval: Optional[float] = field(default=None, compare=False)  # seconds; if set, repeats
    job_id: Optional[str] = field(default=None, compare=False)
    cancelled: bool = field(default=False, compare=False)


class Scheduler:
    def __init__(self) -> None:
        self._cv = threading.Condition()
        self._pq: list[_ScheduledItem] = []
        self._seq = 0
        self._stop = False
        self._jobs: dict[str, _ScheduledItem] = {}
        self._thread = threading.Thread(target=self._run_loop, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def shutdown(self, wait: bool = True) -> None:
        with self._cv:
            self._stop = True
            self._cv.notify_all()
        if wait:
            self._thread.join()

    def schedule_at(
        self,
        run_at_epoch: float,
        func: Callable[..., Any],
        *args: Any,
        job_id: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        return self._schedule(run_at_epoch, None, func, args, kwargs, job_id)

    def schedule_in(
        self,
        delay_s: float,
        func: Callable[..., Any],
        *args: Any,
        job_id: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        return self._schedule(time.time() + float(delay_s), None, func, args, kwargs, job_id)

    def every(
        self,
        interval_s: float,
        func: Callable[..., Any],
        *args: Any,
        job_id: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        interval_s = float(interval_s)
        return self._schedule(time.time() + interval_s, interval_s, func, args, kwargs, job_id)

    def cancel(self, job_id: str) -> bool:
        with self._cv:
            item = self._jobs.get(job_id)
            if not item:
                return False
            item.cancelled = True
            self._jobs.pop(job_id, None)
            self._cv.notify_all()
            return True

    def _schedule(
        self,
        run_at: float,
        interval: Optional[float],
        func: Callable[..., Any],
        args: Tuple[Any, ...],
        kwargs: dict,
        job_id: Optional[str],
    ) -> str:
        with self._cv:
            self._seq += 1
            jid = job_id or f"job-{self._seq}"
            item = _ScheduledItem(run_at=run_at, seq=self._seq, func=func, args=args, kwargs=kwargs, interval=interval, job_id=jid)
            heapq.heappush(self._pq, item)
            self._jobs[jid] = item
            self._cv.notify_all()
            return jid

    def _run_loop(self) -> None:
        while True:
            with self._cv:
                while not self._stop and not self._pq:
                    self._cv.wait()

                if self._stop:
                    return

                now = time.time()
                item = self._pq[0]
                wait_s = item.run_at - now
                if wait_s > 0:
                    self._cv.wait(timeout=wait_s)
                    continue

                heapq.heappop(self._pq)

                if item.cancelled:
                    continue

            # run outside lock
            try:
                item.func(*item.args, **item.kwargs)
            except Exception:
                # replace with logging if desired
                pass

            # reschedule repeating jobs
            if item.interval and not item.cancelled:
                item.run_at = time.time() + item.interval
                with self._cv:
                    heapq.heappush(self._pq, item)
                    self._cv.notify_all()
            else:
                if item.job_id:
                    with self._cv:
                        self._jobs.pop(item.job_id, None)

