"""Typing animation utilities for text widgets."""

from textual.timer import Timer

TYPING_SPEED: float = 0.04  # seconds per character


def stop_timer_safely(timer: Timer | None) -> None:
    """Stop a timer if it exists."""
    if timer:
        timer.stop()
