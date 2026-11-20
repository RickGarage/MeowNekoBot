import threading
import time
from typing import Callable, Optional, Any, Tuple, Dict


class BackgroundTask:
    """
    A generic background task runner that executes a given function
    either once or repeatedly at a specified interval, without blocking
    the main thread.

    Example usage:
        def my_task(name, value):
            print(f"Hello {name}, value={value}")

        # Run once
        task = BackgroundTask(my_task, args=("Alice",), kwargs={"value": 42})
        task.start()
        # ... do other things ...
        task.stop()  # if needed

        # Run every 5 seconds
        task = BackgroundTask(my_task, args=("Bob",), kwargs={"value": 99},
                              interval=5.0)
        task.start()
        # ... do other things ...
        task.stop()
    """

    def __init__(
        self,
        func: Callable[..., Any],
        args: Tuple[Any, ...] = (),
        kwargs: Optional[Dict[str, Any]] = None,
        interval: Optional[float] = None,
        daemon: bool = True
    ) -> None:
        """
        Initialize the background task.

        :param func: The function to execute.
        :param args: Positional arguments to pass to `func`.
        :param kwargs: Keyword arguments to pass to `func`.
        :param interval: If `None`, the function runs only once.
                         Otherwise, it runs repeatedly every `interval` seconds.
        :param daemon: Whether the internal thread should be a daemon.
                       Daemon threads exit when the main program ends.
        """
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.interval = interval
        self.daemon = daemon

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self) -> None:
        """Start the background task. Does nothing if already running."""
        if self._running or (self._thread and self._thread.is_alive()):
            return
        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=self.daemon)
        self._thread.start()

    def stop(self, timeout: Optional[float] = None) -> None:
        """
        Stop the background task (if running). Blocks until the thread finishes.

        :param timeout: Maximum time (seconds) to wait for the thread to finish.
                        If `None`, wait indefinitely.
        """
        self._stop_event.set()
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)

    def is_running(self) -> bool:
        """Return `True` if the task is currently running."""
        return self._running and self._thread and self._thread.is_alive()

    def _run(self) -> None:
        """Internal loop that executes the user function."""
        try:
            if self.interval is None:
                # Run once
                if not self._stop_event.is_set():
                    self.func(*self.args, **self.kwargs)
            else:
                # Run repeatedly
                while not self._stop_event.is_set():
                    self.func(*self.args, **self.kwargs)
                    # Wait for the interval or until stop signal is set
                    self._stop_event.wait(timeout=self.interval)
        except Exception as e:
            # You can replace this with proper logging if needed
            print(f"BackgroundTask error: {e}")
        finally:
            self._running = False