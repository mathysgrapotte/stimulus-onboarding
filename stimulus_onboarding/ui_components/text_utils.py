"""Text processing utilities for typed content rendering."""


def fix_incomplete_markup(text: str) -> str:
    """Remove incomplete Rich markup tags from truncated text.

    When text is being typed character-by-character, markup tags like
    [bold] may be cut off mid-tag. This function removes such incomplete tags.
    """
    while text.count("[") > text.count("]"):
        if (last_open := text.rfind("[")) == -1:
            break
        text = text[:last_open]
    return text
