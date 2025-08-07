"""Trivial pytest stub for CI wiring."""

from opsvi_memory import __version__


def test_version() -> None:
    assert isinstance(__version__, str) and __version__
