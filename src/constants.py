from src.utils import find_file_with_wildcard

# Define scopes for accessing Google Drive
SCOPES = ["https://www.googleapis.com/auth/drive"]
MEMORY_FILE = "processed_files.json"
CREDENTIALS_FILE_WILDCARDED = "../.credentials/client_secret*.json"
CREDENTIALS_FILE = find_file_with_wildcard(CREDENTIALS_FILE_WILDCARDED)
TOKEN_FILE = "../.credentials/token.json"
SERVER_FOLDER = "server_files"

# google drive
FLASHCARD_FILE_NAME = "pleco_flashcards.xml"

# AnkiConnect API endpoint
ANKI_CONNECT_URL = "http://localhost:8765"
