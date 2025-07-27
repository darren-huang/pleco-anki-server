"""Color mapping utilities for Chinese pinyin tones."""

from enum import Enum


class ToneColor(Enum):
    """Enum defining color codes for different pinyin tones."""

    RED = "#E30000"
    GREEN = "#02B31C"
    PURPLE = "#8900BF"
    BLUE = "#1510F0"
    GREY = "#777777"  # Neutral tone


def get_pinyin_color(pinyin):
    """Get the color code for a pinyin string based on its tone marks.

    Args:
        pinyin: String containing pinyin with tone marks

    Returns:
        str: Hex color code for the tone
    """
    tone_map = {
        "āēīōūǖ": ToneColor.RED,
        "áéíóúǘ": ToneColor.GREEN,
        "ǎěǐǒǔǚ": ToneColor.PURPLE,
        "àèìòùǜ": ToneColor.BLUE,
    }

    tone_color = ToneColor.GREY  # Default to neutral tone
    for chars, t in tone_map.items():
        if any(char in pinyin for char in chars):
            tone_color = t
            break

    return tone_color.value
