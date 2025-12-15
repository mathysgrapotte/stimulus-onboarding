"""Stimulus run scene widget for STIMULUS onboarding."""

from pathlib import Path

from stimulus_onboarding.scripting import Terminal, WaitForInput, Type, DisplayPython, DisplayYaml
from stimulus_onboarding.script_runner import ScriptedScene

# Asset paths
assets_dir = Path(__file__).parent / "assets"

# Commands
INSTALL_COMMAND = "uv pip install git+https://github.com/mathysgrapotte/stimulus-py.git@h5ad-support"
SPLIT_COMMAND = "stimulus split --data data/vcc_training_subset.h5ad --yaml data/split.yaml --output output/vcc_split"
LS_COMMAND = "ls -lh output/vcc_split"
ANALYSIS_COMMAND = "uv run stimulus_onboarding/case_study_analysis/analyze_splits.py"


class StimulusModelFileScene(ScriptedScene):
    """Scene for installing and running STIMULUS."""

    def build_script(self):
        return [
            # Part 1: Model File intro
            Type(assets_dir / "train-model-part-1.txt"),
            WaitForInput(key="down", prompt="press ↓ to continue"),

            # Part 2: __init__ constructor
            Type(assets_dir / "train-model-part-2.txt"),
            WaitForInput(key="down", prompt="press ↓ to continue"),
            DisplayPython(Path(__file__).parent / "assets" / "model-file.py"),
            WaitForInput(key="down", prompt="press ↓ to continue"),

            # Part 3: __init__ explained
            Type(assets_dir / "train-model-part-3.txt"),
            WaitForInput(key="down", prompt="press ↓ to continue"),
            DisplayYaml(Path(__file__).parent / "assets" / "model-network-params.yaml"),
            WaitForInput(key="down", prompt="press ↓ to continue"),
            Type(assets_dir / "train-model-part-4.txt"),
            WaitForInput(key="down", prompt="press ↓ to continue"),

            # Part 4: Training functions
            DisplayPython(Path(__file__).parent / "assets" / "model-file-with-functions.py"),
            WaitForInput(key="down", prompt="press ↓ to continue"),
            Type(assets_dir / "train-model-part-5.txt"),
            WaitForInput(key="down", prompt="press ↓ to continue"),
            DisplayYaml(Path(__file__).parent / "assets" / "model-optimizer-optuna.yaml"),
            WaitForInput(key="down", prompt="press ↓ to continue"),
            Type(assets_dir / "train-model-part-6.txt"),

            WaitForInput(prompt="Press Enter ↵ to continue")
        ]
