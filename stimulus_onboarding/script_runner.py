"Generic script runner widget for declarative scenes."

from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual import events
from textual.widgets import Static

from stimulus_onboarding.scripting import Display, Step, Terminal, Wait, WaitForInput
from stimulus_onboarding.ui_components import (
    ActionMenu,
    TerminalWidget,
    fix_incomplete_markup,
    process_text_placeholders,
    YAML_BLOCK_END,
    YAML_BLOCK_START,
    apply_gradient,
    cycle_gradient_offset,
    stop_timer_safely,
)

# Base path for project root (assumed to be 2 levels up from this file)
# stimulus_onboarding/script_runner.py -> stimulus_onboarding/ -> root
PROJECT_ROOT = Path(__file__).parent.parent


def _strip_yaml_markers(text: str) -> str:
    """Remove YAML block markers from text."""
    return text.replace(YAML_BLOCK_START, "").replace(YAML_BLOCK_END, "")


class ScriptedScene(Static):
    """A generic scene that executes a list of Steps."""

    can_focus = True
    
    # Allow some default bindings, but WaitForInput will handle specific keys dynamically if needed
    BINDINGS = [
        # We might need to capture specific keys for WaitForInput
    ]

    def __init__(self) -> None:
        super().__init__()
        self._script: list[Step] = []
        self._current_step_index = 0
        
        # State
        self._waiting_for_input = False
        self._expected_key = ""
        self._waiting_for_command = False
        
        # UI Elements
        self._text_widget: Static
        self._command_container: Static
        self._navigation_hint: Static
        self._terminal: TerminalWidget | None = None
        
        # Hint animation
        self._nav_hint_animation_timer = None
        self._nav_hint_gradient_offset = 0

    def build_script(self) -> list[Step]:
        """Override this method to define the scene's script."""
        return []

    def compose(self) -> ComposeResult:
        """Standard composition for scripted scenes."""
        yield Static("", id="script-text")
        yield Static(id="command-container")
        yield Static("", id="navigation-hint")

    def on_mount(self) -> None:
        """Start the script execution."""
        self.focus()
        self._text_widget = self.query_one("#script-text", Static)
        self._command_container = self.query_one("#command-container", Static)
        self._navigation_hint = self.query_one("#navigation-hint", Static)
        
        self._script = self.build_script()
        self._execute_next_step()

    def _execute_next_step(self) -> None:
        """Execute the current step in the script."""
        if self._current_step_index >= len(self._script):
            # Script complete
            return

        step = self._script[self._current_step_index]
        self._current_step_index += 1
        
        match step:
            case Display():
                self._handle_display(step)
                self._execute_next_step()
            case Terminal():
                self._handle_terminal(step)
                # Does not auto-advance; waits for action menu
            case Wait():
                self._handle_wait(step)
                # Auto-advances after timer
            case WaitForInput():
                self._handle_wait_for_input(step)
                # Does not auto-advance; waits for input

    def _handle_display(self, step: Display) -> None:
        """Handle Display step."""
        content = step.content
        if isinstance(content, Path):
            # Read and process file
            raw_text = content.read_text().strip()
            # We assume placeholders might need processing
            text = process_text_placeholders(raw_text, PROJECT_ROOT)
        else:
            text = str(content)
        
        # Strip markers for immediate display (animation support could be added here later)
        text = _strip_yaml_markers(text)
        text = fix_incomplete_markup(text)
        
        # To support "append", we really should maintain the full text state.
        if not hasattr(self, "_full_text_buffer"):
            self._full_text_buffer = ""
            
        if step.clear:
            self._full_text_buffer = text
        else:
            if self._full_text_buffer:
                 self._full_text_buffer += "\n\n" + text
            else:
                 self._full_text_buffer = text
        
        self._text_widget.update(self._full_text_buffer)
        
        self.call_after_refresh(self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> None:
        """Scroll the parent container to bottom."""
        # This assumes the widget is in a VerticalScroll
        if self.parent and isinstance(self.parent, VerticalScroll):
            self.parent.scroll_end(animate=True)

    def _handle_terminal(self, step: Terminal) -> None:
        """Handle Terminal step."""
        if self._terminal is None:
            self._terminal = TerminalWidget(
                prefilled_command=step.command, 
                auto_focus=False,
                # Simple heuristic for timeout based on command type, could be exposed in Step
                timeout=120 if "pip install" in step.command else 30
            )
            self._command_container.mount(self._terminal)
        else:
            self._terminal.input_widget.value = step.command
            self._terminal.input_widget.disabled = False
        
        menu = ActionMenu()
        self._command_container.mount(menu)
        menu.focus()
        self._command_container.scroll_visible()
        
        self._waiting_for_command = True
        self._navigation_hint.update("Select an option to continue")

    def _handle_wait(self, step: Wait) -> None:
        """Handle Wait step."""
        self.set_timer(step.seconds, self._execute_next_step)

    def _handle_wait_for_input(self, step: WaitForInput) -> None:
        """Handle WaitForInput step."""
        self._waiting_for_input = True
        self._expected_key = step.key
        
        if step.key == "down":
             self._start_hint_animation()
        else:
             self._navigation_hint.update(step.prompt)

    def on_key(self, event: events.Key) -> None:
        """Handle key presses for WaitForInput."""
        if not self._waiting_for_input:
            return
            
        if event.key == self._expected_key:
            self._waiting_for_input = False
            self._stop_hint_animation()
            self._navigation_hint.update("")
            self._execute_next_step()

    def on_action_menu_action_selected(self, event: ActionMenu.ActionSelected) -> None:
        """Handle action menu selection for Terminal step."""
        if not self._waiting_for_command:
            return

        try:
            menu = self.query_one(ActionMenu)
            menu.remove()
        except Exception:
            pass

        if self._terminal:
            self._terminal.disable_input()

        # Execute action
        match event.action:
            case "Run":
                if self._terminal:
                    # We need the command from the *current* step (which was the terminal step)
                    # But we already incremented index. So it's index-1.
                    last_step = self._script[self._current_step_index - 1]
                    if isinstance(last_step, Terminal):
                        self.run_worker(self._terminal.run_command(last_step.command))
            case "Skip":
                if self._terminal:
                    self._terminal.log_widget.write("[yellow]Skipping step...[/]")

        self._waiting_for_command = False
        # Continue script
        self._execute_next_step()

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
        # Only clear if we are not showing something else? 
        # _execute_next_step might overwrite it anyway.

    def on_blur(self, event: events.Blur) -> None:
        """Keep focus on the widget unless terminal/menu is active."""
        if not self._waiting_for_command:
            self.call_after_refresh(self.focus)

    def on_unmount(self) -> None:
        """Clean up."""
        stop_timer_safely(self._nav_hint_animation_timer)
