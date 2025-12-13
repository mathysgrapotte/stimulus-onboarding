"""Case study scene widget for STIMULUS onboarding."""

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Key
from textual.timer import Timer
from textual.widgets import Static

from stimulus_onboarding.ui_components.animations import GRADIENT_COLORS, apply_gradient

# Load case study text from files
assets_dir = Path(__file__).parent / "assets"
case_study_part1_file = assets_dir / "case-study-part-1.txt"
case_study_part2_file = assets_dir / "case-study-part-2.txt"

_part1_content = case_study_part1_file.read_text().strip()
_part2_content = case_study_part2_file.read_text().strip()

# Prepend STIMULUS header to create complete text for each part
PART1_TEXT = _part1_content
PART2_TEXT = "\n\n" + _part2_content

FULL_TEXT = PART1_TEXT + PART2_TEXT
PART2_START_INDEX = len(PART1_TEXT)


class CaseStudyScene(Static):
    """Case study scene for the onboarding experience."""

    # Key bindings
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
        self._part2_done = False
        self._waiting_for_down = False
        
        # Navigation hint
        self._nav_hint_gradient_offset = 0
        self._nav_hint_animation_timer: Timer | None = None
        
        self._text_widget: Static
        self._navigation_hint: Static

    def compose(self) -> ComposeResult:
        """Compose the case study scene content."""
        yield Static("", id="case-study-text")
        yield Static("", id="navigation-hint")  # Always visible but content changes

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self.focus()
        self._text_widget = self.query_one("#case-study-text", Static)

        self._navigation_hint = self.query_one("#navigation-hint", Static)
        
        # Start typing animation
        self._typing_timer = self.set_interval(0.04, self._type_next_char)

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
            if not self._part2_done:
                self._part2_done = True
                if self._typing_timer:
                    self._typing_timer.stop()
                # Show final navigation hint
                self._navigation_hint.update("Press Enter ↵ to continue, Esc or Ctrl+C to exit")
            return

        # Type next character
        self._char_index += 1
        self._text_widget.update(self._render_text(self._char_index))

        # Check for pause at newlines
        current_text = FULL_TEXT
        if self._char_index > 0 and current_text[self._char_index - 1] == '\n':
            if self._char_index < 2 or current_text[self._char_index - 2] != '\n':
                if self._typing_timer:
                    self._typing_timer.stop()
                self.set_timer(0.8, self._resume_typing_after_pause)

    def _resume_typing_after_pause(self) -> None:
        """Resume typing after a narrative pause."""
        self._typing_timer = self.set_interval(0.04, self._type_next_char)

    def _render_text(self, length: int) -> str:
        """Render text up to length."""
        text = FULL_TEXT[:length]
        
        # Fix incomplete markup
        while text.count('[') > text.count(']'):
            last_open = text.rfind('[')
            if last_open != -1:
                text = text[:last_open]
            else:
                break
        return text

    def _animate_down_hint(self) -> None:
        """Animate the down arrow hint with a gradient."""
        self._nav_hint_gradient_offset = (self._nav_hint_gradient_offset + 1) % len(GRADIENT_COLORS)
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
        if self._typing_timer:
            self._typing_timer.stop()
        if self._nav_hint_animation_timer:
            self._nav_hint_animation_timer.stop()
