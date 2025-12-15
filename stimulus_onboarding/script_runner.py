"Generic script runner widget for declarative scenes."

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual import events
from textual.widgets import Static

from stimulus_onboarding.scripting import (
    Display,
    DisplayPython,
    DisplayYaml,
    Gradient,
    Step,
    Terminal,
    Type,
    Wait,
    WaitForInput,
)
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


@dataclass
class CodeSegment:
    """A segment of code to display with syntax highlighting."""
    content: str
    language: str
    title: str | None = None
    
    def render(self) -> RenderableType:
        """Render the code segment."""
        # Use One Dark inspired theme if possible, or default
        syntax = Syntax(
            self.content, 
            self.language, 
            theme="one-dark", 
            line_numbers=True,
            word_wrap=True
        )
        if self.title:
            return Panel(syntax, title=self.title, border_style="blue")
        return syntax


class ScriptedScene(Static):
    """A generic scene that executes a list of Steps."""

    can_focus = True
    
    BINDINGS = []

    def __init__(self) -> None:
        super().__init__()
        self._script: list[Step] = []
        self._current_step_index = 0
        
        # Buffer
        self._segments: list[Union[TextSegment, CodeSegment]] = []
        
        # State
        self._waiting_for_input = False
        self._expected_key = ""
        self._waiting_for_command = False
        self._waiting_for_command_completion = False
        
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
        """Render all segments to the widget."""
        renderables: list[RenderableType] = []
        current_text_buffer = ""
        
        for segment in self._segments:
            if isinstance(segment, TextSegment):
                current_text_buffer += segment.render()
            else:
                # Flush text buffer if needed
                if current_text_buffer:
                    renderables.append(_strip_yaml_markers(current_text_buffer))
                    current_text_buffer = ""
                
                # Add code segment
                renderables.append(segment.render())
        
        # Flush remaining text
        if current_text_buffer:
            renderables.append(_strip_yaml_markers(current_text_buffer))
            
        if not renderables:
            self._text_widget.update("")
        elif len(renderables) == 1:
            self._text_widget.update(renderables[0])
        else:
            self._text_widget.update(Group(*renderables))
            
        self.call_after_refresh(self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> None:
        """Scroll the parent container to bottom."""
        if self.parent and isinstance(self.parent, VerticalScroll):
            self.parent.scroll_end(animate=True)

    def _animate_frame(self) -> None:
        """Update animations (gradients) and re-render."""
        needs_render = False
        for segment in self._segments:
            if isinstance(segment, TextSegment) and segment.is_gradient:
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
        # Don't proceed if we're waiting for a command to complete
        if self._waiting_for_command_completion:
            return
            
        if self._current_step_index >= len(self._script):
            return

        step = self._script[self._current_step_index]
        self._current_step_index += 1
        
        match step:
            case Display():
                self._handle_display(step)
                self._execute_next_step()
            case DisplayYaml():
                self._handle_display_yaml(step)
                self._execute_next_step()
            case DisplayPython():
                self._handle_display_python(step)
                self._execute_next_step()
            case Type():
                self._handle_type(step)
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
             # Heuristic: Add spacing if we are appending to a text block
             if isinstance(self._segments[-1], TextSegment):
                 self._segments.append(TextSegment(content="\n\n", visible_length=2))
            
        self._segments.append(TextSegment(content=text, visible_length=len(text)))
        self._render_all()

    def _handle_display_yaml(self, step: DisplayYaml) -> None:
        content_str = ""
        title = None
        if isinstance(step.content, Path):
            # Resolve relative to project root if needed
            full_path = PROJECT_ROOT / step.content
            content_str = full_path.read_text().strip()
            title = step.content.name
        else:
            content_str = str(step.content)
            
        self._segments.append(CodeSegment(content=content_str, language="yaml", title=title))
        self._render_all()

    def _handle_display_python(self, step: DisplayPython) -> None:
        content_str = ""
        title = None
        if isinstance(step.content, Path):
            content_str = step.content.read_text().strip()
            title = step.content.name
        else:
            content_str = str(step.content)

        self._segments.append(CodeSegment(content=content_str, language="python", title=title))
        self._render_all()

    def _handle_gradient(self, step: Gradient) -> None:
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
            
        segment.visible_length += 1
        
        # Check for newline pause
        current_idx = segment.visible_length - 1
        if current_idx > 0 and segment.content[current_idx] == '\n':
             if current_idx < 1 or segment.content[current_idx - 1] != '\n':
                 stop_timer_safely(self._typing_timer)
                 self._typing_timer = None
                 self.set_timer(0.8, lambda: self._resume_typing(segment, speed))
        
        self._render_all()

    def _resume_typing(self, segment: TextSegment, speed: float) -> None:
        self._typing_timer = self.set_interval(speed, lambda: self._type_tick(segment, speed))

    def _handle_terminal(self, step: Terminal) -> None:
        # Add spacing before terminal if needed
        if self._segments:
            last = self._segments[-1]
            if isinstance(last, TextSegment) and not last.content.endswith("\n"):
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

        self._waiting_for_command = False

        match event.action:
            case "Run":
                if self._terminal:
                    # Look back for the last Terminal step
                    # Note: We incremented index, so it's likely index-1
                    last_step = self._script[self._current_step_index - 1]
                    if isinstance(last_step, Terminal):
                        self._waiting_for_command_completion = True
                        self.run_worker(self._run_command_and_continue(last_step.command))
            case "Skip":
                if self._terminal:
                    self._terminal.log_widget.write("[yellow]Skipping step...[/]")
                self._execute_next_step()

    async def _run_command_and_continue(self, command: str) -> None:
        """Run a terminal command and continue to next step when complete."""
        if self._terminal:
            await self._terminal.run_command(command)
        self._waiting_for_command_completion = False
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
