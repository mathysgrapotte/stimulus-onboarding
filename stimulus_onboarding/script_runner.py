"Generic script runner widget for declarative scenes."

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual import events
from textual.widgets import Static

from stimulus_onboarding.scripting import Display, Gradient, Step, Terminal, Type, Wait, WaitForInput
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
PROJECT_ROOT = Path(__file__).parent.parent


def _strip_yaml_markers(text: str) -> str:
    """Remove YAML block markers from text."""
    return text.replace(YAML_BLOCK_START, "").replace(YAML_BLOCK_END, "")


@dataclass
class TextSegment:
    """A segment of text in the display buffer."""
    content: str
    visible_length: int
    is_gradient: bool = False
    gradient_offset: int = 0
    
    @property
    def is_fully_visible(self) -> bool:
        return self.visible_length >= len(self.content)
    
    def render(self) -> str:
        """Render the segment to a string with markup."""
        text = self.content[:self.visible_length]
        
        # Handle gradient
        if self.is_gradient:
            return apply_gradient(text, self.gradient_offset)
            
        # Handle incomplete markup for typing
        return fix_incomplete_markup(text)


class ScriptedScene(Static):
    """A generic scene that executes a list of Steps."""

    can_focus = True
    
    BINDINGS = []

    def __init__(self) -> None:
        super().__init__()
        self._script: list[Step] = []
        self._current_step_index = 0
        
        # Buffer
        self._segments: list[TextSegment] = []
        
        # State
        self._waiting_for_input = False
        self._expected_key = ""
        self._waiting_for_command = False
        
        # UI Elements
        self._text_widget: Static
        self._command_container: Static
        self._navigation_hint: Static
        self._terminal: TerminalWidget | None = None
        
        # Timers
        self._typing_timer = None
        self._animation_timer = None
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
        
        # Start global animation loop for gradients
        self._animation_timer = self.set_interval(0.08, self._animate_frame)
        
        self._execute_next_step()

    def _render_all(self) -> None:
        """Render all text segments to the widget."""
        full_text = ""
        for i, segment in enumerate(self._segments):
            rendered = segment.render()
            if i > 0:
                # Add spacing between segments if they are paragraphs?
                # For now, we assume segments are just chunks of text.
                # If we want newlines, the content must have them.
                # But previous Display implementation added \n\n.
                # Let's verify how we construct segments.
                pass
            full_text += rendered
            
        # Strip markers only for final display?
        # Actually segments might have markers if they came from Display/Type.
        # But we want to keep markers if we are typing char by char?
        # fix_incomplete_markup handles tags.
        # _strip_yaml_markers handles the block markers.
        # If we strip them early, we lose the box drawing structure during typing?
        # No, markers are usually at start/end.
        
        # Simple approach: Join all rendered segments.
        self._text_widget.update(_strip_yaml_markers(full_text))
        self.call_after_refresh(self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> None:
        """Scroll the parent container to bottom."""
        # This assumes the widget is in a VerticalScroll
        if self.parent and isinstance(self.parent, VerticalScroll):
            self.parent.scroll_end(animate=True)

    def _animate_frame(self) -> None:
        """Update animations (gradients) and re-render."""
        needs_render = False
        for segment in self._segments:
            if segment.is_gradient:
                segment.gradient_offset = cycle_gradient_offset(segment.gradient_offset)
                needs_render = True
        
        if needs_render:
            self._render_all()

    def _process_content(self, content: Union[str, Path]) -> str:
        """Load and process content from string or file."""
        if isinstance(content, Path):
            raw_text = content.read_text().strip()
            return process_text_placeholders(raw_text, PROJECT_ROOT)
        return str(content)

    def _execute_next_step(self) -> None:
        """Execute the current step in the script."""
        if self._current_step_index >= len(self._script):
            return

        step = self._script[self._current_step_index]
        self._current_step_index += 1
        
        match step:
            case Display():
                self._handle_display(step)
                self._execute_next_step()
            case Type():
                self._handle_type(step)
                # Does not auto-advance; waits for typing to finish
            case Gradient():
                self._handle_gradient(step)
                self._execute_next_step()
            case Terminal():
                self._handle_terminal(step)
            case Wait():
                self._handle_wait(step)
            case WaitForInput():
                self._handle_wait_for_input(step)

    def _handle_display(self, step: Display) -> None:
        text = self._process_content(step.content)
        
        if step.clear:
            self._segments.clear()
        elif self._segments:
            # Add separator if appending
            self._segments.append(TextSegment(content="\n\n", visible_length=2))
            
        self._segments.append(TextSegment(content=text, visible_length=len(text)))
        self._render_all()

    def _handle_gradient(self, step: Gradient) -> None:
        # Gradient text usually shouldn't add a double newline before it if it's part of a sentence?
        # But our current usage in welcome.py is "Welcome to " + "STIMULUS".
        # So we should NOT force newlines.
        # But `Display` step (previous impl) forced newlines.
        # Let's make `Display` / `Type` / `Gradient` just append raw text.
        # It's the USER'S responsibility to add \n\n in the content string if they want paragraphs.
        # CHANGE from previous version: removed automatic \n\n injection.
        
        # Wait, previous `Display` did `if self._full_text_buffer: += "\n\n"`.
        # This is useful for "Step 1", "Step 2" blocks.
        # But for "Welcome to " + "STIMULUS", it breaks.
        # Compromise: Check if the content starts with newline? No.
        # We need a `append: bool = True` or `newline: bool = True` flag?
        # Or just let the script handle it.
        # Let's assume for now script handles it, OR we add a specialized `Paragraph` step.
        # I will remove automatic newline insertion to support inline composition (Welcome + STIMULUS).
        # Existing scenes might need updates if they relied on it.
        # Checking `TransformScene`: `Display(intro)`, `Terminal`, `Display(run)`.
        # `intro` text usually ends with text. `run` text usually starts with `\n\n` in the file?
        # In `transform_scene.py` original: `TRANSFORM_RUN = "\n\n" + ...`
        # So the files often have newlines.
        # BUT `DataConfigScene`: `PART2_TEXT = "\n\n" + ...`
        # `StimulusRunScene`: `PART2_TEXT = PART1_TEXT + "\n\n" + ...`
        # It seems the previous code manually managed newlines often.
        # So removing auto-newline is probably safer for granular control.
        
        self._segments.append(TextSegment(content=step.content, visible_length=len(step.content), is_gradient=True))
        self._render_all()

    def _handle_type(self, step: Type) -> None:
        text = self._process_content(step.content)
        
        segment = TextSegment(content=text, visible_length=0)
        self._segments.append(segment)
        
        # Start typing timer
        self._typing_timer = self.set_interval(step.speed, lambda: self._type_tick(segment, step.speed))

    def _type_tick(self, segment: TextSegment, speed: float) -> None:
        if segment.is_fully_visible:
            stop_timer_safely(self._typing_timer)
            self._typing_timer = None
            self._execute_next_step()
            return
            
        # Handle pause at newlines (mimic welcome.py behavior)
        # Check current char about to be typed (or just typed?)
        # welcome.py checks AFTER typing.
        
        segment.visible_length += 1
        
        # Check for newline pause
        current_idx = segment.visible_length - 1
        if current_idx > 0 and segment.content[current_idx] == '\n':
             # Heuristic: if valid newline and not a sequence of newlines
             if current_idx < 1 or segment.content[current_idx - 1] != '\n':
                 stop_timer_safely(self._typing_timer)
                 self._typing_timer = None
                 self.set_timer(0.8, lambda: self._resume_typing(segment, speed))
        
        self._render_all()

    def _resume_typing(self, segment: TextSegment, speed: float) -> None:
        self._typing_timer = self.set_interval(speed, lambda: self._type_tick(segment, speed))

    def _handle_terminal(self, step: Terminal) -> None:
        if self._segments and not self._segments[-1].content.endswith("\n"):
             # Terminals usually look better on a new line
             self._segments.append(TextSegment(content="\n\n", visible_length=2))
             self._render_all()

        if self._terminal is None:
            self._terminal = TerminalWidget(
                prefilled_command=step.command, 
                auto_focus=False,
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
        self.set_timer(step.seconds, self._execute_next_step)

    def _handle_wait_for_input(self, step: WaitForInput) -> None:
        self._waiting_for_input = True
        self._expected_key = step.key
        
        if step.key == "down":
             self._start_hint_animation()
        else:
             self._navigation_hint.update(step.prompt)

    def on_key(self, event: events.Key) -> None:
        if not self._waiting_for_input:
            return
            
        if event.key == self._expected_key:
            self._waiting_for_input = False
            self._stop_hint_animation()
            self._navigation_hint.update("")
            self._execute_next_step()

    def on_action_menu_action_selected(self, event: ActionMenu.ActionSelected) -> None:
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
                    last_step = self._script[self._current_step_index - 1]
                    if isinstance(last_step, Terminal):
                        self.run_worker(self._terminal.run_command(last_step.command))
            case "Skip":
                if self._terminal:
                    self._terminal.log_widget.write("[yellow]Skipping step...[/]")

        self._waiting_for_command = False
        self._execute_next_step()

    def _start_hint_animation(self) -> None:
        self._nav_hint_animation_timer = self.set_interval(0.08, self._animate_down_hint)

    def _animate_down_hint(self) -> None:
        self._nav_hint_gradient_offset = cycle_gradient_offset(self._nav_hint_gradient_offset)
        arrow = apply_gradient("↓", self._nav_hint_gradient_offset)
        self._navigation_hint.update(f"press {arrow} to continue")

    def _stop_hint_animation(self) -> None:
        stop_timer_safely(self._nav_hint_animation_timer)
        self._nav_hint_animation_timer = None

    def on_blur(self, event: events.Blur) -> None:
        if not self._waiting_for_command:
            self.call_after_refresh(self.focus)

    def on_unmount(self) -> None:
        stop_timer_safely(self._nav_hint_animation_timer)
        stop_timer_safely(self._typing_timer)
        stop_timer_safely(self._animation_timer)