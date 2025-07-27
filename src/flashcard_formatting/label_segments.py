"""Module for segmenting and labeling Chinese text with pinyin, parts of speech, and example sentences."""

import regex as re
import json
from src.utils.utils import overlap_length
from src.flashcard_formatting.example_sentences import add_bold_segments
from src.utils.pinyin import get_fifth_tone_pinyins
from src.utils.resource_utils import get_resource_path


# Load the part of speech keywords from the JSON file
with open(
    get_resource_path("part_of_speech_keywords.json"), "r", encoding="utf-8"
) as file:
    part_of_speech_keywords = json.load(file)


def label_segments(text, traditional_word):
    """Segment Chinese text into labeled parts including Chinese characters, pinyin, and English translations.

    Args:
        text: The text to segment, containing Chinese characters, pinyin, and English
        traditional_word: The traditional Chinese word being processed

    Returns:
        List of dictionaries containing labeled segments with keys 'segment' and 'label'
    """
    segments = []
    part_of_speech_pattern = re.compile(
        r"(\n?\b("
        + "|".join([re.escape(keyword) for keyword in part_of_speech_keywords])
        + r"))\b",
        re.IGNORECASE,
    )
    chinese_pattern = re.compile(r"[^\s\(\)\[\]]*\p{Han}+[^\s\(\)\[\]]*")
    pinyin_pattern = re.compile(
        r"\S*[āēīōūǖĀĒĪŌŪǕáéíóúǘÁÉÍÓÚǗǎěǐǒǔǚǍĚǏǑǓǙàèìòùǜÀÈÌÒÙǛ]\S*"
    )
    english_brackets_pattern = re.compile(r"\[[^\[\]]*\]")
    english_paren_pattern = re.compile(r"\([^\(\)]*\)")
    pleco_uead_pattern = re.compile(r"\uead1.*?\uead2")

    pos_matches = list(part_of_speech_pattern.finditer(text))
    uead_matches = list(pleco_uead_pattern.finditer(text))
    chinese_matches = list(chinese_pattern.finditer(text))
    pinyin_matches = list(pinyin_pattern.finditer(text))
    english_brackets_matches = list(english_brackets_pattern.finditer(text))
    english_paren_pattern = list(english_paren_pattern.finditer(text))

    all_matches = sorted(
        pos_matches
        + english_brackets_matches
        + english_paren_pattern
        + uead_matches
        + chinese_matches
        + pinyin_matches,
        key=lambda x: x.start(),
    )

    last_end = 0
    for match in all_matches:
        if match.start() < last_end:
            continue
        if match.start() > last_end:
            segments.append(
                {"segment": text[last_end : match.start()], "label": "english"}
            )

        if match in pos_matches:
            pos_label = (
                "part of speech" if match.group()[0] == "\n" else "temp part of speech"
            )
            segments.append({"segment": match.group().strip(), "label": pos_label})
        elif match in english_brackets_matches:
            segments.append({"segment": match.group(), "label": "english"})
        elif match in english_paren_pattern:
            target_str = match.group()
            if re.match(pinyin_pattern, target_str):
                segments.append({"segment": target_str, "label": "pinyin"})
            elif re.match(r"^[\p{Han}《》=]+$", re.sub(r"[\(\)\s]", "", target_str)):
                segments.append({"segment": target_str, "label": "chinese"})
            else:
                segments.append({"segment": target_str, "label": "english"})
        elif match in uead_matches:
            segments.append({"segment": match.group(), "label": "english"})
        elif match in chinese_matches:
            segments.append({"segment": match.group(), "label": "chinese"})
        elif match in pinyin_matches:
            segments.append({"segment": match.group(), "label": "pinyin"})
        last_end = match.end()

    if last_end < len(text):
        segments.append({"segment": text[last_end:], "label": "english"})

    # process empty segments and whitespace
    segments = filter_empty_segs(segments)
    segments = process_whitespace_english(segments)
    segments = combine_adjacent_segments(segments)
    segments = shift_leading_whitespace(segments)

    # adjust pinyin for toneless pinyin
    segments = process_fifth_tone_pinyin(segments)
    segments = filter_empty_segs(segments)
    segments = combine_adjacent_segments(segments)
    segments = shift_leading_whitespace(segments)

    # process item numbers
    segments = process_item_numbers(segments)
    segments = filter_empty_segs(segments)
    segments = combine_adjacent_segments(segments)
    # print(segments)

    # process parts of speech
    segments = process_parts_of_speech(segments)
    segments = filter_empty_segs(segments)
    segments = combine_adjacent_segments(segments)

    # example sentences
    segments = combine_pinyin_english_pinyin(segments)
    segments = combine_adjacent_segments(segments)
    segments = combine_example_sentences(segments)
    segments = combine_adjacent_segments(segments, {("english", "chinese"): "english"})

    # bold
    segments = bold_example_sentences(segments, traditional_word)
    segments = combine_adjacent_segments(segments)

    segments = convert_segment_labels(segments, "chinese", "english")
    segments = convert_segment_labels(segments, "pinyin", "english")
    segments = combine_adjacent_segments(segments)

    return segments


def convert_segment_labels(segments, from_label, to_label):
    new_segments = []
    for seg in segments:
        if seg["label"] == from_label:
            seg["label"] = to_label
        new_segments.append(seg)
    return new_segments


def process_parts_of_speech(segments):
    new_segments = []
    i = 0
    valid_next_labels = ["english", "temp part of speech", "item_number"]
    prev_english_last_ws_chars = ["\n"]
    prev_english_last_chars = ["\uead2"]

    # process POS at the very beginning
    last_seg = None
    while i < len(segments) - 1:
        if (
            segments[i]["label"] == "temp part of speech"
            and segments[i + 1]["label"] in valid_next_labels
        ):
            segments[i]["label"] = "part of speech"
            new_segments.append(segments[i])
            last_seg = segments[i]
            i += 1
        else:
            break

    # for every segment where the last segment is a line number, convert POS
    while i < len(segments):
        if segments[i]["label"] == "temp part of speech":
            if (
                i != len(segments) - 1
                and last_seg
                and last_seg["label"] in ["item_number", "part of speech"]
                and segments[i + 1]["label"] in valid_next_labels
            ):
                segments[i]["label"] = "part of speech"
            elif (
                i != len(segments) - 1
                and last_seg
                and last_seg["label"] == "english"
                and (
                    last_seg["segment"][-1] in prev_english_last_ws_chars
                    or last_seg["segment"].strip()[-1] in prev_english_last_chars
                )
                and segments[i + 1]["label"] in valid_next_labels
            ):
                segments[i]["label"] = "part of speech"
            else:
                segments[i]["label"] = "english"

        last_seg = segments[i]
        new_segments.append(segments[i])
        i += 1
    return new_segments


def shift_leading_whitespace(segments):
    for i in range(1, len(segments)):
        current_segment = segments[i]["segment"]
        match = re.match(r"^(\s+)", current_segment)
        if match:
            leading_ws = match.group(1)
            # Remove leading whitespace from current segment
            segments[i]["segment"] = current_segment[len(leading_ws) :]
            # Append it to the previous segment
            segments[i - 1]["segment"] += leading_ws
    return segments


def process_whitespace_english(segments):
    new_segments = []
    last_seg = {}
    for seg in segments:
        if (
            last_seg
            and seg["label"] == "english"
            and re.fullmatch(r"\s*", seg["segment"]) is not None
        ):
            last_seg["segment"] += seg["segment"]
        else:
            new_segments.append(seg)
            last_seg = seg
    return new_segments


def bold_example_sentences(segments, traditional_word):
    new_segments = []
    for seg in segments:
        if seg["label"] == "example_sentence":
            try:
                add_bold_segments(seg, traditional_word=traditional_word)
            except ValueError as e:
                print(
                    f"{traditional_word}: Error processing example sentence: {seg}, converting to english: {e}"
                )
                # update_example_sentence_with_variants(traditional_word, seg)
                # update_example_sentence_with_separated_words(traditional_word, seg)
                seg = {
                    "segment": seg["chinese"] + seg["pinyin"] + seg["english"],
                    "label": "english",
                }
            new_segments.append(seg)
        else:
            new_segments.append(seg)
    return new_segments


def update_example_sentence_english_chinese_overlap(segment):
    if segment["label"] == "example_sentence":
        chinese = segment["chinese"]
        english = segment["english"]
        overlap = overlap_length(chinese, english)
        if overlap > 0:
            segment["english"] = english[overlap:]
            segment["pinyin"] += " " + english[:overlap]
            # print(chinese, english, segment)
    return segment


def combine_example_sentences(segments):
    new_segments = []
    i = 0
    while i + 2 < len(segments):
        if (
            segments[i]["label"] == "chinese"
            and segments[i + 1]["label"] == "pinyin"
            and segments[i + 2]["label"] == "english"
        ):
            combined_segment = {
                "label": "example_sentence",
                "chinese": segments[i]["segment"],
                "pinyin": segments[i + 1]["segment"],
                "english": segments[i + 2]["segment"],
            }
            combined_segment = update_example_sentence_english_chinese_overlap(
                combined_segment
            )
            new_segments.append(combined_segment)
            i += 3
        elif (  # special case
            i + 3 < len(segments)
            and segments[i]["label"] == "chinese"
            and segments[i + 1]["label"] == "english"
            # and len(segments[i + 1]["segment"]) <= 1
            and segments[i + 2]["label"] == "pinyin"
            and segments[i + 3]["label"] == "english"
        ):
            combined_segment = {
                "label": "example_sentence",
                "chinese": segments[i]["segment"],
                "pinyin": segments[i + 2]["segment"],
                "english": segments[i + 3]["segment"],
            }
            extra_segment = segments[i + 1]["segment"]
            if extra_segment == "。":
                combined_segment["chinese"] += extra_segment
            elif combined_segment["chinese"].startswith(extra_segment):
                combined_segment["pinyin"] = (
                    extra_segment + " " + combined_segment["pinyin"]
                )
            else:
                combined_segment["chinese"] += " " + extra_segment
            combined_segment = update_example_sentence_english_chinese_overlap(
                combined_segment
            )

            # print("special case", combined_segment)
            # print(segments[i + 1])
            new_segments.append(combined_segment)
            i += 4
        else:
            new_segments.append(segments[i])
            i += 1
    new_segments.extend(segments[i:])
    return new_segments


def process_item_numbers(segments):
    # Process sequences between "part of speech" segments
    def search(segment_str, num, is_one=False):
        regex_patt = str(num) + r"(?=($|\s))"
        if is_one:
            regex_patt = r"(^|(\(-//-\) )|(\uead2 ))" + regex_patt
        else:
            regex_patt = r"(?<=(^|\s))" + regex_patt
        return re.search(regex_patt, segment_str)

    new_segments = []
    i = 0
    num = 1
    while i < len(segments):
        seg = segments[i]
        if seg["label"] == "english" and (
            search(seg["segment"], 1, is_one=True)
            or (num != 1 and search(seg["segment"], num))
        ):
            if search(seg["segment"], 1, is_one=True):
                num = 1

            start_index = search(seg["segment"], num).start()
            new_segments.append(
                {
                    "segment": seg["segment"][:start_index],
                    "label": "english",
                }
            )
            new_segments.append({"segment": str(num), "label": "item_number"})
            seg["segment"] = seg["segment"][start_index + len(str(num)) :].lstrip()
            num += 1
            continue  # don't update i
        else:
            new_segments.append(seg)
            i += 1
    return new_segments


def filter_empty_segs(segments):
    return [segment for segment in segments if segment["segment"]]


def combine_adjacent_segments(segments, equivalent_labels=None):
    if equivalent_labels is None:
        equivalent_labels = {}
    else:
        equivalent_labels = {
            tuple(sorted(list(k))): v for k, v in equivalent_labels.items()
        }

    combined_segments = []
    for segment in segments:
        if combined_segments and segment["label"] not in [
            "example_sentence",
            "part of speech",
            "temp part of speech",
        ]:
            # if combined_segments and segment["label"] not in ["example_sentence"]:
            last_label = combined_segments[-1]["label"]
            current_label = segment["label"]
            eq_label = tuple(sorted([last_label, current_label]))
            if last_label == current_label or eq_label in equivalent_labels:
                # combined_segments[-1]["segment"] += " " + segment["segment"]
                combined_segments[-1]["segment"] += segment["segment"]
                if eq_label in equivalent_labels:
                    combined_segments[-1]["label"] = equivalent_labels[eq_label]
            else:
                combined_segments.append(segment)
        else:
            combined_segments.append(segment)
    return combined_segments


def process_fifth_tone_pinyin(segments):
    new_segments = []
    for i in range(len(segments) - 1):
        current_segment = segments[i]
        next_segment = segments[i + 1]
        new_segments.append(current_segment)

        done = False
        while not done:
            if (
                current_segment["label"] in ["chinese", "pinyin"]
                and next_segment["label"] == "english"
            ):
                for pinyin in get_fifth_tone_pinyins():
                    regex_patt = "^" + pinyin + r"($|[^a-zA-Z’])"
                    mtch = re.match(regex_patt, next_segment["segment"].lower())
                    if mtch:
                        pinyin_seg, rest = (
                            next_segment["segment"][: mtch.end()],
                            next_segment["segment"][mtch.end() :],
                        )

                        new_segments.append(
                            # {"segment": pinyin_seg.strip(), "label": "pinyin"}
                            {"segment": pinyin_seg, "label": "pinyin"}
                        )
                        # next_segment["segment"] = rest.strip()
                        next_segment["segment"] = rest
                        break
                else:
                    done = True
            else:
                done = True
    new_segments.append(segments[-1])
    return new_segments


def combine_pinyin_english_pinyin(segments):
    new_segments = []
    segments = segments.copy()
    i = 0
    while i + 2 < len(segments):
        if (
            segments[i]["label"] == "pinyin"
            and segments[i + 1]["label"] == "english"
            and segments[i + 2]["label"] == "pinyin"
        ):
            combined_segment = {
                "segment": segments[i]["segment"]
                + segments[i + 1]["segment"]
                + segments[i + 2]["segment"],
                # "segment": segments[i]["segment"] + " " + segments[i + 1]["segment"] + " " + segments[i + 2]["segment"],
                "label": "pinyin",
            }
            i += 2
            segments[i] = combined_segment
        else:
            new_segments.append(segments[i])
            i += 1
    new_segments.extend(segments[i:])
    return new_segments
