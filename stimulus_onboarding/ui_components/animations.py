"""Animation helpers for UI components."""

# Gradient colors for STIMULUS (orange theme matching nextflow-vibe)
GRADIENT_COLORS = [
    "#ff6b00",
    "#ff7b00",
    "#ff8c00",
    "#ff9d00",
    "#ffae00",
    "#ffbf00",
    "#ffae00",
    "#ff9d00",
    "#ff8c00",
    "#ff7b00",
]


def apply_gradient(text: str, offset: int) -> str:
    """Apply cycling gradient colors to text."""
    result = []
    for i, char in enumerate(text):
        color = GRADIENT_COLORS[(i + offset) % len(GRADIENT_COLORS)]
        result.append(f"[bold {color}]{char}[/]")
    return "".join(result)
