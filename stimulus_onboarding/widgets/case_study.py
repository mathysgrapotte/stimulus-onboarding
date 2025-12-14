"""Case study scene widget for STIMULUS onboarding."""

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual import events
from textual.timer import Timer
from textual.widgets import Static

from stimulus_onboarding.ui_components import (
    ActionMenu,
    apply_gradient,
    cycle_gradient_offset,
    fix_incomplete_markup,
    stop_timer_safely,
    TerminalWidget,
)

# Load case study text from files
assets_dir = Path(__file__).parent / "assets"
case_study_part1_file = assets_dir / "case-study-part-1.txt"
case_study_part2_file = assets_dir / "case-study-part-2.txt"
case_study_part3_file = assets_dir / "case-study-part-3.txt"

_part1_content = case_study_part1_file.read_text().strip()
_part2_content = case_study_part2_file.read_text().strip()
_part3_content = case_study_part3_file.read_text().strip()

PART1_TEXT = _part1_content
PART2_TEXT = "\n\n" + _part2_content
PART3_TEXT = "\n\n" + _part3_content

FULL_TEXT = PART1_TEXT + PART2_TEXT + PART3_TEXT

# Command for visualization
VISUALIZE_COMMAND = "uv run stimulus_onboarding/case_study_analysis/visualize_anndata.py"


class CaseStudyScene(Static):
    """Case study scene for the onboarding experience."""

    BINDINGS = [
        Binding("down", "next_part", "Next Part", show=False),
    ]

    can_focus = True

    def __init__(self) -> None:
        super().__init__()
        self._current_part = 0
        self._waiting_for_action = False
        self._nav_hint_gradient_offset = 0
        self._nav_hint_animation_timer: Timer | None = None
        self._text_widget: Static
        self._navigation_hint: Static
        self._command_container: Static
        self._terminal: TerminalWidget | None = None

    def compose(self) -> ComposeResult:
        """Compose the case study scene content."""
        yield Static("", id="case-study-text")
        yield Static(id="command-container")
        yield Static("", id="navigation-hint")

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self.focus()
        self._text_widget = self.query_one("#case-study-text", Static)
        self._command_container = self.query_one("#command-container", Static)
        self._navigation_hint = self.query_one("#navigation-hint", Static)
        self._show_part(0)

    def _show_part(self, part: int) -> None:
        """Display text for given part immediately."""
        match part:
            case 0:
                self._text_widget.update(fix_incomplete_markup(PART1_TEXT))
                self._start_hint_animation()
            case 1:
                self._text_widget.update(fix_incomplete_markup(PART1_TEXT + PART2_TEXT))
                self._show_terminal_and_menu()
            case 2:
                self._text_widget.update(fix_incomplete_markup(FULL_TEXT))
                self._navigation_hint.update("Press Enter ↵ to continue to next step")

    def _start_hint_animation(self) -> None:
        """Start animated gradient hint for down arrow."""
        self._nav_hint_animation_timer = self.set_interval(0.08, self._animate_down_hint)

    def _animate_down_hint(self) -> None:
        """Animate the down arrow hint with a gradient."""
        self._nav_hint_gradient_offset = cycle_gradient_offset(self._nav_hint_gradient_offset)
        arrow = apply_gradient("↓", self._nav_hint_gradient_offset)
        self._navigation_hint.update(f"press {arrow} to continue")

    def _stop_hint_animation(self) -> None:
        """Stop the hint animation."""
        stop_timer_safely(self._nav_hint_animation_timer)
        self._nav_hint_animation_timer = None
        self._navigation_hint.update("")

    def _show_terminal_and_menu(self) -> None:
        """Show terminal widget with visualization command."""
        self._terminal = TerminalWidget(prefilled_command=VISUALIZE_COMMAND, auto_focus=False)
        self._command_container.mount(self._terminal)

        menu = ActionMenu()
        self._command_container.mount(menu)
        menu.focus()
        self._command_container.scroll_visible()

        self._waiting_for_action = True
        self._navigation_hint.update("Select an option to continue")

    def action_next_part(self) -> None:
        """Handle down arrow press."""
        if self._waiting_for_action:
            return
        if self._current_part >= 2:
            return

        self._stop_hint_animation()
        self._current_part += 1
        self._show_part(self._current_part)

    def on_action_menu_action_selected(self, event: ActionMenu.ActionSelected) -> None:
        """Handle action menu selection."""
        if not self._waiting_for_action:
            return

        try:
            menu = self.query_one(ActionMenu)
            menu.remove()
        except Exception:
            pass

        if self._terminal:
            self._terminal.disable_input()

        match event.action:
            case "Run":
                if self._terminal:
                    self.run_worker(self._terminal.run_command(VISUALIZE_COMMAND))
            case "Skip":
                if self._terminal:
                    self._terminal.log_widget.write("[yellow]Skipping step...[/]")

        self._waiting_for_action = False
        self._navigation_hint.update("")
        self._current_part = 2
        self._show_part(2)

    def on_unmount(self) -> None:
        """Clean up timers."""
        stop_timer_safely(self._nav_hint_animation_timer)

    def on_blur(self, event: events.Blur) -> None:
        """Keep focus on the widget unless terminal/menu is active."""
        if not self._waiting_for_action:
            self.call_after_refresh(self.focus)
