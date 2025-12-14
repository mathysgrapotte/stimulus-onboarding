"""Data configuration scene widget for STIMULUS onboarding."""

from pathlib import Path

from stimulus_onboarding.scripting import DisplayYaml, Type, WaitForInput
from stimulus_onboarding.script_runner import ScriptedScene

# Asset paths
assets_dir = Path(__file__).parent / "assets"


class DataConfigScene(ScriptedScene):
    """Data configuration scene for the onboarding experience."""

    def build_script(self):
        return [
            # Part 1
            Type(assets_dir / "data-config-part-1.txt"),
            WaitForInput(key="down", prompt="press ↓ to continue"),
            
            # Part 2
            Type(assets_dir / "data-config-part-2-pre.txt"),
            WaitForInput(key="down", prompt="press ↓ to continue"),
            DisplayYaml(Path("data/split.yaml")),
            WaitForInput(key="down", prompt="press ↓ to continue"),
            Type(assets_dir / "data-config-part-2-post.txt"),
            WaitForInput(prompt="Press Enter ↵ to continue to next step")
        ]
