"""Scripting primitives for the onboarding scenes.

This module defines the 'Language' used to describe onboarding scenes
declaratively, decoupling the content from the execution logic.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Union


@dataclass
class Step:
    """Base class for all script steps."""
    pass


@dataclass
class Display(Step):
    """Display text content.
    
    Attributes:
        content: The text string or Path to a text file to display.
        clear: If True, replace existing text. If False, append to it.
        animate: If True, use typing animation (not implemented yet, reserved).
    """
    content: Union[str, Path]
    clear: bool = False
    animate: bool = True


@dataclass
class Terminal(Step):
    """Run a terminal command interactively.
    
    Attributes:
        command: The shell command to execute.
        auto_run: If True, run immediately without asking user (not standard).
    """
    command: str
    auto_run: bool = False


@dataclass
class Wait(Step):
    """Pause execution for a specific duration.
    
    Attributes:
        seconds: Time to wait in seconds.
    """
    seconds: float


@dataclass
class WaitForInput(Step):
    """Block execution until user provides input.
    
    Attributes:
        prompt: Text to show in the navigation hint area.
        key: The key to wait for (default: "enter").
    """
    prompt: str = "Press Enter ↵ to continue"
    key: str = "enter"
