"""Case study scene widget for STIMULUS onboarding."""

from pathlib import Path

from stimulus_onboarding.scripting import Terminal, WaitForInput, Type
from stimulus_onboarding.script_runner import ScriptedScene

# Asset paths
assets_dir = Path(__file__).parent / "assets"

# Command for visualization
VISUALIZE_COMMAND = "uv run stimulus_onboarding/case_study_analysis/visualize_anndata.py"


class CaseStudyScene(ScriptedScene):
    """Case study scene for the onboarding experience."""

    def build_script(self):
        return [
            # Part 1
            Type(assets_dir / "case-study-part-1.txt", speed=0.03),
            WaitForInput(key="down", prompt="press ↓ to continue"),

            # Part 2
            Type(assets_dir / "case-study-part-2.txt", speed=0.03),
            Terminal(command=VISUALIZE_COMMAND),

            # Part 3
            Type(assets_dir / "case-study-part-3.txt", speed=0.03),
            WaitForInput(prompt="Press Enter ↵ to continue to next step")
        ]
