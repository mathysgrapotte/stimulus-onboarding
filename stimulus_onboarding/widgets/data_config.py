"""Data configuration scene widget for STIMULUS onboarding."""

from pathlib import Path

from stimulus_onboarding.scripting import WaitForInput, Type
from stimulus_onboarding.script_runner import ScriptedScene

# Asset paths
assets_dir = Path(__file__).parent / "assets"


class DataConfigScene(ScriptedScene):
    """Data configuration scene for the onboarding experience."""

    def build_script(self):
        return [
            # Part 1
            Type(assets_dir / "data-config-part-1.txt", speed=0.03),
            WaitForInput(key="down", prompt="press ↓ to continue"),
            
            # Part 2
            Type(assets_dir / "data-config-part-2.txt", speed=0.03),
            WaitForInput(prompt="Press Enter ↵ to continue to next step")
        ]
