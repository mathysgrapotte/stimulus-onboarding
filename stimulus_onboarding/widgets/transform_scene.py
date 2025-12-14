"""Transform scene widget for STIMULUS onboarding."""

from pathlib import Path

from textual.app import ComposeResult
from textual import events
from textual.timer import Timer
from textual.widgets import Static

from stimulus_onboarding.ui_components import (
    ActionMenu,
    fix_incomplete_markup,
    process_text_placeholders,
    stop_timer_safely,
    TerminalWidget,
    TYPING_SPEED,
    YAML_BLOCK_START,
    YAML_BLOCK_END,
)

# Load text from files
assets_dir = Path(__file__).parent / "assets"
project_root = Path(__file__).parent.parent.parent

TRANSFORM_INTRO = process_text_placeholders((assets_dir / "transform-intro.txt").read_text().strip(), project_root)
TRANSFORM_RUN = "\n\n" + process_text_placeholders((assets_dir / "transform-run.txt").read_text().strip(), project_root)

FULL_TEXT = TRANSFORM_INTRO + TRANSFORM_RUN

# Command
TRANSFORM_COMMAND = "stimulus transform --data output/vcc_split --yaml data/transform_2000.yaml --output output/vcc_2000"

# Typing speeds
YAML_TYPING_SPEED = 0.005


class TransformScene(Static):
    """Scene for transforming data."""

    can_focus = True

    def __init__(self) -> None:
        super().__init__()
        self._char_index = 0
        self._typing_timer: Timer | None = None

        # State tracking
        self._intro_done = False
        self._waiting_for_command = False
        self._completed = False
        self._terminal_shown = False
        self._in_yaml_block = False

        self._text_widget: Static
        self._command_container: Static
        self._navigation_hint: Static
        self._terminal: TerminalWidget | None = None
        
        # Pre-compute YAML block boundaries for intro text only first
        self._yaml_start_index = TRANSFORM_INTRO.find(YAML_BLOCK_START)
        self._yaml_end_index = TRANSFORM_INTRO.find(YAML_BLOCK_END)

    def compose(self) -> ComposeResult:
        """Compose the scene content."""
        yield Static("", id="transform-text")
        yield Static(id="command-container")
        yield Static("", id="navigation-hint")

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self.focus()
        self._text_widget = self.query_one("#transform-text", Static)
        self._command_container = self.query_one("#command-container", Static)
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
        # Check if we reached end of Intro
        if not self._intro_done and self._char_index >= len(TRANSFORM_INTRO):
            self._intro_done = True
            self._waiting_for_command = True
            if self._typing_timer:
                self._typing_timer.stop()

            # Show terminal with transform command
            if not self._terminal_shown:
                self._terminal_shown = True
                self._terminal = TerminalWidget(
                    prefilled_command=TRANSFORM_COMMAND,
                    auto_focus=False,
                )
                self._command_container.mount(self._terminal)

            # Mount action menu
            menu = ActionMenu()
            self._command_container.mount(menu)
            menu.focus()
            self._command_container.scroll_visible()

            self._navigation_hint.update("Select an option to continue")
            return

        # Check if we reached end of Run text
        if self._intro_done and self._char_index >= len(FULL_TEXT):
            if not self._completed:
                self._completed = True
                self._navigation_hint.update("Press Enter ↵ to continue")
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

        # Check for pause at newlines
        current_text = FULL_TEXT
        # only pause if not in yaml block
        if not self._in_yaml_block:
             if self._char_index > 0 and current_text[self._char_index - 1] == "\n":
                if self._char_index < 2 or current_text[self._char_index - 2] != "\n":
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
        text = text.replace(YAML_BLOCK_START, "").replace(YAML_BLOCK_END, "")
        return fix_incomplete_markup(text)

    def on_action_menu_action_selected(self, event: ActionMenu.ActionSelected) -> None:
        """Handle action menu selection."""
        # Remove the menu
        try:
            menu = self.query_one(ActionMenu)
            menu.remove()
        except Exception:
            pass

        if self._waiting_for_command:
            if self._terminal:
                self._terminal.disable_input()

            if event.action == "Run":
                if self._terminal:
                    self.run_worker(self._terminal.run_command(TRANSFORM_COMMAND))
            elif event.action == "Skip":
                if self._terminal:
                    self._terminal.log_widget.write("[yellow]Skipping transform...[/]")

            self._waiting_for_command = False
            self._navigation_hint.update("")
            self._resume_typing_after_pause()

    def on_unmount(self) -> None:
        """Clean up timers."""
        stop_timer_safely(self._typing_timer)

    def on_blur(self, event: events.Blur) -> None:
        """Keep focus on the widget unless terminal/menu is active."""
        if not self._terminal_shown or not self._waiting_for_command:
             self.call_after_refresh(self.focus)
