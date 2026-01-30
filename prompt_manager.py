import os
import json
import uuid
from datetime import datetime

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROMPT_DB_FILE = os.path.join(DATA_DIR, "prompts.json")

os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------------
# DB OPS
# ---------------------------------------------------------
def load_db():
    if not os.path.exists(PROMPT_DB_FILE): return {}
    try:
        with open(PROMPT_DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}

def save_db(data):
    with open(PROMPT_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# ---------------------------------------------------------
# LOGIC
# ---------------------------------------------------------
def create_prompt(title, content, tags, linked_chars):
    """
    linked_chars: list of character IDs
    """
    db = load_db()
    pid = str(uuid.uuid4())
    
    db[pid] = {
        "title": title,
        "content": content,
        "tags": [t.strip() for t in tags if t.strip()],
        "linked_chars": linked_chars,
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }
    save_db(db)
    return pid

def get_all_prompts():
    return load_db()

def get_prompt(pid):
    db = load_db()
    return db.get(pid)

def delete_prompt(pid):
    db = load_db()
    if pid in db:
        del db[pid]
        save_db(db)

def get_prompts_for_character(char_id):
    """Returns a list of prompts assigned to a specific character."""
    db = load_db()
    matches = []
    for pid, data in db.items():
        if char_id in data.get("linked_chars", []):
            data['id'] = pid
            matches.append(data)
    return matches
