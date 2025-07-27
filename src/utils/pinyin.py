"""Utilities for handling Chinese pinyin, including tone processing and conversion functions."""

import csv
import functools
from collections import defaultdict
from enum import Enum

import regex as re

from src.utils.resource_utils import get_resource_path

SKIPPABLE_LEFTOVER_PINYIN = [".", ","]
KEEPABLE_PINYIN_PUNC = ["'", "-", "·"]

# Cache for fifth tone pinyin list
_FIFTH_TONE_PINYIN_CACHE = None


def get_fifth_tone_pinyins():
    """
    Get the list of fifth tone pinyin syllables from CEDICT.
    Uses caching to avoid repeated file reads.

    Returns:
        list: List of fifth tone pinyin syllables
    """
    global _FIFTH_TONE_PINYIN_CACHE  # pylint: disable=global-statement
    if _FIFTH_TONE_PINYIN_CACHE is None:
        cedict_path = get_resource_path(CEDICT_FILENAME)
        _FIFTH_TONE_PINYIN_CACHE = sorted(extract_fifth_tone_pinyin(cedict_path))
    return _FIFTH_TONE_PINYIN_CACHE


CONVERT_PUNC_DICT = {
    "。": ".",
    "！": "!",
    "？": "?",
    "，": ",",
    "；": ";",
    "：": ":",
    "《": "«",
    "》": "»",
}
CEDICT_FILENAME = "cedict_ts.u8"


class ToneColor(Enum):
    RED = "#E30000"
    GREEN = "#02B31C"
    PURPLE = "#8900BF"
    BLUE = "#1510F0"
    GREY = "#777777"  # Neutral tone


def get_pinyin_color(pinyin):
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


def extract_fifth_tone_pinyin(file_path):
    """Extract fifth tone pinyin syllables from the CEDICT file."""
    fifth_tone_pinyin = set()  # Use a set to avoid duplicates
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            # Skip comments
            if line.startswith("#"):
                continue
            # Parse the line: format is "汉字 [han4 zi5] /meaning/"
            parts = re.findall(r"\[(.*?)\]", line)
            for pinyin in parts:
                for syllable in re.split(r"(?<=\d)\s*|\s+", pinyin):
                    if syllable.endswith("5"):
                        syllable = re.sub(r"[^a-z]", "", syllable.lower())
                        if syllable:
                            fifth_tone_pinyin.add(syllable)
    return fifth_tone_pinyin


def extract_toneless_pinyin(file_path):
    """Extract toneless pinyin syllables from the CEDICT file."""
    toneless_pinyin = set()  # Use a set to avoid duplicates
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            # Skip comments
            if line.startswith("#"):
                continue
            # Parse the line: format is "汉字 [han4 zi5] /meaning/"
            parts = re.findall(r"\[(.*?)\]", line)
            for pinyin in parts:
                for syllable in re.split(r"(?<=\d)\s*|\s+", pinyin):
                    syllable = re.sub(r"[^a-z]", "", syllable.lower())
                    if syllable:
                        toneless_pinyin.add(syllable)
    return toneless_pinyin


class TrieNode:
    """Node class for Trie data structure."""

    def __init__(self):
        self.children = {}
        self.is_end_of_word = False


class Trie:
    """Trie data structure for efficient prefix matching."""

    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        """Insert a word into the Trie."""
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True

    def get_longest_length(self, word, i):
        """Get the length of the longest prefix in the Trie starting from index i."""
        node = self.root
        longest_length = 0
        current_length = 0

        for char in word[i:]:
            if char in node.children:
                node = node.children[char]
                current_length += 1
                if node.is_end_of_word:
                    longest_length = current_length
            else:
                break

        return longest_length


def create_trie_from_pinyin(pinyin_set):
    """Create a Trie from a set of pinyin strings."""
    trie = Trie()
    for pinyin in pinyin_set:
        trie.insert(pinyin.lower().strip())
    return trie


def convert_pinyin(pinyin):
    """Convert numbered pinyin to pinyin with tone marks."""
    tone_marks = {
        "a": "āáǎàa",
        "e": "ēéěèe",
        "i": "īíǐìi",
        "o": "ōóǒòo",
        "u": "ūúǔùu",
        "ü": "ǖǘǚǜü",
        "A": "ĀÁǍÀA",
        "E": "ĒÉĚÈE",
        "I": "ĪÍǏÌI",
        "O": "ŌÓǑÒO",
        "U": "ŪÚǓÙU",
        "Ü": "ǕǗǙǛÜ",
    }
    result = []

    prev = False
    # prev_ends_with_vowel = False
    for syllable in re.split(r"(?<=\d)(?=\D)", pinyin):
        starts_with_vowel = syllable[0] in "aeiouü"
        if syllable[-1].isdigit():
            tone = int(syllable[-1])
            syllable = syllable[:-1]
            if "a" in syllable.lower():
                syllable = re.sub("a", tone_marks["a"][tone - 1], syllable)
                syllable = re.sub("A", tone_marks["A"][tone - 1], syllable)
            elif "e" in syllable.lower():
                syllable = re.sub("e", tone_marks["e"][tone - 1], syllable)
                syllable = re.sub("E", tone_marks["E"][tone - 1], syllable)
            elif "ou" in syllable.lower():
                syllable = re.sub("o", tone_marks["o"][tone - 1], syllable)
                syllable = re.sub("O", tone_marks["O"][tone - 1], syllable)
            else:
                for letter in reversed(syllable):
                    if letter.lower() in "iouüIOUÜ":
                        syllable = syllable.replace(
                            letter, tone_marks[letter][tone - 1]
                        )
                        break
        if prev and starts_with_vowel:
            syllable = "'" + syllable
        prev = True
        result.append(syllable)
    return result


@functools.lru_cache(maxsize=None)  # Infinite cache size
def parse_cedict_toneless_pinyins(filename="cedict_ts.u8"):
    """Parse cedict_ts.u8 and extract a dictionary mapping Chinese characters to toneless Pinyin."""
    char_to_pinyin = defaultdict(set)

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue  # Skip comment lines

            parts = line.split()
            if len(parts) < 3:
                continue  # Skip malformed lines

            traditional, simplified, *pinyin_parts = parts

            pinyin_bracket_match = re.search(r"\[(.*?)\]", line)
            if not pinyin_bracket_match:
                continue

            pinyin_string = re.sub(
                r"[^A-Za-z ü]", "", pinyin_bracket_match.group(1).replace("u:", "ü")
            )
            pinyin_with_tones = pinyin_string.split()
            pinyin_toneless = [p for p in pinyin_with_tones]

            for char, pinyin_ in zip(traditional, pinyin_toneless):
                char_to_pinyin[char].add(pinyin_.lower())
                if pinyin_ == "-":
                    print(line)

    return char_to_pinyin


@functools.lru_cache(maxsize=None)  # Infinite cache size
def load_manual_pinyins(filename="manual_pinyins.csv"):
    """Parses manual_pinyins.csv to extract bidirectional variant mappings."""
    pinyins = {}

    with open(filename, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)

        next(reader)  # Skip the header row
        for row in reader:
            if len(row) < 2:
                continue  # Skip malformed rows

            pinyins.setdefault(row[0], set()).add(
                row[1]
            )  # add the pinyin to the set of pinyins for this character

    return pinyins


def strip_tone_marks(pinyin_with_tone):
    """
    Removes tone marks from pinyin to get the base pinyin (5th tone equivalent).
    Handles both lowercase and uppercase vowels with tone marks.

    Args:
        pinyin_with_tone (str): Pinyin with tone marks

    Returns:
        str: Pinyin without tone marks
    """
    # Map of vowels with tone marks to base vowels (lowercase)
    tone_marks_map_lower = {
        "ā": "a",
        "á": "a",
        "ǎ": "a",
        "à": "a",
        "ē": "e",
        "é": "e",
        "ě": "e",
        "è": "e",
        "ī": "i",
        "í": "i",
        "ǐ": "i",
        "ì": "i",
        "ō": "o",
        "ó": "o",
        "ǒ": "o",
        "ò": "o",
        "ū": "u",
        "ú": "u",
        "ǔ": "u",
        "ù": "u",
        "ǖ": "ü",
        "ǘ": "ü",
        "ǚ": "ü",
        "ǜ": "ü",
        "ü": "ü",
    }

    # Map of vowels with tone marks to base vowels (uppercase)
    tone_marks_map_upper = {
        "Ā": "A",
        "Á": "A",
        "Ǎ": "A",
        "À": "A",
        "Ē": "E",
        "É": "E",
        "Ě": "E",
        "È": "E",
        "Ī": "I",
        "Í": "I",
        "Ǐ": "I",
        "Ì": "I",
        "Ō": "O",
        "Ó": "O",
        "Ǒ": "O",
        "Ò": "O",
        "Ū": "U",
        "Ú": "U",
        "Ǔ": "U",
        "Ù": "U",
        "Ǖ": "Ü",
        "Ǘ": "Ü",
        "Ǚ": "Ü",
        "Ǜ": "Ü",
        "Ü": "Ü",
    }

    # Combine both maps
    tone_marks_map = {**tone_marks_map_lower, **tone_marks_map_upper}

    result = ""
    for char in pinyin_with_tone:
        result += tone_marks_map.get(char, char)

    return result
