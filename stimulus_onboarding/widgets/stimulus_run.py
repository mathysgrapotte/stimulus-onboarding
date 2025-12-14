"""Stimulus run scene widget for STIMULUS onboarding."""

from pathlib import Path

from stimulus_onboarding.scripting import Display, Terminal, WaitForInput
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
            Display(assets_dir / "stimulus-run-part-1.txt"),
            Terminal(command=INSTALL_COMMAND),
            
            # Part 2: Split
            Display(assets_dir / "stimulus-run-part-2.txt"),
            Terminal(command=SPLIT_COMMAND),
            
            # Part 3: List files
            Display(assets_dir / "stimulus-run-part-3.txt"),
            Terminal(command=LS_COMMAND),
            
            # Part 4: Analysis
            Display(assets_dir / "stimulus-run-part-4.txt"),
            Terminal(command=ANALYSIS_COMMAND),
            
            # Part 5: Conclusion
            Display(assets_dir / "stimulus-run-part-5.txt"),
            WaitForInput(prompt="Press Enter ↵ to continue")
        ]
