"""UI components package."""

from stimulus_onboarding.ui_components.action_menu import ActionMenu
from stimulus_onboarding.ui_components.animations import (
    GRADIENT_COLORS,
    apply_gradient,
    cycle_gradient_offset,
)
from stimulus_onboarding.ui_components.terminal import TerminalWidget
from stimulus_onboarding.ui_components.text_utils import fix_incomplete_markup
from stimulus_onboarding.ui_components.typing import TYPING_SPEED, stop_timer_safely

__all__ = [
    "ActionMenu",
    "GRADIENT_COLORS",
    "apply_gradient",
    "cycle_gradient_offset",
    "TerminalWidget",
    "fix_incomplete_markup",
    "TYPING_SPEED",
    "stop_timer_safely",
]
