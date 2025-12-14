"""Stimulus run scene widget for STIMULUS onboarding."""

from enum import StrEnum, auto
from pathlib import Path

from textual.app import ComposeResult
from textual import events
from textual.widgets import Static

from stimulus_onboarding.ui_components import (
    ActionMenu,
    fix_incomplete_markup,
    process_text_placeholders,
    TerminalWidget,
)

project_root = Path(__file__).parent.parent.parent

# Load text from files
assets_dir = Path(__file__).parent / "assets"

_part1_content = process_text_placeholders(
    (assets_dir / "stimulus-run-part-1.txt").read_text().strip(), project_root
)
_part2_content = process_text_placeholders(
    (assets_dir / "stimulus-run-part-2.txt").read_text().strip(), project_root
)
_part3_content = process_text_placeholders(
    (assets_dir / "stimulus-run-part-3.txt").read_text().strip(), project_root
)
_part4_content = process_text_placeholders(
    (assets_dir / "stimulus-run-part-4.txt").read_text().strip(), project_root
)
_part5_content = process_text_placeholders(
    (assets_dir / "stimulus-run-part-5.txt").read_text().strip(), project_root
)

PART1_TEXT = _part1_content
PART2_TEXT = PART1_TEXT + "\n\n" + _part2_content
PART3_TEXT = PART2_TEXT + "\n\n" + _part3_content
PART4_TEXT = PART3_TEXT + "\n\n" + _part4_content
PART5_TEXT = PART4_TEXT + "\n\n" + _part5_content

# Commands
INSTALL_COMMAND = "uv pip install git+https://github.com/mathysgrapotte/stimulus-py.git@h5ad-support"
SPLIT_COMMAND = "stimulus split --data data/vcc_training_subset.h5ad --yaml data/split.yaml --output output/vcc_split"
LS_COMMAND = "ls -lh output/vcc_split"
ANALYSIS_COMMAND = "uv run stimulus_onboarding/case_study_analysis/analyze_splits.py"


class RunState(StrEnum):
    """State machine for the stimulus run scene."""

    PART1 = auto()
    WAIT_INSTALL = auto()
    PART2 = auto()
    WAIT_SPLIT = auto()
    PART3 = auto()
    WAIT_LS = auto()
    PART4 = auto()
    WAIT_ANALYSIS = auto()
    PART5 = auto()
    COMPLETE = auto()


# State configuration: maps state to (text_to_display, command_or_none, next_state)
STATE_CONFIG: dict[RunState, tuple[str, str | None, RunState | None]] = {
    RunState.PART1: (PART1_TEXT, None, RunState.WAIT_INSTALL),
    RunState.WAIT_INSTALL: (PART1_TEXT, INSTALL_COMMAND, RunState.PART2),
    RunState.PART2: (PART2_TEXT, None, RunState.WAIT_SPLIT),
    RunState.WAIT_SPLIT: (PART2_TEXT, SPLIT_COMMAND, RunState.PART3),
    RunState.PART3: (PART3_TEXT, None, RunState.WAIT_LS),
    RunState.WAIT_LS: (PART3_TEXT, LS_COMMAND, RunState.PART4),
    RunState.PART4: (PART4_TEXT, None, RunState.WAIT_ANALYSIS),
    RunState.WAIT_ANALYSIS: (PART4_TEXT, ANALYSIS_COMMAND, RunState.PART5),
    RunState.PART5: (PART5_TEXT, None, RunState.COMPLETE),
    RunState.COMPLETE: (PART5_TEXT, None, None),
}


class StimulusRunScene(Static):
    """Scene for installing and running STIMULUS."""

    can_focus = True

    def __init__(self) -> None:
        super().__init__()
        self._state = RunState.PART1
        self._text_widget: Static
        self._navigation_hint: Static
        self._command_container: Static
        self._terminal: TerminalWidget | None = None

    def compose(self) -> ComposeResult:
        """Compose the scene content."""
        yield Static("", id="stimulus-run-text")
        yield Static(id="command-container")
        yield Static("", id="navigation-hint")

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self.focus()
        self._text_widget = self.query_one("#stimulus-run-text", Static)
        self._command_container = self.query_one("#command-container", Static)
        self._navigation_hint = self.query_one("#navigation-hint", Static)
        self._show_state()

    def _show_state(self) -> None:
        """Display current state's text and UI elements."""
        text, command, _ = STATE_CONFIG[self._state]
        self._text_widget.update(fix_incomplete_markup(text))

        # Handle states with commands (WAIT_* states)
        if command is not None:
            self._setup_terminal_for_command(command)
            return

        # Handle completion state
        if self._state == RunState.COMPLETE:
            self._navigation_hint.update("Press Enter ↵ to continue")
            return

        # Handle text-only states (PART* states) - auto-advance to next WAIT state
        _, _, next_state = STATE_CONFIG[self._state]
        if next_state is not None:
            self._state = next_state
            self._show_state()

    def _setup_terminal_for_command(self, command: str) -> None:
        """Show terminal with given command and action menu."""
        if self._terminal is None:
            self._terminal = TerminalWidget(
                prefilled_command=command,
                auto_focus=False,
                timeout=120 if "pip install" in command else 30,
            )
            self._command_container.mount(self._terminal)
        else:
            self._terminal.input_widget.value = command
            self._terminal.input_widget.disabled = False

        menu = ActionMenu()
        self._command_container.mount(menu)
        menu.focus()
        self._command_container.scroll_visible()

        self._navigation_hint.update("Select an option to continue")

    def _get_current_command(self) -> str | None:
        """Get the command for the current state."""
        _, command, _ = STATE_CONFIG[self._state]
        return command

    def _advance_state(self) -> None:
        """Move to next state."""
        _, _, next_state = STATE_CONFIG[self._state]
        if next_state is None:
            return

        self._state = next_state
        self._navigation_hint.update("")
        self._show_state()

    def on_action_menu_action_selected(self, event: ActionMenu.ActionSelected) -> None:
        """Handle action menu selection."""
        # Only handle in WAIT_* states
        command = self._get_current_command()
        if command is None:
            return

        # Remove menu
        try:
            menu = self.query_one(ActionMenu)
            menu.remove()
        except Exception:
            pass

        # Disable terminal input
        if self._terminal:
            self._terminal.disable_input()

        # Execute action
        match event.action:
            case "Run":
                if self._terminal:
                    self.run_worker(self._terminal.run_command(command))
            case "Skip":
                if self._terminal:
                    self._terminal.log_widget.write("[yellow]Skipping step...[/]")

        self._advance_state()

    def on_blur(self, event: events.Blur) -> None:
        """Keep focus on the widget unless terminal/menu is active."""
        command = self._get_current_command()
        if command is None:
            self.call_after_refresh(self.focus)
