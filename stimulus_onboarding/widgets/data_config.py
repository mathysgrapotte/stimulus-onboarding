"""Data configuration scene widget for STIMULUS onboarding."""

import re
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual import events
from textual.timer import Timer
from textual.widgets import Static

from stimulus_onboarding.ui_components import (
    YAML_BLOCK_END,
    YAML_BLOCK_START,
    apply_gradient,
    cycle_gradient_offset,
    fix_incomplete_markup,
    process_text_placeholders,
    stop_timer_safely,
    TYPING_SPEED,
)

# Base paths
assets_dir = Path(__file__).parent / "assets"
project_root = Path(__file__).parent.parent.parent

# Typing speeds
YAML_TYPING_SPEED = 0.005  # Much faster for YAML blocks





# Load and process text files
data_config_part1_file = assets_dir / "data-config-part-1.txt"
data_config_part2_file = assets_dir / "data-config-part-2.txt"

PART1_TEXT = data_config_part1_file.read_text().strip()
_part2_raw = data_config_part2_file.read_text().strip()
PART2_TEXT = "\n\n" + process_text_placeholders(_part2_raw, project_root)

FULL_TEXT = PART1_TEXT + PART2_TEXT


class DataConfigScene(Static):
    """Data configuration scene for the onboarding experience."""

    BINDINGS = [
        Binding("down", "next_part", "Next Part", show=False),
    ]

    can_focus = True

    def __init__(self) -> None:
        super().__init__()
        self._char_index = 0
        self._typing_timer: Timer | None = None

        # State tracking
        self._part1_done = False
        self._waiting_for_down = False
        self._completed = False
        self._in_yaml_block = False

        # Navigation hint
        self._nav_hint_gradient_offset = 0
        self._nav_hint_animation_timer: Timer | None = None

        self._text_widget: Static
        self._navigation_hint: Static

        # Pre-compute YAML block boundaries
        self._yaml_start_index = FULL_TEXT.find(YAML_BLOCK_START)
        self._yaml_end_index = FULL_TEXT.find(YAML_BLOCK_END)

    def compose(self) -> ComposeResult:
        """Compose the data config scene content."""
        yield Static("", id="data-config-text")
        yield Static("", id="navigation-hint")

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self.focus()
        self._text_widget = self.query_one("#data-config-text", Static)
        self._navigation_hint = self.query_one("#navigation-hint", Static)

        # Start typing animation
        self._typing_timer = self.set_interval(TYPING_SPEED, self._type_next_char)

    def _is_in_yaml_block(self) -> bool:
        """Check if current position is inside a YAML block."""
        if self._yaml_start_index == -1:
            return False
        return self._yaml_start_index < self._char_index < self._yaml_end_index

    def _type_next_char(self) -> None:
        """Type one character at a time."""
        # Check if we reached end of Part 1
        if not self._part1_done and self._char_index >= len(PART1_TEXT):
            self._part1_done = True
            self._waiting_for_down = True
            if self._typing_timer:
                self._typing_timer.stop()

            # Start animating the down arrow hint
            self._nav_hint_animation_timer = self.set_interval(0.08, self._animate_down_hint)
            return

        # Check if we reached end of Part 2
        if self._part1_done and self._char_index >= len(FULL_TEXT):
            if not self._completed:
                self._completed = True
                self._navigation_hint.update("Press Enter ↵ to continue to next step")
                if self._typing_timer:
                    self._typing_timer.stop()
            return

        # Type next character
        self._char_index += 1
        self._text_widget.update(self._render_text(self._char_index))

        # Check if we need to switch typing speed for YAML block
        was_in_yaml = self._in_yaml_block
        self._in_yaml_block = self._is_in_yaml_block()

        if was_in_yaml != self._in_yaml_block:
            # Speed changed, restart timer with new speed
            if self._typing_timer:
                self._typing_timer.stop()
            speed = YAML_TYPING_SPEED if self._in_yaml_block else TYPING_SPEED
            self._typing_timer = self.set_interval(speed, self._type_next_char)
            return

        # Check for pause at newlines (only outside YAML blocks)
        if not self._in_yaml_block:
            if self._char_index > 0 and FULL_TEXT[self._char_index - 1] == '\n':
                if self._char_index < 2 or FULL_TEXT[self._char_index - 2] != '\n':
                    if self._typing_timer:
                        self._typing_timer.stop()
                    self.set_timer(0.8, self._resume_typing_after_pause)

    def _resume_typing_after_pause(self) -> None:
        """Resume typing after a narrative pause."""
        speed = YAML_TYPING_SPEED if self._in_yaml_block else TYPING_SPEED
        self._typing_timer = self.set_interval(speed, self._type_next_char)

    def _render_text(self, length: int) -> str:
        """Render text up to length, stripping markers."""
        text = FULL_TEXT[:length]
        # Remove markers from rendered text
        text = text.replace(YAML_BLOCK_START, "").replace(YAML_BLOCK_END, "")
        return fix_incomplete_markup(text)

    def _animate_down_hint(self) -> None:
        """Animate the down arrow hint with a gradient."""
        self._nav_hint_gradient_offset = cycle_gradient_offset(self._nav_hint_gradient_offset)
        arrow = apply_gradient("↓", self._nav_hint_gradient_offset)
        self._navigation_hint.update(f"press {arrow} to continue")

    def action_next_part(self) -> None:
        """Handle down arrow press."""
        if self._waiting_for_down:
            self._waiting_for_down = False
            # Stop hint animation and clear it
            if self._nav_hint_animation_timer:
                self._nav_hint_animation_timer.stop()
            self._navigation_hint.update("")

            # Resume typing for Part 2
            self._resume_typing_after_pause()

    def on_unmount(self) -> None:
        """Clean up timers."""
        stop_timer_safely(self._typing_timer)
        stop_timer_safely(self._nav_hint_animation_timer)

    def on_blur(self, event: events.Blur) -> None:
        """Keep focus on the widget."""
        self.call_after_refresh(self.focus)
