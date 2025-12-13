"""Case study scene widget for STIMULUS onboarding."""

from pathlib import Path

from textual.app import ComposeResult
from textual.widgets import Static


class CaseStudyScene(Static):
    """Case study scene for the onboarding experience."""

    def compose(self) -> ComposeResult:
        """Compose the case study scene content."""
        assets_dir = Path(__file__).parent / "assets"
        case_study_file = assets_dir / "case-study.txt"
        case_study_text = case_study_file.read_text()
        yield Static(case_study_text, id="case-study-text")

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        pass
