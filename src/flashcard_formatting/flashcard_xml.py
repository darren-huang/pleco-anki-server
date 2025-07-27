"""Module for parsing and processing Pleco flashcard XML files."""

import xml.etree.ElementTree as ET
from src.utils.pinyin import convert_pinyin


def process_flashcard_xml(xml_text):
    """Process Pleco flashcard XML into dictionary entries.

    Args:
        xml_text: XML string containing Pleco flashcard data

    Returns:
        tuple: (list of processed entries, list of problematic entries)
        entries is a list of dictionaries with keys:
            - simplified: Simplified Chinese characters
            - traditional: Traditional Chinese characters
            - pinyin: Pinyin representation
            - definition: English definition
            - dictid: Dictionary ID from the card
    """
    # example xml text: <?xml version="1.0" encoding="UTF-8"?><plecoflash formatversion="2" creator="Pleco User 19097293" generator="Pleco 2.0 Flashcard Exporter" platform="iPhone OS" created="1735693200"><categories></categories><cards><card language="chinese" created="1735513394" modified="1735513394"><entry><headword charset="sc">游戏</headword><headword charset="tc">遊戲</headword><pron type="hypy" tones="numbers">you2xi4</pron><defn>noun recreation; game 做遊戲 Zuò yóuxì play games verb play 孩子們在公園裡遊戲。 Háizi men zài gōngyuán lǐ yóuxì. The children are playing in the park.</defn></entry><dictref dictid="PACE" entryid="35050240"/></card><card language="chinese" created="1735514285" modified="1735514285"><entry><headword charset="sc">革新</headword><headword charset="tc">革新</headword><pron type="hypy" tones="numbers">ge2xin1</pron><defn>noun innovation; renovation 技術革新 jìshù géxīn technological innovation verb innovate; improve 傳統的手工藝技術不斷革新。 Chuántǒng de shǒu gōngyì jìshù bùduàn géxīn. Traditional handicraft techniques are being steadily improved.</defn></entry><dictref dictid="PACE" entryid="21578752"/></card>

    # Parse the XML content
    root = ET.fromstring(xml_text)

    # Find all <card> tags
    cards = root.findall(".//card")

    # Extract and print each entry
    entries_data = []
    problematic_cards = []
    for card in cards:
        try:
            entries = card.findall("entry")
            if len(entries) != 1:
                print(ET.tostring(card, encoding="unicode"))
                raise ValueError("Card does not contain exactly one entry.")

            entry = entries[0]
            simplified = entry.find('headword[@charset="sc"]').text
            traditional = entry.find('headword[@charset="tc"]').text
            pinyin = convert_pinyin(entry.find("pron").text)
            if entry.find("defn") is None:
                definition = ""
            else:
                definition = entry.find("defn").text
            dictid = card.find("dictref").attrib["dictid"]

            entry_data = {
                "simplified": simplified,
                "traditional": traditional,
                "pinyin": pinyin,
                "definition": definition,
                "dictid": dictid,
            }
            if definition:
                entries_data.append(entry_data)
            else:
                problematic_cards.append(entry_data)
        except Exception as e:
            print(ET.tostring(card, encoding="unicode"))
            raise e

    return entries_data, problematic_cards
