import regex as re
import regex
import functools
import csv
import os


# Load CC-CEDICT (Only Traditional Variants) ###
@functools.lru_cache(maxsize=None)  # Infinite cache size
def load_cc_cedict(filename="cedict_ts.u8"):
    """Parses CC-CEDICT to extract traditional-only variant mappings."""
    variants = {}
    with open(filename, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            match = re.match(r"(\S+) (\S+) \[.*?\] /(.*?)/", line)
            if match:
                trad, simp, definition = match.groups()

                # Extract explicit variants from definitions: "/variant of X|Y[pinyin]/"
                variant_match = re.search(
                    r"variant of ([\u4E00-\u9FFF\|]+)", definition
                )
                if variant_match:
                    var = variant_match.group(1).split("|")[0]
                    # Ensure bidirectional mapping
                    variants.setdefault(trad, set()).add(var)
                    variants.setdefault(var, set()).add(trad)

    return variants


# Load CC-CEDICT (Only Traditional Variants) ###
@functools.lru_cache(maxsize=None)  # Infinite cache size
def load_moedict(filename="moedict.csv"):
    variants = {}

    # Open the moedict.csv file
    with open(filename, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        # Iterate through each row in the CSV
        for row in reader:
            term = row["字詞名"]
            definition = row["釋義"]

            # Search for variants indicated by 也作「<VARIANT>」
            matches = re.findall(r"也作「(.*?)」", definition)
            all_words = set([term] + list(matches))

            # Print the term and its variants
            for variant in all_words:
                variants.setdefault(variant, set()).update(
                    all_words.difference({variant})
                )

    return variants


@functools.lru_cache(maxsize=None)  # Infinite cache size
def get_c_variants(folder_path="c"):
    """
    Iterates through all files in the specified folder and prints their contents.

    Args:
        folder_path (str): Path to the folder containing files.
    """
    global test_txt
    variants = {}

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            # Print the contents of the JSON file
            # data_json = json.dumps(data, indent=4, ensure_ascii=False)
            if (
                file_name.startswith("@")
                or file_name.startswith("=")
                or file_name.startswith("xref")
            ):
                continue
            non_chinese_or_bracket = regex.compile(r"[^「」\p{Han}]")
            word = regex.sub(non_chinese_or_bracket, "", data["t"])
            definitions = [
                regex.sub(non_chinese_or_bracket, "", d["f"])
                for h in data.get("h", [])  # Start from the 'h' key
                for d in h.get("d", [])  # Look inside the 'd' list
            ]
            for definition in definitions:
                # Search for variants indicated by 也作「<VARIANT>」
                matches = re.findall(r"也作「(.*?)」", definition)
                all_words = set([word] + list(matches))

                # Print the term and its variants
                if matches:
                    for variant in all_words:
                        variants.setdefault(variant, set()).update(
                            all_words.difference({variant})
                        )

    return variants


@functools.lru_cache(maxsize=None)  # Infinite cache size
def load_unihan_variants(filename="Unihan_Variants.txt"):
    """Parses Unihan_Variants.txt for character-level variants (traditional-only)."""
    variants = {}
    with open(filename, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                char = chr(int(parts[0][2:], 16))  # Convert U+XXXX to character
                key = parts[1]

                # Extract only the U+XXXX part before '<' (if present)
                var_code = parts[2].split("<")[0].strip()

                try:
                    var = chr(int(var_code[2:], 16))  # Convert U+XXXX to character

                    # Only keep traditional variants (ignore kSimplifiedVariant)
                    if (
                        "Variant" in key
                        and "Simplified" not in key
                        and "Traditional" not in key
                    ):
                        variants.setdefault(char, set()).add(var)
                        variants.setdefault(var, set()).add(char)
                except ValueError:
                    pass  # Skip bad format entries

    return variants


@functools.lru_cache(maxsize=None)  # Infinite cache size
def load_manual_variants(filename="manual_variants.csv"):
    """Parses manual_variants.csv to extract bidirectional variant mappings."""
    variants = {}

    with open(filename, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)

        for row in reader:
            if len(row) < 2:
                continue  # Skip malformed rows

            words = set(word.strip() for word in row if word.strip())

            for word in words:
                variants.setdefault(word, set()).update(words.difference({word}))

    return variants


def get_variants(word):
    return (
        load_cc_cedict()
        .get(word, set())
        .union(load_moedict().get(word, set()))
        .union(get_c_variants().get(word, set()))
        .union(load_unihan_variants().get(word, set()))
        .union(load_manual_variants().get(word, set()))
    )


load_cc_cedict()
load_moedict()
get_c_variants()
load_unihan_variants()
load_manual_variants()
""
