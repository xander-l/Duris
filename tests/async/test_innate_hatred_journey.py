#!/usr/bin/env python3
"""The Hatred journey must reject server crashes, including during client close."""
import signal
import subprocess
import sys
import unittest
from contextlib import contextmanager
from unittest.mock import Mock

from run_innate_hatred_journey import stop


@contextmanager
def child_process(script, *, stdout=None):
    process = subprocess.Popen([sys.executable, "-c", script], stdout=stdout, text=True)
    try:
        yield process
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        if process.stdout:
            process.stdout.close()


class HatredJourneyShutdown(unittest.TestCase):
    def test_no_process(self):
        client = Mock()
        clients = [client]
        stop(None, clients)
        client.close.assert_called_once_with()
        self.assertEqual(clients, [])

    def test_clean_shutdown(self):
        script = ("import signal; "
                  "signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM}); "
                  "print('ready', flush=True); signal.sigwait({signal.SIGTERM})")
        with child_process(script, stdout=subprocess.PIPE) as process:
            self.assertEqual(process.stdout.readline(), "ready\n")
            clients = [Mock()]
            stop(process, clients)
            self.assertEqual(process.returncode, 0)
            self.assertEqual(clients, [])

    def test_already_crashed(self):
        with child_process("raise SystemExit(17)") as process:
            process.wait(timeout=5)
            with self.assertRaisesRegex(AssertionError, "status 17"):
                stop(process, [])

    def test_crash_during_client_close(self):
        with child_process("import signal; signal.pause()") as process:
            def close():
                process.kill()
                process.wait(timeout=5)

            clients = [Mock(close=close)]
            with self.assertRaisesRegex(AssertionError, f"status {-signal.SIGKILL}"):
                stop(process, clients)
            self.assertEqual(clients, [])

    def test_fixture_failure_reaps_child(self):
        with self.assertRaisesRegex(RuntimeError, "fixture failure"):
            with child_process("import signal; signal.pause()") as process:
                raise RuntimeError("fixture failure")
        self.assertEqual(process.returncode, -signal.SIGKILL)


if __name__ == "__main__":
    unittest.main()
