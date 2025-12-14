"""Main Textual application for STIMULUS onboarding."""

from collections.abc import Iterable
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static

from stimulus_onboarding.widgets import (
    CaseStudyScene,
    DataConfigScene,
    StimulusRunScene,
    TransformScene,
    WelcomeScene,
)


class StimulusOnboardingApp(App[None]):
    """Interactive onboarding TUI for STIMULUS."""

    CSS_PATH = Path(__file__).parent / "app.tcss"

    BINDINGS: Iterable[Binding] = [
        Binding("enter", "next_scene", "Next", show=True),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("escape", "quit", "Quit", show=False),
    ]

    current_scene_index: reactive[int] = reactive(0)
    scenes: list[type[Static]] = [
        WelcomeScene,
        CaseStudyScene,
        DataConfigScene,
        StimulusRunScene,
        TransformScene,
    ]

    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        with VerticalScroll(id="main"):
            yield self.scenes[self.current_scene_index]()

    def action_next_scene(self) -> None:
        """Advance to the next scene."""
        if self.current_scene_index < len(self.scenes) - 1:
            self.current_scene_index += 1
            # Remove old scene and add new scene
            container = self.query_one("#main", VerticalScroll)
            container.remove_children()
            container.mount(self.scenes[self.current_scene_index]())
        else:
            # On last scene, exit the app
            self.exit()


def main() -> None:
    """Entry point for the onboarding TUI."""
    app = StimulusOnboardingApp()
    app.run()


if __name__ == "__main__":
    main()
