import time
import unittest

from nlb.util import timeout


class TestTimeout(unittest.TestCase):
    def test_timeout_no_exception(self):
        with timeout.timeout(seconds=0.1):
            pass  # Should complete without exception

    def test_timeout_with_exception(self):
        with self.assertRaises(timeout.TimeoutError):
            with timeout.timeout(0.001):  # Very short timeout
                time.sleep(0.01)  # Sleep longer than the timeout

    def test_timeout_nested(self):
        with self.assertRaises(timeout.TimeoutError):
            with timeout.timeout(300.0):
                with timeout.timeout(0.001):
                    time.sleep(0.01)  # Sleep longer than the inner timeout
