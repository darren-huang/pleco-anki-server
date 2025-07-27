"""Utility functions for the Pleco Anki Server project."""
import unicodedata
import glob
import regex as re


def find_file_with_wildcard(pattern):
    """Find file with wildcard pattern, raise error if no match or multiple matches."""
    # Use glob to find matching files
    matching_files = glob.glob(pattern)

    # Check if no file was found
    if len(matching_files) == 0:
        raise FileNotFoundError(f"No files found matching pattern: {pattern}")

    # Check if more than one file was found
    if len(matching_files) > 1:
        raise ValueError(f"Multiple files found matching pattern: {pattern}")

    # Return the matched file path
    return matching_files[0]


def fullwidth_to_ascii(text):
    """Convert fullwidth characters to their ASCII equivalents."""
    return "".join(unicodedata.normalize("NFKC", char) for char in text)


def overlap_length(chinese: str, english: str) -> int:
    """Calculate the length of overlapping trailing characters between Chinese and English text."""
    # Match all trailing non-Han characters from the Chinese string
    match = re.search(r".*[\p{Han}]", chinese)
    if match:
        non_chinese_suffix = chinese[match.end() :]  # Get trailing non-Han portion
    else:
        non_chinese_suffix = chinese  # Entire string is non-Han

    # Check how much of this suffix matches the start of the English string
    overlap = 0
    for i in range(1, len(non_chinese_suffix) + 1):
        if english.startswith(non_chinese_suffix[-i:]):
            overlap = i

    return overlap
