"""Welcome scene widget for STIMULUS onboarding."""

from pathlib import Path

from stimulus_onboarding.scripting import Gradient, Type, Wait, WaitForInput
from stimulus_onboarding.script_runner import ScriptedScene

# Load welcome text from file
assets_dir = Path(__file__).parent / "assets"
welcome_file = assets_dir / "welcome.txt"


class WelcomeScene(ScriptedScene):
    """Welcome banner scene for the onboarding experience."""

    def build_script(self):
        return [
            # "Welcome to "
            Type("Welcome to ", speed=0.08),
            
            # "STIMULUS" (gradient, paused for effect)
            Gradient("STIMULUS"),
            Wait(1.4),
            
            # Rest of the intro
            Type("\n\n" + welcome_file.read_text().strip(), speed=0.03),
            
            # Nav hint (wait 0.5s then show)
            Wait(0.5),
            
            WaitForInput(prompt="Press Enter ↵ to continue, Esc or Ctrl+C to exit")
        ]
