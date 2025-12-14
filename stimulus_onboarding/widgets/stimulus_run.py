"""Stimulus run scene widget for STIMULUS onboarding."""

import re
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
)

project_root = Path(__file__).parent.parent.parent





# Load text from files
assets_dir = Path(__file__).parent / "assets"

_part1_content = process_text_placeholders((assets_dir / "stimulus-run-part-1.txt").read_text().strip(), project_root)
_part2_content = process_text_placeholders((assets_dir / "stimulus-run-part-2.txt").read_text().strip(), project_root)
_part3_content = process_text_placeholders((assets_dir / "stimulus-run-part-3.txt").read_text().strip(), project_root)
_part4_content = process_text_placeholders((assets_dir / "stimulus-run-part-4.txt").read_text().strip(), project_root)
_part5_content = process_text_placeholders((assets_dir / "stimulus-run-part-5.txt").read_text().strip(), project_root)

PART1_TEXT = _part1_content
PART2_TEXT = "\n\n" + _part2_content
PART3_TEXT = "\n\n" + _part3_content
PART4_TEXT = "\n\n" + _part4_content
PART5_TEXT = "\n\n" + _part5_content

FULL_TEXT = PART1_TEXT + PART2_TEXT + PART3_TEXT + PART4_TEXT + PART5_TEXT

# Commands
INSTALL_COMMAND = "uv pip install git+https://github.com/mathysgrapotte/stimulus-py.git@h5ad-support"
SPLIT_COMMAND = "stimulus split --data data/vcc_training_subset.h5ad --yaml data/split.yaml --output output/vcc_split"
LS_COMMAND = "ls -lh output/vcc_split"
ANALYSIS_COMMAND = "uv run stimulus_onboarding/case_study_analysis/analyze_splits.py"


class StimulusRunScene(Static):
    """Scene for installing and running STIMULUS."""

    can_focus = True

    def __init__(self) -> None:
        super().__init__()
        self._char_index = 0
        self._typing_timer: Timer | None = None

        # State tracking
        self._part1_done = False
        self._part2_done = False
        self._part3_done = False
        self._part4_done = False
        self._waiting_for_install = False
        self._waiting_for_split = False
        self._waiting_for_ls = False
        self._waiting_for_analysis = False
        self._terminal_shown = False
        self._completed = False

        # Single persistent terminal for both commands
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

        # Start typing animation
        self._typing_timer = self.set_interval(TYPING_SPEED, self._type_next_char)

    def _type_next_char(self) -> None:
        """Type one character at a time."""
        # Check if we reached end of Part 1
        if not self._part1_done and self._char_index >= len(PART1_TEXT):
            self._part1_done = True
            self._waiting_for_install = True
            if self._typing_timer:
                self._typing_timer.stop()

            # Show terminal with install command (first time)
            if not self._terminal_shown:
                self._terminal_shown = True
                self._terminal = TerminalWidget(
                    prefilled_command=INSTALL_COMMAND,
                    auto_focus=False,
                    timeout=120,  # Longer timeout for pip install
                )
                self._command_container.mount(self._terminal)

            # Mount action menu
            menu = ActionMenu()
            self._command_container.mount(menu)
            menu.focus()
            self._command_container.scroll_visible()

            self._navigation_hint.update("Select an option to continue")
            return

        # Check if we reached end of Part 2
        if self._part1_done and self._char_index >= len(PART1_TEXT + PART2_TEXT):
            if not self._part2_done:
                self._part2_done = True
                self._waiting_for_split = True
                if self._typing_timer:
                    self._typing_timer.stop()

                # Update terminal input with split command (reuse same terminal)
                if self._terminal:
                    self._terminal.input_widget.value = SPLIT_COMMAND
                    self._terminal.input_widget.disabled = False

                # Mount new action menu
                menu = ActionMenu()
                self._command_container.mount(menu)
                menu.focus()
                self._command_container.scroll_visible()

                self._navigation_hint.update("Select an option to continue")

            if self._waiting_for_split:
                return

        # Check if we reached end of Part 3
        if self._part2_done and self._char_index >= len(PART1_TEXT + PART2_TEXT + PART3_TEXT):
            if not self._part3_done:
                self._part3_done = True
                self._waiting_for_ls = True
                if self._typing_timer:
                    self._typing_timer.stop()

                # Update terminal input with ls command
                if self._terminal:
                    self._terminal.input_widget.value = LS_COMMAND
                    self._terminal.input_widget.disabled = False

                # Mount new action menu
                menu = ActionMenu()
                self._command_container.mount(menu)
                menu.focus()
                self._command_container.scroll_visible()

                self._navigation_hint.update("Select an option to continue")

            if self._waiting_for_ls:
                return

        # Check if we reached end of Part 4
        if self._part3_done and self._char_index >= len(PART1_TEXT + PART2_TEXT + PART3_TEXT + PART4_TEXT):
            if not self._part4_done:
                self._part4_done = True
                self._waiting_for_analysis = True
                if self._typing_timer:
                    self._typing_timer.stop()

                # Update terminal input with analysis command
                if self._terminal:
                    self._terminal.input_widget.value = ANALYSIS_COMMAND
                    self._terminal.input_widget.disabled = False

                # Mount new action menu
                menu = ActionMenu()
                self._command_container.mount(menu)
                menu.focus()
                self._command_container.scroll_visible()

                self._navigation_hint.update("Select an option to continue")

            if self._waiting_for_analysis:
                return

        # Check if we reached end of Part 5
        if self._part4_done and self._char_index >= len(FULL_TEXT):
            if not self._completed:
                self._completed = True
                self._navigation_hint.update("Press Enter ↵ to continue")
                if self._typing_timer:
                    self._typing_timer.stop()
            return

        # Type next character
        self._char_index += 1
        self._text_widget.update(self._render_text(self._char_index))

        # Check for pause at newlines
        current_text = FULL_TEXT
        if self._char_index > 0 and current_text[self._char_index - 1] == "\n":
            if self._char_index < 2 or current_text[self._char_index - 2] != "\n":
                if self._typing_timer:
                    self._typing_timer.stop()
                self.set_timer(0.8, self._resume_typing_after_pause)

    def _resume_typing_after_pause(self) -> None:
        """Resume typing after a narrative pause."""
        self._typing_timer = self.set_interval(TYPING_SPEED, self._type_next_char)

    def _render_text(self, length: int) -> str:
        """Render text up to length."""
        return fix_incomplete_markup(FULL_TEXT[:length])

    def on_action_menu_action_selected(self, event: ActionMenu.ActionSelected) -> None:
        """Handle action menu selection."""
        # Remove the menu immediately using query to ensure we get the right one
        try:
            menu = self.query_one(ActionMenu)
            menu.remove()
        except Exception:
            pass

        if self._waiting_for_install:
            if self._terminal:
                self._terminal.disable_input()

            if event.action == "Run":
                if self._terminal:
                    self.run_worker(self._terminal.run_command(INSTALL_COMMAND))
            elif event.action == "Skip":
                if self._terminal:
                    self._terminal.log_widget.write("[yellow]Skipping install...[/]")

            self._waiting_for_install = False
            self._navigation_hint.update("")
            self._resume_typing_after_pause()

        elif self._waiting_for_split:
            if self._terminal:
                self._terminal.disable_input()

            if event.action == "Run":
                if self._terminal:
                    self.run_worker(self._terminal.run_command(SPLIT_COMMAND))
            elif event.action == "Skip":
                if self._terminal:
                    self._terminal.log_widget.write("[yellow]Skipping split...[/]")

            self._waiting_for_split = False
            self._navigation_hint.update("")
            self._resume_typing_after_pause()

        elif self._waiting_for_ls:
            if self._terminal:
                self._terminal.disable_input()

            if event.action == "Run":
                if self._terminal:
                    self.run_worker(self._terminal.run_command(LS_COMMAND))
            elif event.action == "Skip":
                if self._terminal:
                    self._terminal.log_widget.write("[yellow]Skipping ls...[/]")

            self._waiting_for_ls = False
            self._navigation_hint.update("")
            self._resume_typing_after_pause()

        elif self._waiting_for_analysis:
            if self._terminal:
                self._terminal.disable_input()

            if event.action == "Run":
                if self._terminal:
                    self.run_worker(self._terminal.run_command(ANALYSIS_COMMAND))
            elif event.action == "Skip":
                if self._terminal:
                    self._terminal.log_widget.write("[yellow]Skipping analysis...[/]")

            self._waiting_for_analysis = False
            self._navigation_hint.update("")
            self._resume_typing_after_pause()

    def on_unmount(self) -> None:
        """Clean up timers."""
        stop_timer_safely(self._typing_timer)

    def on_blur(self, event: events.Blur) -> None:
        """Keep focus on the widget unless terminal/menu is active."""
        if not self._terminal_shown:
            self.call_after_refresh(self.focus)
