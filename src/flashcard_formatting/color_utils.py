"""Color utilities for handling pinyin tone colors in Chinese text."""

from enum import Enum


class ToneColor(Enum):
    """Enum defining color codes for different pinyin tones."""

    RED = "#E30000"
    GREEN = "#02B31C"
    PURPLE = "#8900BF"
    BLUE = "#1510F0"
    GREY = "#777777"  # Neutral tone


def get_pinyin_color(pinyin):
    """
    Get the color for a pinyin based on its tone.

    Args:
        pinyin (str): The pinyin text with tone marks

    Returns:
        str: The hex color code for the tone
    """
    tone_map = {
        "āēīōūǖĀĒĪŌŪǕ": ToneColor.RED,
        "áéíóúǘÁÉÍÓÚǗ": ToneColor.GREEN,
        "ǎěǐǒǔǚǍĚǏǑǓǙ": ToneColor.BLUE,
        "àèìòùǜÀÈÌÒÙǛ": ToneColor.PURPLE,
    }

    tone_color = ToneColor.GREY  # Default to neutral tone
    for chars, t in tone_map.items():
        if any(char in pinyin for char in chars):
            tone_color = t
            break

    return tone_color.value
