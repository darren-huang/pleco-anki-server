from enum import Enum


class ToneColor(Enum):
    RED = "#E30000"
    GREEN = "#02B31C"
    PURPLE = "#8900BF"
    BLUE = "#1510F0"
    GREY = "#777777"  # Neutral tone


def get_pinyin_color(pinyin):
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
