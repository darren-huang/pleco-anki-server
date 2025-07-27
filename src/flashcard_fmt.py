#!/usr/bin/env python3

import os
import re
from flashcard_formatting.format_entry import fmt_entry, grade_fmt_entry
from utils.file_utils import save_flashcard_entries
from utils.google_drive_utils import get_latest_flashcard_xml
from flashcard_formatting.flashcard_xml import process_flashcard_xml
from utils.anki_connect import get_card_info
from utils.html import convert_unicode_segments


def main():
    """
    Main function to process and format flashcard entries.
    """
    # Change to resources directory for file operations
    os.chdir("resources")

    # Get latest flashcard XML from Google Drive
    xml_text = get_latest_flashcard_xml()
    if xml_text:
        # Process XML to get flashcard entries
        flashcard_entries, error_entries = process_flashcard_xml(xml_text)
        print(
            len(flashcard_entries),
            "flashcard entries found|",
            len(error_entries),
            "error entries found",
        )

        # Get Anki card information
        anki_cards = get_card_info("Pleco Import")
        anki_cards_dict = {
            re.sub(r"[^\u4e00-\u9fff]", "", card["fields"]["Front"]["value"]): card
            for card in anki_cards
        }

        # Add formatted back and pinyin from Anki
        for entry in flashcard_entries:
            anki_card = anki_cards_dict.get(entry["traditional"])
            if anki_card:
                entry["formatted_back"] = convert_unicode_segments(
                    anki_card["fields"]["Back"]["value"]
                )
                entry["anki_pinyin"] = convert_unicode_segments(
                    anki_card["fields"]["pinyin"]["value"]
                )

        # Save the processed entries
        save_flashcard_entries(flashcard_entries)

        # Format entries and check for errors
        formatted_entries = []
        for entry in flashcard_entries:
            formatted_back = fmt_entry(entry)
            entry["formatted_back"] = formatted_back
            formatted_entries.append(entry)

        # Save the formatted entries
        save_flashcard_entries(formatted_entries)

        # Grade the formatting results
        print("\nGrading format results:")
        grade_fmt_entry(formatted_entries)
    else:
        print("No flashcard XML found or error retrieving from Google Drive")


if __name__ == "__main__":
    main()
