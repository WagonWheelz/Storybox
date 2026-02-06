import os
import json
import uuid
import shutil
import hashlib
from datetime import datetime

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LORE_IMG_DIR = os.path.join(BASE_DIR, "lore_images")
LORE_DB_FILE = os.path.join(DATA_DIR, "lore.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LORE_IMG_DIR, exist_ok=True)

# ---------------------------------------------------------
# DB OPS
# ---------------------------------------------------------
def load_db():
    if not os.path.exists(LORE_DB_FILE): return {}
    try:
        with open(LORE_DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}

def save_db(data):
    with open(LORE_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# ---------------------------------------------------------
# LOGIC
# ---------------------------------------------------------
def create_lore(title, content, type_category, tags):
    db = load_db()
    lid = str(uuid.uuid4())
    
    db[lid] = {
        "title": title,
        "content": content,
        "type": type_category, # e.g., Location, Item, History
        "tags": [t.strip() for t in tags if t.strip()],
        "image": None,
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }
    save_db(db)
    return lid

def get_all_lore():
    return load_db()

def get_lore(lid):
    db = load_db()
    return db.get(lid)

def update_lore(lid, title, content, type_category, tags, image_filename=None):
    db = load_db()
    if lid in db:
        db[lid]["title"] = title
        db[lid]["content"] = content
        db[lid]["type"] = type_category
        db[lid]["tags"] = [t.strip() for t in tags if t.strip()]
        if image_filename:
            db[lid]["image"] = image_filename
        save_db(db)

def delete_lore(lid):
    db = load_db()
    if lid in db:
        del db[lid]
        save_db(db)

def save_lore_image(lid, file_object, original_filename):
    ext = os.path.splitext(original_filename)[1]
    safe_filename = f"{lid}_{uuid.uuid4().hex[:6]}{ext}"
    file_path = os.path.join(LORE_IMG_DIR, safe_filename)
    
    with open(file_path, "wb+") as dest:
        shutil.copyfileobj(file_object, dest)
        
    return safe_filename
