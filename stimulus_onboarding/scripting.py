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
    """Display text content immediately.
    
    Attributes:
        content: The text string or Path to a text file to display.
        clear: If True, replace existing text. If False, append to it.
    """
    content: Union[str, Path]
    clear: bool = False


@dataclass
class DisplayYaml(Step):
    """Display YAML content with formatting.
    
    Attributes:
        content: The YAML string or Path to a YAML file.
    """
    content: Union[str, Path]


@dataclass
class DisplayPython(Step):
    """Display Python content with syntax highlighting.
    
    Attributes:
        content: The Python code string or Path to a Python file.
    """
    content: Union[str, Path]


@dataclass
class Type(Step):
    """Type text content character by character.
    
    Attributes:
        content: The text string or Path to a text file to display.
        speed: Seconds per character.
    """
    content: Union[str, Path]
    speed: float = 0.05


@dataclass
class Gradient(Step):
    """Display text with a cycling gradient animation.
    
    Attributes:
        content: The text string to display.
    """
    content: str


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
