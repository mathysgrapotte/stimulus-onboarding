"""Text processing utilities for typed content rendering."""


import re
from pathlib import Path

# Markers for YAML block detection
YAML_BLOCK_START = "{{YAML_START}}"
YAML_BLOCK_END = "{{YAML_END}}"


def fix_incomplete_markup(text: str) -> str:
    """Fix incomplete Rich markup tags at the end of a string.

    When typing text character by character, we might cut off a tag like
    [bold blue] or [/]. This function detects such cases and either:
    1. Removes the partial tag if it's opening
    2. Completes the partial tag if it's closing (conceptually, though
       we actually just strip partial tags typically)

    Actually, for a typing effect, it's often safer to strip any partial
    tag at the very end.
    """
    # If text ends with an incomplete tag like "[bold", remove it
    if "[" in text and "]" not in text.split("[")[-1]:
        return text.rsplit("[", 1)[0]
    return text


def format_yaml_preview(yaml_path: str, params_project_root: Path) -> str:
    """Format YAML file with Rich markup in a bordered preview box.
    
    Args:
        yaml_path: Relative path to the yaml file from project root.
        params_project_root: Path object pointing to the project root.
    """
    yaml_file = params_project_root / yaml_path
    if not yaml_file.exists():
        return f"[red]File not found: {yaml_path}[/]"
        
    yaml_text = yaml_file.read_text().strip()

    # Modern color scheme (One Dark inspired)
    border_color = "#3e4451"
    title_color = "#61afef"
    key_color = "#e06c75"
    string_color = "#98c379"
    number_color = "#d19a66"
    punctuation_color = "#c678dd"

    # Box drawing characters (round style)
    box_width = 44
    title = f" {yaml_path} "
    title_padding = (box_width - 2 - len(title)) // 2

    lines = []
    # Top border with centered title
    top_left = "─" * title_padding
    top_right = "─" * (box_width - 2 - title_padding - len(title))
    lines.append(f"[{border_color}]╭{top_left}[/][bold {title_color}]{title}[/][{border_color}]{top_right}╮[/]")

    # Content lines
    for line in yaml_text.split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            indent = len(key) - len(key.lstrip())
            key = key.strip()
            value = value.strip()

            if value:
                # Determine value type for coloring
                if value.startswith('"') or value.startswith("'"):
                    value_formatted = f"[{string_color}]{value}[/]"
                elif value.isdigit() or value.replace(".", "").isdigit():
                    value_formatted = f"[{number_color}]{value}[/]"
                else:
                    value_formatted = f"[{string_color}]{value}[/]"
                content = f"{'  ' * (indent // 2)}[{key_color}]{key}[/][{border_color}]:[/] {value_formatted}"
            else:
                content = f"{'  ' * (indent // 2)}[{key_color}]{key}[/][{border_color}]:[/]"
        elif line.strip().startswith("-"):
            indent = len(line) - len(line.lstrip())
            item = line.strip()[1:].strip()
            content = f"{'  ' * (indent // 2)}[{punctuation_color}]-[/] [{string_color}]{item}[/]"
        else:
            content = line

        lines.append(f"[{border_color}]│[/]  {content}")

    # Bottom border
    lines.append(f"[{border_color}]╰{'─' * (box_width - 2)}╯[/]")

    # Wrap with markers for speed detection
    return YAML_BLOCK_START + "\n".join(lines) + YAML_BLOCK_END


def process_text_placeholders(text: str, project_root: Path) -> str:
    """Process {{italic:...}} and {{yaml:...}} placeholders in text."""
    # Process italic placeholders
    text = re.sub(
        r"\{\{italic:(.*?)\}\}",
        r"[italic dim]\1[/]",
        text,
        flags=re.DOTALL,
    )

    # Process yaml placeholders
    def yaml_replacer(match: re.Match) -> str:
        yaml_path = match.group(1)
        return format_yaml_preview(yaml_path, project_root)

    text = re.sub(r"\{\{yaml:(.*?)\}\}", yaml_replacer, text)

    return text
