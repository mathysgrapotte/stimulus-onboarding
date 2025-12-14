"""Data configuration scene widget for STIMULUS onboarding."""

from pathlib import Path

from stimulus_onboarding.scripting import Display, WaitForInput
from stimulus_onboarding.script_runner import ScriptedScene

# Asset paths
assets_dir = Path(__file__).parent / "assets"


class DataConfigScene(ScriptedScene):
    """Data configuration scene for the onboarding experience."""

    def build_script(self):
        return [
            # Part 1
            Display(assets_dir / "data-config-part-1.txt"),
            WaitForInput(key="down", prompt="press ↓ to continue"),
            
            # Part 2
            Display(assets_dir / "data-config-part-2.txt"),
            WaitForInput(prompt="Press Enter ↵ to continue to next step")
        ]
