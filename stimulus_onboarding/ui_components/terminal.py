"""Interactive terminal widget."""

import shlex
import subprocess

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Input, RichLog


class TerminalWidget(Vertical):
    """A widget that simulates a terminal with command input and output."""

    DEFAULT_CSS = """
    TerminalWidget {
        width: 100%;
        height: auto;
        min-height: 20;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }

    RichLog {
        width: 100%;
        height: auto;
        min-height: 10;
        max-height: 20;
        background: $surface;
        color: $text;
        border: none;
        overflow-y: scroll;
    }

    Input {
        width: 100%;
        margin-top: 1;
        background: $surface;
        border: none;
        color: $text;
    }
    
    Input:focus {
        border: none;
    }
    """

    def __init__(self, prefilled_command: str = "") -> None:
        super().__init__()
        self.prefilled_command = prefilled_command
        self.log_widget: RichLog
        self.input_widget: Input

    def compose(self) -> ComposeResult:
        yield RichLog(highlight=True, markup=True)
        yield Input(placeholder="Type a command...", value=self.prefilled_command)

    def on_mount(self) -> None:
        self.log_widget = self.query_one(RichLog)
        self.input_widget = self.query_one(Input)
        
        # Write generic welcome message or prompt setup if needed
        self.log_widget.write("[bold green]$[/] Ready")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip()
        if not command:
            return

        # Echo command
        self.log_widget.write(f"[bold green]$[/] {command}")
        
        # Clear input (optional, or keep generic)
        # self.input_widget.value = "" 

        try:
            # Run command
            args = shlex.split(command)
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=10 
            )
            
            # Display output
            if result.stdout:
                self.log_widget.write(result.stdout.rstrip())
            if result.stderr:
                self.log_widget.write(f"[red]{result.stderr.rstrip()}[/]")
                
        except Exception as e:
            self.log_widget.write(f"[red]Error: {e}[/]")
        
        # Scroll to bottom
        self.log_widget.scroll_end()
