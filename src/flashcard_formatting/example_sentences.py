from src.utils.pinyin import (
    get_variants,
    strip_tone_marks,
    load_manual_pinyins,
    parse_cedict_toneless_pinyins,
    SKIPPABLE_LEFTOVER_PINYIN,
    KEEPABLE_PINYIN_PUNC,
    CONVERT_PUNC_DICT,
)
import regex as re
from pypinyin import pinyin, Style


def update_example_sentence_with_variants(traditional_word, segment):
    """
    Updates example sentences in the segments list by checking if the traditional word or its variants
    are present in the example sentences. If a variant is found, it is added to the example sentence dict.

    Args:
        traditional_word (str): The traditional Chinese phrase to check.
        segments (list): List of segment dictionaries.

    Returns:
        list: Updated list of segments.
    """
    # Get the variants of the traditional word
    word_variants = get_variants(traditional_word)
    if segment["label"] == "example_sentence":
        # Check if the traditional word is not in the Chinese segment
        if traditional_word not in segment["chinese"]:
            # Search through the variants
            for variant in word_variants:
                if variant in segment["chinese"]:
                    # Add the variant to the example sentence dict
                    segment["variant"] = variant
                    return True
    return False


def update_example_sentence_with_separated_words(traditional_word, segment, max_len=6):
    for word in [traditional_word] + list(get_variants(traditional_word)):
        if (
            len(word) == 2
            and segment["label"] == "example_sentence"
            and word not in segment["chinese"]
        ):
            char1, char2 = word
            pattern = f"{char1}.{{0,{max_len}}}{char2}"
            match = re.search(pattern, segment["chinese"])
            # print(pattern, segment['chinese'], match)
            if not match:
                continue
            separated_words = match.group()
            segment["separated_word"] = separated_words
            return True
    return False


def split_chinese_string(text):
    pattern = re.compile(r"\([^\(\)]*\)")
    parts = []
    i = 0

    for match in pattern.finditer(text):
        start, end = match.span()

        # Add characters before the match, one by one
        while i < start:
            parts.append(text[i])
            i += 1

        # Add the whole parenthetical as one item
        parts.append(match.group())
        i = end

    # Add any remaining characters after the last match
    while i < len(text):
        parts.append(text[i])
        i += 1

    return parts


def split_chinese_pinyin(example_sentence, trad_word=None, print_debug=False):
    try:
        return split_chinese_pinyin_helper(
            example_sentence,
            rmv_paren=False,
            trad_word=trad_word,
            print_debug=print_debug,
        )
    except ValueError:
        return split_chinese_pinyin_helper(
            example_sentence,
            rmv_paren=True,
            trad_word=trad_word,
            print_debug=print_debug,
        )


def split_chinese_pinyin_helper(
    example_sentence, rmv_paren, trad_word=None, print_debug=False
):
    """
    Splits a Chinese string and its corresponding pinyin string into matching lists.
    Uses the regex package with {Han} pattern for accurate Chinese character detection.
    Handles both toned and tone-less pinyin matching, in both lowercase and uppercase.

    Args:
        example_sentence (dict): Dictionary containing 'chinese' and 'pinyin' keys
        rmv_paren (bool): Whether to remove parenthetical text from Chinese string
        trad_word (str, optional): Traditional word for debugging
        print_debug (bool, optional): Whether to print debug information

    Returns:
        dict: Updated example_sentence with 'chinese_list' and 'pinyin_list'

    Raises:
        ValueError: If the Chinese and pinyin strings cannot be properly aligned after trying all possibilities
    """
    if rmv_paren:
        # chinese_string = re.sub(r"\([^\(\)]*\)\s*", "", example_sentence['chinese']).rstrip()
        chinese_string = split_chinese_string(example_sentence["chinese"])
    else:
        chinese_string = example_sentence["chinese"].rstrip()
    pinyin_string = example_sentence["pinyin"]

    # Check if the Chinese string contains any Han characters
    if not re.search(r"\p{Han}", "".join(chinese_string)):
        raise ValueError("The Chinese string contains no Han characters.")

    # Remove tones from the input pinyin string for matching
    toneless_pinyin_string = "".join(strip_tone_marks(char) for char in pinyin_string)

    # Function to attempt matching with backtracking
    def backtrack_match():
        # Stack to keep track of state for backtracking
        # Each entry contains (position, chinese_list, pinyin_list, remaining_pinyin, remaining_toneless, pinyin_choices_idx)
        stack = [
            (0, [], [], pinyin_string.strip(), toneless_pinyin_string.strip(), 0, "")
        ]

        while stack:
            (
                i,
                current_chinese,
                current_pinyin,
                remain_py,
                remain_toneless_py,
                choice_idx,
                ignored,
            ) = stack.pop()

            # Success condition: we've processed the entire Chinese string
            if i >= len(chinese_string):
                # Check if there's significant remaining pinyin
                if (
                    remain_py.strip()
                    and remain_py.strip() not in SKIPPABLE_LEFTOVER_PINYIN
                ):
                    # Add remaining pinyin to English and update the final result
                    if print_debug:
                        print(
                            remain_py.strip(),
                            trad_word,
                            current_chinese,
                            current_pinyin,
                        )
                    example_sentence["english"] = (
                        remain_py + " " + example_sentence["english"]
                    ).lstrip()
                    example_sentence["pinyin"] = example_sentence["pinyin"][
                        : -len(remain_py)
                    ].rstrip()
                    if current_pinyin:
                        current_pinyin[-1] = current_pinyin[-1].strip()

                # We found a complete match
                return current_chinese, current_pinyin, ignored

            while len(chinese_string[i]) > 1 and i < len(chinese_string):
                current_chinese.append(chinese_string[i])
                current_pinyin.append("")
                i += 1

            while (
                current_pinyin
                and len(remain_py) > 0
                and remain_py[0] in KEEPABLE_PINYIN_PUNC
            ):
                current_pinyin[-1] += remain_py[0]
                remain_py = remain_py[1:]
                remain_toneless_py = remain_toneless_py[1:]

            current_char = chinese_string[i]

            # Check if current character is Chinese using \p{Han} pattern
            if re.match(r"\p{Han}", current_char):
                # Get all possible pinyins for this character
                possible_pinyins = list(
                    set(
                        [
                            p[0]
                            for p in pinyin(
                                [current_char], style=Style.TONE, heteronym=True
                            )
                        ]
                    )
                    .union(load_manual_pinyins().get(current_char, set()))
                    .union(parse_cedict_toneless_pinyins().get(current_char, set()))
                )

                # Add tone-less versions of each pinyin
                toneless_pinyins = sorted(
                    [strip_tone_marks(p) for p in possible_pinyins],
                    key=len,
                    reverse=True,
                )

                # Try pinyin choices starting from choice_idx
                match_found = False
                for idx in range(choice_idx, len(toneless_pinyins)):
                    possible_toneless_pinyin = toneless_pinyins[idx]

                    # Case-insensitive matching with tone-less pinyin
                    if remain_toneless_py.lower().startswith(
                        possible_toneless_pinyin.lower()
                    ):
                        # Check for whitespace in the original pinyin string
                        whitespace_match = re.match(
                            r"^" + re.escape(possible_toneless_pinyin) + r"(\s*)",
                            remain_toneless_py,
                            re.IGNORECASE,
                        )

                        if whitespace_match:
                            toneless_pinyin_with_space = whitespace_match.group(0)

                            # Create new state with this match
                            new_chinese = current_chinese + [current_char]
                            new_pinyin = current_pinyin + [
                                remain_py[: len(toneless_pinyin_with_space)]
                            ]
                            new_remain_py = remain_py[len(toneless_pinyin_with_space) :]
                            new_remain_toneless = remain_toneless_py[
                                len(toneless_pinyin_with_space) :
                            ]

                            # Push the current state for backtracking (in case this path fails)
                            # We'll try the next pinyin choice if we come back to this state
                            if idx + 1 < len(toneless_pinyins):
                                stack.append(
                                    (
                                        i,
                                        current_chinese.copy(),
                                        current_pinyin.copy(),
                                        remain_py,
                                        remain_toneless_py,
                                        idx + 1,
                                        ignored,
                                    )
                                )

                            # Push the new state to continue with this match
                            stack.append(
                                (
                                    i + 1,
                                    new_chinese,
                                    new_pinyin,
                                    new_remain_py,
                                    new_remain_toneless,
                                    0,
                                    ignored,
                                )
                            )
                            match_found = True
                            break

                # If no match found and we have remaining pinyin, try skipping one character from pinyin
                if not match_found and len(remain_py) > 0:
                    new_ignored = ignored + remain_py[0]
                    stack.append(
                        (
                            i,
                            current_chinese.copy(),
                            current_pinyin.copy(),
                            remain_py[1:],
                            remain_toneless_py[1:],
                            0,
                            new_ignored,
                        )
                    )
                # If no match found and no remaining pinyin, we need to continue exploring other paths

            elif current_char in CONVERT_PUNC_DICT and remain_toneless_py.startswith(
                CONVERT_PUNC_DICT.get(current_char)
            ):
                # Handle punctuation
                whitespace_match = re.match(
                    r"^" + re.escape(CONVERT_PUNC_DICT.get(current_char)) + r"(\s*)",
                    remain_toneless_py,
                    re.IGNORECASE,
                )

                if whitespace_match:
                    toneless_pinyin_with_space = whitespace_match.group(0)

                    new_chinese = current_chinese + [current_char]
                    new_pinyin = current_pinyin + [
                        remain_py[: len(toneless_pinyin_with_space)]
                    ]
                    new_remain_py = remain_py[len(toneless_pinyin_with_space) :]
                    new_remain_toneless = remain_toneless_py[
                        len(toneless_pinyin_with_space) :
                    ]

                    stack.append(
                        (
                            i + 1,
                            new_chinese,
                            new_pinyin,
                            new_remain_py,
                            new_remain_toneless,
                            0,
                            ignored,
                        )
                    )
                elif len(remain_py) > 0:  # Only try ignoring if we have characters left
                    # If we can't match punctuation, try ignoring one character from pinyin
                    new_ignored = ignored + remain_py[0]
                    stack.append(
                        (
                            i,
                            current_chinese.copy(),
                            current_pinyin.copy(),
                            remain_py[1:],
                            remain_toneless_py[1:],
                            0,
                            new_ignored,
                        )
                    )

            else:
                # For non-Chinese characters, process the segment
                non_chinese_segment = ""
                current_pos = i
                while current_pos < len(chinese_string) and not re.match(
                    r"\p{Han}", chinese_string[current_pos]
                ):
                    non_chinese_segment += chinese_string[current_pos]
                    current_pos += 1

                # Add the non-Chinese segment to the lists
                if non_chinese_segment:
                    if current_chinese:  # If we have a current Chinese segment
                        # Check for whitespace at the start of the non-Chinese segment
                        whitespace_match = re.match(r"^\s+", non_chinese_segment)
                        if whitespace_match:  # Handle leading whitespace
                            whitespace = whitespace_match.group(0)
                            non_chinese_segment = non_chinese_segment[len(whitespace) :]
                            # current_chinese[-1] += whitespace

                    if non_chinese_segment:
                        new_chinese = current_chinese + [non_chinese_segment]

                        # Try to match and remove the non-Chinese segment from the pinyin string
                        if remain_py.startswith(non_chinese_segment):
                            new_pinyin = current_pinyin + [non_chinese_segment]
                            new_remain_py = remain_py[len(non_chinese_segment) :]
                            new_remain_toneless = remain_toneless_py[
                                len(non_chinese_segment) :
                            ]
                        else:
                            # Handle case where non-Chinese characters might not appear in pinyin
                            new_pinyin = current_pinyin + [non_chinese_segment]
                            new_remain_py = remain_py
                            new_remain_toneless = remain_toneless_py

                        stack.append(
                            (
                                current_pos,
                                new_chinese,
                                new_pinyin,
                                new_remain_py,
                                new_remain_toneless,
                                0,
                                ignored,
                            )
                        )
                    else:
                        stack.append(
                            (
                                current_pos,
                                current_chinese.copy(),
                                current_pinyin.copy(),
                                remain_py,
                                remain_toneless_py,
                                0,
                                ignored,
                            )
                        )

        # If we've exhausted all possibilities without finding a match
        if print_debug:
            if trad_word:
                print("Trad word:", trad_word)
            print("Chinese string:", chinese_string)
            print("Pinyin string:", pinyin_string)

        raise ValueError(
            f"{trad_word}: Could not match pinyin for Chinese text '{chinese_string}' after trying all possibilities"
        )

    # Run the backtracking algorithm
    try:
        chinese_list, pinyin_list, ignored_pinyin = backtrack_match()

        example_sentence["chinese_list"] = chinese_list
        example_sentence["pinyin_list"] = pinyin_list
        example_sentence["ignored_pinyin"] = ignored_pinyin.strip()

        return example_sentence

    except ValueError as e:
        if print_debug:
            print(f"Error: {e}")
        raise e


def add_bold_segments(example_sentence, traditional_word):
    split_chinese_pinyin(example_sentence, trad_word=traditional_word)
    update_example_sentence_with_variants(traditional_word, example_sentence)
    update_example_sentence_with_separated_words(traditional_word, example_sentence)
    to_bold = None
    if traditional_word in example_sentence["chinese"]:
        to_bold = traditional_word
    elif "variant" in example_sentence:
        to_bold = example_sentence["variant"]
    elif "separated_word" in example_sentence:
        to_bold = example_sentence["separated_word"]
    else:
        raise ValueError(
            f"No valid word found to bold for {traditional_word}, example sentence: {example_sentence}"
        )

    chinese_final_list = []  # [{'segment': '升級到', 'bold': false}, ...]}
    pinyin_final_list = []  # [{'segment': 'shengjidao', 'bold': false}, ...]}

    # Collect characters and pinyins to process
    chinese_chars = example_sentence["chinese_list"]
    pinyin_chars = example_sentence["pinyin_list"]
    found_bold = False

    i = 0
    while i < len(chinese_chars):
        # Check if the current position starts a matching segment for to_bold
        if (
            i + len(to_bold) <= len(chinese_chars)
            and "".join(chinese_chars[i : i + len(to_bold)]) == to_bold
        ):
            # Add the bold segment as a whole
            chinese_final_list.append({"segment": to_bold, "bold": True})

            # Collect corresponding pinyin for the bold segment
            bold_pinyin = "".join(pinyin_chars[i : i + len(to_bold)])
            bold_pinyin_whtspc = bold_pinyin[len(bold_pinyin.rstrip()) :]
            bold_pinyin = bold_pinyin.rstrip()
            pinyin_final_list.append({"segment": bold_pinyin, "bold": True})
            if bold_pinyin_whtspc:
                pinyin_chars[i + len(to_bold)] = (
                    bold_pinyin_whtspc + pinyin_chars[i + len(to_bold)]
                )

            # Skip ahead past the bold segment
            found_bold = True
            i += len(to_bold)
        else:
            # Add non-bold character
            chinese_final_list.append({"segment": chinese_chars[i], "bold": False})
            pinyin_final_list.append({"segment": pinyin_chars[i], "bold": False})
            i += 1

    if not found_bold:
        raise ValueError(
            f"Could not find the word '{to_bold}' in the example sentence. {example_sentence}"
        )

    # Now combine any adjacent segments with the same bold status
    # (This is technically redundant with the logic above but included for clarity)
    combined_chinese = []
    combined_pinyin = []

    if chinese_final_list:
        current_chinese = chinese_final_list[0]
        current_pinyin = pinyin_final_list[0]

        for i in range(1, len(chinese_final_list)):
            if chinese_final_list[i]["bold"] == current_chinese["bold"]:
                # Combine with previous segment of same type
                current_chinese["segment"] += chinese_final_list[i]["segment"]
                current_pinyin["segment"] += pinyin_final_list[i]["segment"]
            else:
                # Add the completed segment and start a new one
                combined_chinese.append(current_chinese)
                combined_pinyin.append(current_pinyin)
                current_chinese = chinese_final_list[i]
                current_pinyin = pinyin_final_list[i]

        # Add the last segment
        combined_chinese.append(current_chinese)
        combined_pinyin.append(current_pinyin)

    example_sentence["chinese_list_w_bold_labels"] = combined_chinese
    example_sentence["pinyin_list_w_bold_labels"] = combined_pinyin
