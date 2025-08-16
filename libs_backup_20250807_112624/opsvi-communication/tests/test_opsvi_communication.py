"""Trivial pytest stub for CI wiring."""

from opsvi_communication import __version__


def test_version() -> None:
    assert isinstance(__version__, str) and __version__
