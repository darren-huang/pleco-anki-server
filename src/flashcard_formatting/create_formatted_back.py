import json

def create_formatted_back(entry):
    traditional = entry.get("traditional", "")
    simplified = entry.get("simplified", "")
    pinyin = entry.get("pinyin", "")
    definition = entry.get("definition", "")
    
    formatted_back = f'<div align="left"><p><span style="font-size:32px" ;="">{traditional}〔{simplified}〕</span><br>\n'
    formatted_back += f'<span style="color:#B4B4B4;"><b><span style="font-size:0.80em;">PY </span></b></span><span style="color:#E30000;"><span style="font-weight:600;">{pinyin}</span></span></p>\n</div>'
    formatted_back += f'<div align="left"><p>{definition}</p>\n</div>'
    formatted_back += '<plecoentry c="00000000" d="50414345" e="01d53000" x="-1"></plecoentry>'
    
    return formatted_back

def process_flashcard_entries(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        entries = json.load(file)
    
    for entry in entries:
        entry["formatted_back"] = create_formatted_back(entry)
    
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(entries, file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    flashcard_entries_path = '/Users/darrenhuang/code/pleco-anki-server/flashcard_entries.json'
    process_flashcard_entries(flashcard_entries_path)
