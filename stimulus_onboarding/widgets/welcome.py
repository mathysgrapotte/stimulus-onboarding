"""Welcome scene widget for STIMULUS onboarding."""

from pathlib import Path

from textual.app import ComposeResult
from textual.timer import Timer
from textual.widgets import Static

from stimulus_onboarding.ui_components import (
    GRADIENT_COLORS,
    apply_gradient,
    cycle_gradient_offset,
    fix_incomplete_markup,
    stop_timer_safely,
    TYPING_SPEED,
)

# Load welcome text from file
assets_dir = Path(__file__).parent / "assets"
welcome_file = assets_dir / "welcome.txt"
_welcome_content = welcome_file.read_text().strip()

# Prepend STIMULUS header to create complete intro text
INTRO_TEXT = "Welcome to STIMULUS\n\n" + _welcome_content

# Navigation hint text (plain text to avoid markup parsing issues during animation)
NAV_HINT_TEXT = "Press Enter ↵ to continue, Esc or Ctrl+C to exit"

# Position of STIMULUS in the intro text for gradient animation
STIMULUS_START = len("Welcome to ")
STIMULUS_END = STIMULUS_START + len("STIMULUS")






class WelcomeScene(Static):
    """Welcome banner scene for the onboarding experience."""

    def __init__(self) -> None:
        super().__init__()
        self._char_index = 0
        self._gradient_offset = 0
        self._typing_done = False
        self._paused = False
        self._typing_timer: Timer | None = None
        self._nav_hint_char_index = 0
        self._nav_hint_typing_timer: Timer | None = None
        self._welcome_text: Static
        self._navigation_hint: Static

    def compose(self) -> ComposeResult:
        """Compose the welcome scene content."""
        yield Static("", id="welcome-text")
        yield Static("", id="navigation-hint", classes="hidden")

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self._welcome_text = self.query_one("#welcome-text", Static)
        self._navigation_hint = self.query_one("#navigation-hint", Static)
        # Start typing animation at 0.08s per character (slower)
        self._typing_timer = self.set_interval(0.08, self._type_next_char)

    def _render_text(self, length: int) -> str:
        """Render text up to length with gradient applied to STIMULUS."""
        text = fix_incomplete_markup(INTRO_TEXT[:length])

        # Before STIMULUS - return as-is
        if length <= STIMULUS_START:
            return text

        # Split text into: prefix + STIMULUS (with gradient) + suffix
        prefix = text[:STIMULUS_START]

        # Calculate how much of STIMULUS to show
        highlight_len = min(length, STIMULUS_END) - STIMULUS_START
        highlight = apply_gradient("STIMULUS"[:highlight_len], self._gradient_offset)

        # Add suffix if we're past STIMULUS
        if length > STIMULUS_END:
            suffix = text[STIMULUS_END:]
            return prefix + highlight + suffix

        return prefix + highlight

    def _type_next_char(self) -> None:
        """Type one character at a time."""
        # Check if we've reached the end
        if self._char_index >= len(INTRO_TEXT):
            if not self._typing_done:
                self._typing_done = True
                # Stop typing timer
                if self._typing_timer:
                    self._typing_timer.stop()
                # Show navigation hint after 0.5s
                self.set_timer(0.5, self._show_navigation_hint)
            return

        # Check if we've reached end of STIMULUS - pause for gradient
        if self._char_index == STIMULUS_END and not self._paused:
            self._paused = True
            if self._typing_timer:
                self._typing_timer.stop()
            # Start gradient animation at 0.08s per frame
            self.set_interval(0.08, self._animate_gradient)
            # Resume typing after 1.4s
            self.set_timer(1.4, self._resume_typing)
            return

        # Type next character
        self._char_index += 1
        self._welcome_text.update(self._render_text(self._char_index))

        # Check if we just typed a newline (end of line pause)
        if self._char_index > 0 and INTRO_TEXT[self._char_index - 1] == '\n':
            # Only pause if the previous character wasn't also a newline
            # (avoids multiple pauses for blank lines)
            if self._char_index < 2 or INTRO_TEXT[self._char_index - 2] != '\n':
                if self._typing_timer:
                    self._typing_timer.stop()
                # Longer pause at end of each line
                self.set_timer(0.8, self._resume_typing_after_pause)

    def _animate_gradient(self) -> None:
        """Cycle gradient colors on STIMULUS."""
        self._gradient_offset = cycle_gradient_offset(self._gradient_offset)
        self._welcome_text.update(self._render_text(self._char_index))

    def _resume_typing(self) -> None:
        """Resume typing after gradient pause."""
        self._typing_timer = self.set_interval(TYPING_SPEED, self._type_next_char)

    def _resume_typing_after_pause(self) -> None:
        """Resume typing after a regular narrative pause."""
        self._typing_timer = self.set_interval(TYPING_SPEED, self._type_next_char)

    def _show_navigation_hint(self) -> None:
        """Show and animate the navigation hint."""
        # Make widget visible
        self._navigation_hint.remove_class("hidden")
        # Start typing animation for hint at 0.03s per character
        self._nav_hint_typing_timer = self.set_interval(0.03, self._type_nav_hint_char)

    def _type_nav_hint_char(self) -> None:
        """Type navigation hint one character at a time."""
        if self._nav_hint_char_index >= len(NAV_HINT_TEXT):
            # Stop timer when done
            if self._nav_hint_typing_timer:
                self._nav_hint_typing_timer.stop()
            return

        self._nav_hint_char_index += 1
        self._navigation_hint.update(NAV_HINT_TEXT[: self._nav_hint_char_index])

    def on_unmount(self) -> None:
        """Clean up timers when widget is unmounted."""
        stop_timer_safely(self._typing_timer)
        stop_timer_safely(self._nav_hint_typing_timer)
