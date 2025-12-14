"""Interactive terminal widget."""

import asyncio

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

    def __init__(
        self, prefilled_command: str = "", auto_focus: bool = True, timeout: int = 10
    ) -> None:
        super().__init__()
        self.prefilled_command = prefilled_command
        self.auto_focus = auto_focus
        self.timeout = timeout
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
        
        # Auto-focus input
        if self.auto_focus:
            self.input_widget.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip()
        if not command:
            return

        # Run command asynchronously using Textual's worker
        self.run_worker(self.run_command(command))

    async def run_command(self, command: str) -> None:
        """Run a command in the terminal with real-time output streaming."""
        # Echo command
        self.log_widget.write(f"[bold green]$[/] {command}")

        process = None
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            async def read_stream(
                stream: asyncio.StreamReader | None, is_error: bool = False
            ) -> None:
                if stream is None:
                    return
                async for line in stream:
                    text = line.decode().rstrip()
                    if text:
                        if is_error:
                            self.log_widget.write(f"[red]{text}[/]")
                        else:
                            self.log_widget.write(text)
                        self.log_widget.scroll_end()

            await asyncio.wait_for(
                asyncio.gather(
                    read_stream(process.stdout),
                    read_stream(process.stderr, is_error=True),
                ),
                timeout=self.timeout,
            )
            await process.wait()

        except asyncio.TimeoutError:
            self.log_widget.write("[red]Error: Command timed out[/]")
            if process:
                process.kill()
        except Exception as e:
            self.log_widget.write(f"[red]Error: {e}[/]")

        self.log_widget.scroll_end()

    def disable_input(self) -> None:
        """Disable the input widget."""
        self.input_widget.disabled = True
        self.input_widget.classes = "disabled"
