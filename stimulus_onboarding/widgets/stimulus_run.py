"""Stimulus run scene widget for STIMULUS onboarding."""

from pathlib import Path

from stimulus_onboarding.scripting import Terminal, WaitForInput, Type
from stimulus_onboarding.script_runner import ScriptedScene

# Asset paths
assets_dir = Path(__file__).parent / "assets"

# Commands
INSTALL_COMMAND = "uv pip install git+https://github.com/mathysgrapotte/stimulus-py.git@h5ad-support"
SPLIT_COMMAND = "stimulus split --data data/vcc_training_subset.h5ad --yaml data/split.yaml --output output/vcc_split"
LS_COMMAND = "ls -lh output/vcc_split"
ANALYSIS_COMMAND = "uv run stimulus_onboarding/case_study_analysis/analyze_splits.py"


class StimulusRunScene(ScriptedScene):
    """Scene for installing and running STIMULUS."""

    def build_script(self):
        return [
            # Part 1: Intro & Install
            Type(assets_dir / "stimulus-run-part-1.txt", speed=0.03),
            Terminal(command=INSTALL_COMMAND),
            
            # Part 2: Split
            Type(assets_dir / "stimulus-run-part-2.txt", speed=0.03),
            Terminal(command=SPLIT_COMMAND),
            
            # Part 3: List files
            Type(assets_dir / "stimulus-run-part-3.txt", speed=0.03),
            Terminal(command=LS_COMMAND),
            
            # Part 4: Analysis
            Type(assets_dir / "stimulus-run-part-4.txt", speed=0.03),
            Terminal(command=ANALYSIS_COMMAND),
            
            # Part 5: Conclusion
            Type(assets_dir / "stimulus-run-part-5.txt", speed=0.03),
            WaitForInput(prompt="Press Enter ↵ to continue")
        ]
