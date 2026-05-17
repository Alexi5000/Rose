import unittest

from ai_companion.core.exceptions import (
    SpeechToTextError,
    TextToSpeechError,
)
from ai_companion.core.retry import retry_with_exponential_backoff


class TestRetryUtilities(unittest.TestCase):
    def test_retry_succeeds_after_failures(self):
        calls = {"n": 0}

        @retry_with_exponential_backoff(max_retries=3, initial_backoff=0.0, max_backoff=0.0)
        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise Exception("boom")
            return "ok"

        result = flaky()
        self.assertEqual(result, "ok")
        self.assertEqual(calls["n"], 3)

    def test_retry_skips_on_skip_exceptions(self):
        @retry_with_exponential_backoff(
            max_retries=5, initial_backoff=0.0, max_backoff=0.0, skip_exceptions=(ValueError,)
        )
        def will_raise():
            raise ValueError("bad input")

        with self.assertRaises(ValueError):
            will_raise()

    def test_retry_raises_after_exhaustion(self):
        calls = {"n": 0}

        @retry_with_exponential_backoff(max_retries=3, initial_backoff=0.0, max_backoff=0.0)
        def always_fail():
            calls["n"] += 1
            raise RuntimeError("still failing")

        with self.assertRaises(RuntimeError):
            always_fail()
        self.assertEqual(calls["n"], 3)


class TestCustomExceptions(unittest.TestCase):
    def test_exceptions_are_subclasses(self):
        for exc in (SpeechToTextError, TextToSpeechError):
            self.assertTrue(issubclass(exc, Exception))

    def test_exception_messages(self):
        e = TextToSpeechError("failure")
        self.assertEqual(str(e), "failure")


if __name__ == "__main__":
    unittest.main()
