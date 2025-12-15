"""Tune scene widget for STIMULUS onboarding."""

from pathlib import Path

from stimulus_onboarding.scripting import Terminal, Type, WaitForInput
from stimulus_onboarding.script_runner import ScriptedScene

# Asset paths
assets_dir = Path(__file__).parent / "assets"

# Command
TUNE_COMMAND = (
    "stimulus tune "
    "--data output/vcc_2000 "
    "--model-config data/pca_reconstruction_config.yaml "
    "--model data/pca_reconstructor.py "
    "--optuna-results-dirpath output/pca_reconstruction "
    "--output output/pca_reconstruction/best_model.safetensors"
)


class TuneScene(ScriptedScene):
    """Final scene that runs stimulus tune."""

    def build_script(self):
        return [
            Type(assets_dir / "tune-intro.txt"),
            Terminal(command=TUNE_COMMAND),
            Type(assets_dir / "tune-complete.txt"),
            WaitForInput(prompt="Press Enter ↵ to finish onboarding")
        ]
