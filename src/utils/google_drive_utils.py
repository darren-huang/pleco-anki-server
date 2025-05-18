import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from src.constants import (
    SCOPES,
    TOKEN_FILE,
    CREDENTIALS_FILE,
    FLASHCARD_FILE_NAME,
    MEMORY_FILE,
)
import datetime
import json
import time


def authenticate_google_drive():
    """Authenticate with Google Drive and return the service object."""
    creds = None
    # Check if token.json exists (token storage for authenticated user)
    if os.path.exists(TOKEN_FILE):
        print("Loading credentials from token.json")
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Authenticate if credentials are not valid or do not exist
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("Refreshing expired credentials")
                creds.refresh(Request())
            except Exception as e:
                print(f"Failed to refresh credentials: {e}")
                creds = None
        if not creds or not creds.valid:
            print("Authenticating with Google Drive")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save credentials for the next run
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    # Build the Drive API service
    return build("drive", "v3", credentials=creds)


def get_items_by_name(service, name, is_folder=False, is_root=False):
    """Get a list of items by name, including their modified time, sorted by modified time."""
    try:
        q = f"name = '{name}'"
        if is_folder:
            q += " and mimeType = 'application/vnd.google-apps.folder'"
        else:
            q += " and mimeType != 'application/vnd.google-apps.folder'"
        if is_root:
            q += " and 'root' in parents"

        results = (
            service.files()
            .list(
                q=q,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, parents)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )
        return results.get("files", [])
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []


def move_file_to_folder(service, file_id, folder_id):
    """Move a file to a specific folder in Google Drive."""
    try:
        # Retrieve the current parents
        file = service.files().get(fileId=file_id, fields="parents").execute()
        previous_parents = ",".join(file.get("parents", []))

        # Move the file to the new folder
        service.files().update(
            fileId=file_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields="id, parents",
        ).execute()
        print(f"File {file_id} has been moved to folder {folder_id}.")
    except HttpError as error:
        print(f"An error occurred while moving the file: {error}")


SERVICE = authenticate_google_drive()
FLASCHARD_FILE_ARCHIVE_FOLDER = "_Pleco"
FLASCHARD_FILE_ARCHIVE_FOLDER_ID = get_items_by_name(
    SERVICE, FLASCHARD_FILE_ARCHIVE_FOLDER, is_folder=True, is_root=True
)[0]["id"]


# main google drive functions
def get_latest_flashcard_xml():
    files = get_items_by_name(
        SERVICE, FLASHCARD_FILE_NAME, is_folder=False, is_root=True
    )
    if len(files) == 0:
        print("No files found.")
        return None

    # Download the content of the target file
    target_file = files[0]
    request = SERVICE.files().get_media(fileId=target_file["id"])
    file_content = request.execute()
    file_text = file_content.decode("utf-8")
    modified_time = datetime.datetime.fromisoformat(
        target_file["modifiedTime"].replace("Z", "+00:00")
    )
    local_time = modified_time.astimezone()
    print(
        "Latest flashcard xml last modified time:",
        local_time.strftime("%Y-%m-%d %H:%M:%S %Z%z"),
    )
    return file_text


def archive_flashcard_xmls(archive_latest=False):
    files = get_items_by_name(
        SERVICE, FLASHCARD_FILE_NAME, is_folder=False, is_root=True
    )
    if len(files) == 0:
        print("No files found.")
        return

    # move irrelevant files to archive folder
    for f in files[0 if archive_latest else 1 :]:
        move_file_to_folder(SERVICE, f["id"], FLASCHARD_FILE_ARCHIVE_FOLDER_ID)


def monitor_google_drive(target_folder_id, interval=60):
    """Periodically check for new files, process them, and move them."""
    service = authenticate_google_drive()
    processed_files = load_processed_files()

    while True:
        print("Checking for new files named 'pleco_flashcards.xml'...")
        files = list_files_by_name(service, "pleco_flashcards.xml")

        for file in files:
            if file["id"] not in processed_files:
                # Process the file
                process_file(file)

                # Move the file to the specified folder
                move_file_to_folder(service, file["id"], target_folder_id)

                # Mark the file as processed and save to memory
                processed_files.add(file["id"])
                save_processed_files(processed_files)

        # Wait for the specified interval before checking again
        time.sleep(interval)


def list_files_by_name(service, file_name):
    """List files with a specific name from Google Drive."""
    try:
        results = (
            service.files()
            .list(
                q=f"name = '{file_name}'",
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, parents)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )
        return results.get("files", [])
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []


def process_file(file):
    """Placeholder function to process a file."""
    print(f"Processing file: {file['name']} (ID: {file['id']})")


def load_processed_files():
    """Load the list of processed file IDs from a local memory file."""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as file:
            return set(json.load(file))
    return set()


def save_processed_files(processed_files):
    """Save the list of processed file IDs to a local memory file."""
    with open(MEMORY_FILE, "w") as file:
        json.dump(list(processed_files), file)
