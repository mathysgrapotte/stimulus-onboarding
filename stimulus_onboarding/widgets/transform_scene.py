"""Transform scene widget for STIMULUS onboarding."""

from pathlib import Path

from textual.app import ComposeResult
from textual import events
from textual.widgets import Static

from stimulus_onboarding.ui_components import (
    ActionMenu,
    fix_incomplete_markup,
    process_text_placeholders,
    stop_timer_safely,
    TerminalWidget,
    YAML_BLOCK_END,
    YAML_BLOCK_START,
)

# Load text from files
assets_dir = Path(__file__).parent / "assets"
project_root = Path(__file__).parent.parent.parent

TRANSFORM_INTRO = process_text_placeholders(
    (assets_dir / "transform-intro.txt").read_text().strip(), project_root
)
TRANSFORM_RUN = "\n\n" + process_text_placeholders(
    (assets_dir / "transform-run.txt").read_text().strip(), project_root
)

FULL_TEXT = TRANSFORM_INTRO + TRANSFORM_RUN

# Command
TRANSFORM_COMMAND = "stimulus transform --data output/vcc_split --yaml data/transform_2000.yaml --output output/vcc_2000"


def _strip_yaml_markers(text: str) -> str:
    """Remove YAML block markers from text."""
    return text.replace(YAML_BLOCK_START, "").replace(YAML_BLOCK_END, "")


class TransformScene(Static):
    """Scene for transforming data."""

    can_focus = True

    def __init__(self) -> None:
        super().__init__()
        self._waiting_for_command = False
        self._completed = False
        self._text_widget: Static
        self._command_container: Static
        self._navigation_hint: Static
        self._terminal: TerminalWidget | None = None

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
        self._show_intro()

    def _show_intro(self) -> None:
        """Display intro text and terminal immediately."""
        text = _strip_yaml_markers(TRANSFORM_INTRO)
        self._text_widget.update(fix_incomplete_markup(text))
        self._setup_terminal_and_menu()

    def _setup_terminal_and_menu(self) -> None:
        """Show terminal with transform command."""
        self._terminal = TerminalWidget(prefilled_command=TRANSFORM_COMMAND, auto_focus=False)
        self._command_container.mount(self._terminal)

        menu = ActionMenu()
        self._command_container.mount(menu)
        menu.focus()
        self._command_container.scroll_visible()

        self._waiting_for_command = True
        self._navigation_hint.update("Select an option to continue")

    def _show_run_text(self) -> None:
        """Display full text after command."""
        text = _strip_yaml_markers(FULL_TEXT)
        self._text_widget.update(fix_incomplete_markup(text))
        self._navigation_hint.update("Press Enter ↵ to continue")
        self._completed = True

    def on_action_menu_action_selected(self, event: ActionMenu.ActionSelected) -> None:
        """Handle action menu selection."""
        if not self._waiting_for_command:
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
                    self.run_worker(self._terminal.run_command(TRANSFORM_COMMAND))
            case "Skip":
                if self._terminal:
                    self._terminal.log_widget.write("[yellow]Skipping transform...[/]")

        self._waiting_for_command = False
        self._show_run_text()

    def on_unmount(self) -> None:
        """Clean up resources."""
        pass

    def on_blur(self, event: events.Blur) -> None:
        """Keep focus on the widget unless terminal/menu is active."""
        if not self._waiting_for_command:
            self.call_after_refresh(self.focus)
