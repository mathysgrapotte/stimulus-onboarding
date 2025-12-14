"""Widgets for the STIMULUS onboarding TUI."""

from stimulus_onboarding.widgets.case_study import CaseStudyScene
from stimulus_onboarding.widgets.data_config import DataConfigScene
from stimulus_onboarding.widgets.stimulus_run import StimulusRunScene
from stimulus_onboarding.widgets.transform_scene import TransformScene
from stimulus_onboarding.widgets.welcome import WelcomeScene

__all__ = [
    "CaseStudyScene",
    "DataConfigScene",
    "StimulusRunScene",
    "TransformScene",
    "WelcomeScene",
]
