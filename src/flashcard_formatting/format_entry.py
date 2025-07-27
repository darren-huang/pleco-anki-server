"""Module for formatting dictionary entries into HTML-formatted Anki flashcards."""

import re

from src.flashcard_formatting.color_utils import get_pinyin_color
from src.flashcard_formatting.html_utils import (
    fix_separated_pos_tags,
    reorder_bold_and_color_spans,
)
from src.flashcard_formatting.label_segments import label_segments


def fmt_entry(entry):
    """
    Format a dictionary entry into HTML for Anki flashcard display.

    Args:
        entry (dict): Dictionary containing entry information with keys:
            - traditional: Traditional Chinese characters
            - simplified: Simplified Chinese characters
            - pinyin: List of pinyin strings
            - definition: English definition

    Returns:
        str: Formatted HTML for the flashcard back
    """
    traditional = entry.get("traditional", "")
    simplified = entry.get("simplified", "")
    pinyin = entry.get("pinyin", "")
    definition = entry.get("definition", "")
    simplified_hint = f"〔{simplified}〕" if traditional != simplified else ""

    formatted_back = ""
    formatted_back += f'<div align="left"><p><span style="font-size:32px">{traditional}{simplified_hint}</span><br/>\n'
    formatted_back += '<span style="color:#B4B4B4;"><b><span style="font-size:0.80em;">PY </span></b></span>'

    # pinyin
    for p in pinyin:
        starters = ["//", " ", "-", "→"]
        while any([p.startswith(s) for s in starters]):
            for s in starters:
                if p.startswith(s):
                    formatted_back += f'<span style="font-weight:600;">{s}</span>'
                    p = p.replace(s, "", 1)
        formatted_back += f'<span style="color:{get_pinyin_color(p)};"><span style="font-weight:600;">{p}</span></span>'

    # part of speech
    formatted_back += '</p>\n</div><div align="left"><p>'

    last_label = None
    for segment in label_segments(definition, traditional_word=traditional):
        if segment["label"] == "part of speech":
            if last_label == "example_sentence":
                formatted_back += "<br/>\n</p>\n</blockquote>\n<p><br/>\n"
            elif last_label == "part of speech":
                formatted_back += "<br/>\n"
            elif last_label == "english":
                formatted_back += "</p>\n<p>"
            formatted_back += f'<b><span style="font-size:0.80em;"><span style="color:#B4B4B4;">{segment["segment"].upper().strip()}</span></span></b>'

        elif segment["label"] == "english":
            # process transition
            if last_label == "part of speech":
                formatted_back += "<br/>\n"
            # add english segment
            formatted_back += segment["segment"].strip()

        elif segment["label"] == "example_sentence":
            # process transition
            if last_label == "english":
                formatted_back += "<br/>\n</p>\n"
            elif last_label == "example_sentence":
                formatted_back += "<br/>\n</p>\n</blockquote>\n"

            # process example sentence
            formatted_back += '<blockquote style="border-left: 2px solid #0078c3; margin-left: 3px; padding-left: 1em; margin-top: 0px; margin-bottom: 0px;"><p>'
            # chinese
            for ex_seg in segment["chinese_list_w_bold_labels"]:
                formatted_back += '<span style="color:#0078C3;">'
                if ex_seg["bold"]:
                    formatted_back += f'<b>{ex_seg["segment"]}</b>'
                else:
                    formatted_back += ex_seg["segment"]
                formatted_back += "</span>"
            formatted_back += "<br/>\n"
            # pinyin
            pinyin_punc_to_bold = set(["？"])
            for ex_seg in segment["pinyin_list_w_bold_labels"]:
                if not ex_seg["segment"]:
                    continue
                if ex_seg["bold"] or ex_seg["segment"] in pinyin_punc_to_bold:
                    formatted_back += f'<b>{ex_seg["segment"]}</b>'
                else:
                    formatted_back += (
                        f'<span style="font-weight:600;">{ex_seg["segment"]}</span>'
                    )
            formatted_back += "<br/>\n"
            # english
            formatted_back += segment["english"].strip()

        elif segment["label"] == "item_number":
            if last_label:
                formatted_back += "<br/>\n"
            if last_label == "example_sentence":
                formatted_back += "</p>\n</blockquote>\n<p>"
            formatted_back += f'<b>{segment["segment"].strip()}\t</b>'

        last_label = segment["label"]

    # final
    formatted_back += "</p>"
    if last_label == "example_sentence":
        formatted_back += "\n</blockquote>"

    formatted_back += "\n</div>"

    # Special formatting for variant notes
    formatted_back = re.sub(
        r"VARIANT OF \uead1\ueada\d+\uead8(\p{Han}+)\uead9[\d\w]+\uead0\p{Han}+\uead2 ",
        r'<span style="color:#B4B4B4;"><b><span style="font-size:0.80em;">VARIANT OF </span></b></span>\1<br/>\n',
        formatted_back,
    )
    formatted_back = formatted_back.replace(") a surname", ")<br/>\na surname")

    return formatted_back


def drop(arr, to_drop):
    """
    Remove items at specified indices from a list.

    Args:
        arr (list): The input list
        to_drop (list): List of indices to remove

    Returns:
        list: A new list with the specified items removed
    """
    arr = arr.copy()
    for i in to_drop:
        arr.pop(i)
    return arr


def grade_fmt_entry(
    flashcard_entries,
    n_error_char_show=10,
    to_drop=None,
    stop_at_fail=False,
    print_at_fail=False,
):
    """
    Compare formatted entries with expected output and report differences.

    Args:
        flashcard_entries (list): List of flashcard entries to check
        n_error_char_show (int): Number of characters to show in error messages
        to_drop (list): List of indices to skip
        stop_at_fail (bool): Whether to stop at first failure
        print_at_fail (bool): Whether to print details at failure
    """
    if to_drop is None:
        to_drop = []

    flashcard_entries = drop(flashcard_entries, to_drop)
    correct_count = 0
    length_diff_count = 0
    wrong_count = 0

    for i, entry in enumerate(flashcard_entries):
        expected = entry["formatted_back"]
        expected = expected.replace(' ;=""', ";")
        expected = reorder_bold_and_color_spans(expected)
        expected = re.sub(r"<plecoentry.*?</plecoentry>$", "", expected)
        expected = expected.replace("\xa0", " ")
        expected = fix_separated_pos_tags(expected)
        result = fmt_entry(entry)
        result = re.sub(
            r" See \uead1\ueada\d+\uead8\p{Han}+\uead9[\w\d]+\uead0\p{Han}+\uead2",
            "",
            result,
        )

        if expected != result and re.sub(r"[()]", "", expected) != re.sub(
            r"[()]", "", result
        ):
            for j in range(min(len(expected), len(result))):
                if expected[j] != result[j]:
                    wrong_count += 1
                    if stop_at_fail or print_at_fail:
                        print("{i} wrd:", repr(entry["traditional"]))
                        print(f"Exp: {repr(expected[j:j + n_error_char_show])}...")
                        print(f"Got: {repr(result[j:j + n_error_char_show])}...")
                        print(f"Def: {entry['definition']}...")
                        if stop_at_fail:
                            return
                    break
            else:
                length_diff_count += 1
                if stop_at_fail:
                    print(f"Total correct entries: {correct_count}")
                    print(f"Total wrong entries: {wrong_count}")
                    print(
                        f"Total entries differing only in length: {length_diff_count}"
                    )
                    print(f"{i}: {repr(expected[j:j + n_error_char_show])}...")
                    print("wrd:", repr(entry["traditional"]))
                    print("def:", repr(entry["definition"]))
                    return
        else:
            correct_count += 1

    print(f"Total correct entries: {correct_count}/{correct_count + wrong_count}")
    print(f"Total wrong entries: {wrong_count}/{correct_count + wrong_count}")
    print(f"Total entries differing only in length: {length_diff_count}")
