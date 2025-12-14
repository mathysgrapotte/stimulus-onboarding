"""Data configuration scene widget for STIMULUS onboarding."""

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
    stop_timer_safely,
)

# Base paths
assets_dir = Path(__file__).parent / "assets"
project_root = Path(__file__).parent.parent.parent

# Load and process text files
from stimulus_onboarding.ui_components import process_text_placeholders

data_config_part1_file = assets_dir / "data-config-part-1.txt"
data_config_part2_file = assets_dir / "data-config-part-2.txt"

PART1_TEXT = data_config_part1_file.read_text().strip()
_part2_raw = data_config_part2_file.read_text().strip()
PART2_TEXT = "\n\n" + process_text_placeholders(_part2_raw, project_root)

FULL_TEXT = PART1_TEXT + PART2_TEXT


def _strip_yaml_markers(text: str) -> str:
    """Remove YAML block markers from text."""
    return text.replace(YAML_BLOCK_START, "").replace(YAML_BLOCK_END, "")


class DataConfigScene(Static):
    """Data configuration scene for the onboarding experience."""

    BINDINGS = [
        Binding("down", "next_part", "Next Part", show=False),
    ]

    can_focus = True

    def __init__(self) -> None:
        super().__init__()
        self._current_part = 0
        self._nav_hint_gradient_offset = 0
        self._nav_hint_animation_timer: Timer | None = None
        self._text_widget: Static
        self._navigation_hint: Static

    def compose(self) -> ComposeResult:
        """Compose the data config scene content."""
        yield Static("", id="data-config-text")
        yield Static("", id="navigation-hint")

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self.focus()
        self._text_widget = self.query_one("#data-config-text", Static)
        self._navigation_hint = self.query_one("#navigation-hint", Static)
        self._show_part(0)

    def _show_part(self, part: int) -> None:
        """Display text for given part immediately."""
        match part:
            case 0:
                text = _strip_yaml_markers(PART1_TEXT)
                self._text_widget.update(text)
                self._start_hint_animation()
            case 1:
                text = _strip_yaml_markers(FULL_TEXT)
                self._text_widget.update(text)
                self._navigation_hint.update("Press Enter ↵ to continue to next step")

    def _start_hint_animation(self) -> None:
        """Start animated gradient hint for down arrow."""
        self._nav_hint_animation_timer = self.set_interval(0.08, self._animate_down_hint)

    def _animate_down_hint(self) -> None:
        """Animate the down arrow hint with a gradient."""
        self._nav_hint_gradient_offset = cycle_gradient_offset(self._nav_hint_gradient_offset)
        arrow = apply_gradient("↓", self._nav_hint_gradient_offset)
        self._navigation_hint.update(f"press {arrow} to continue")

    def action_next_part(self) -> None:
        """Handle down arrow press."""
        if self._current_part >= 1:
            return

        stop_timer_safely(self._nav_hint_animation_timer)
        self._nav_hint_animation_timer = None
        self._current_part = 1
        self._show_part(1)

    def on_unmount(self) -> None:
        """Clean up timers."""
        stop_timer_safely(self._nav_hint_animation_timer)

    def on_blur(self, event: events.Blur) -> None:
        """Keep focus on the widget."""
        self.call_after_refresh(self.focus)
