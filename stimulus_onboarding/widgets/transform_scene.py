"""Transform scene widget for STIMULUS onboarding."""

from pathlib import Path

from stimulus_onboarding.scripting import DisplayYaml, Terminal, Type, WaitForInput
from stimulus_onboarding.script_runner import ScriptedScene

# Asset paths
assets_dir = Path(__file__).parent / "assets"

# Command
TRANSFORM_COMMAND = "stimulus transform --data output/vcc_split --yaml data/transform_2000.yaml --output output/vcc_2000"


class TransformScene(ScriptedScene):
    """Scene for transforming data."""

    def build_script(self):
        return [
            # Step 1: Intro
            Type(assets_dir / "transform-intro-pre.txt"),
            WaitForInput(key="down", prompt="press ↓ to continue"),
            DisplayYaml(Path("data/transform_2000.yaml")),
            Type(assets_dir / "transform-intro-post.txt"),
            
            # Step 2: Interactive Command
            Terminal(command=TRANSFORM_COMMAND),
            
            # Step 3: Result and Exit
            Type(assets_dir / "transform-run.txt"),
            WaitForInput(prompt="Press Enter ↵ to continue")
        ]
