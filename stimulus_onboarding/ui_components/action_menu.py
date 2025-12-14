"""Reusable action menu component."""

from textual import events
from textual.app import ComposeResult
from textual.containers import Container
from textual.message import Message
from textual.widgets import Static


class ActionMenu(Container):
    """A navigable menu with selectable options.

    Emits ActionMenu.ActionSelected message when user confirms selection.
    """

    COMPONENT_CLASSES = {"action-menu--selected"}

    DEFAULT_CSS = """
    ActionMenu {
        width: 100%;
        height: auto;
        layout: vertical;
        padding: 1;
        background: $surface;
    }

    .action-menu--option {
        padding: 0 1;
    }

    .action-menu--selected {
        color: $accent;
        text-style: bold;
    }
    """

    class ActionSelected(Message):
        """Emitted when an action is selected."""

        def __init__(self, action: str) -> None:
            super().__init__()
            self.action = action

    def __init__(self, options: list[str] | None = None) -> None:
        super().__init__()
        self._options = options or ["Run", "Skip"]
        self._selected_index = 0
        self._option_widgets: list[Static] = []
        self.can_focus = True

    def compose(self) -> ComposeResult:
        for option in self._options:
            widget = Static(option, classes="action-menu--option")
            self._option_widgets.append(widget)
            yield widget

    def on_mount(self) -> None:
        self._update_display()

    def _update_display(self) -> None:
        for i, widget in enumerate(self._option_widgets):
            widget.remove_class("action-menu--selected")
            if i == self._selected_index:
                widget.add_class("action-menu--selected")
                widget.update(f"› {self._options[i]}")
            else:
                widget.update(f"  {self._options[i]}")

    def on_key(self, event: events.Key) -> None:
        event.stop()
        match event.key:
            case "up":
                self._selected_index = (self._selected_index - 1) % len(self._options)
                self._update_display()
            case "down":
                self._selected_index = (self._selected_index + 1) % len(self._options)
                self._update_display()
            case "enter":
                self.post_message(self.ActionSelected(self._options[self._selected_index]))
