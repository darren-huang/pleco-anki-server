"""Interface to AnkiConnect API for managing Anki flashcard operations."""

import re
import requests
from src.constants import ANKI_CONNECT_URL


def get_anki_deck_cards(deck_name):
    """Retrieve detailed card information from a specified deck."""
    find_payload = {
        "action": "findCards",
        "version": 6,
        "params": {
            "query": f'deck:"{deck_name}"'  # Query for cards only in the specified deck
        },
    }

    response = requests.post(ANKI_CONNECT_URL, json=find_payload, timeout=60)

    if response.status_code == 200:
        find_result = response.json()
        if "result" in find_result and find_result["result"]:
            card_ids = find_result["result"]
            info_payload = {
                "action": "cardsInfo",
                "version": 6,
                "params": {"cards": card_ids},  # Pass the list of card IDs
            }

            info_response = requests.post(
                ANKI_CONNECT_URL, json=info_payload, timeout=60
            )

            if info_response.status_code == 200:
                info_result = info_response.json()
                if "result" in info_result and info_result["result"]:
                    return info_result["result"]
                else:
                    raise ConnectionError(
                        f"Error retrieving card information: {info_result.get('error')}"
                    )
            else:
                raise ConnectionError(
                    "Failed to connect to AnkiConnect for card information."
                )
        else:
            raise ValueError(f"No cards found or error: {find_result.get('error')}")
    else:
        raise ConnectionError("Failed to connect to AnkiConnect for finding cards.")


def sync_anki():
    """Sync Anki with the cloud to ensure the latest data is available."""
    sync_payload = {"action": "sync", "version": 6}

    sync_response = requests.post(ANKI_CONNECT_URL, json=sync_payload, timeout=60)

    if sync_response.status_code == 200:
        sync_result = sync_response.json()
        if sync_result.get("error"):
            raise ConnectionError(f"Error syncing Anki: {sync_result['error']}")
        else:
            print("Anki sync successful.")
    else:
        raise ConnectionError("Failed to connect to AnkiConnect for syncing.")


def get_latest_anki_flaschard_words():
    """Retrieve the latest flashcard words from the 'Pleco Import' deck in Anki."""
    flashcard_set = set()

    # Step 0: Sync Anki with the cloud
    sync_anki()

    # Step 1: Find all card information in the "Pleco Import" deck
    card_info = get_anki_deck_cards("Pleco Import")
    print(f"Total cards found in 'Pleco Import': {len(card_info)}")

    # Step 2: Extract the "Front" field for each card and add to the set
    for card in card_info:
        front_field = re.sub(
            r"[^\u4e00-\u9fff]", "", card["fields"]["Front"]["value"]
        )  # Filter out non-Chinese characters
        flashcard_set.add(front_field)
    print("success")

    return flashcard_set
