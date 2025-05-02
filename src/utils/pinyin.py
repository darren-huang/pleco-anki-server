from enum import Enum
import regex as re


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


# Make use of cc-cedict to extract pinyin info


def extract_fifth_tone_pinyin(file_path):
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
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True

    def get_longest_length(self, word, i):
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
    trie = Trie()
    for pinyin in pinyin_set:
        trie.insert(pinyin.lower().strip())
    return trie
