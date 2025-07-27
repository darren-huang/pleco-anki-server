"""Utilities for handling file operations, including JSON loading/saving and Unicode conversions."""

import json
import html


def convert_unicode_segments(text):
    """Convert unicode segments (like &#33368;) to the actual unicode character."""
    return html.unescape(text)


def load_flashcard_entries(file_path="flashcard_entries.json"):
    """Load flashcard entries from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_flashcard_entries(entries, file_path="flashcard_entries.json"):
    """Save flashcard entries to a JSON file."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=4)
