import os
import json
import shutil
import hashlib
from datetime import datetime

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORY_DIR = os.path.join(BASE_DIR, "stories")
DATA_DIR = os.path.join(BASE_DIR, "data")
BACKGROUND_DIR = os.path.join(BASE_DIR, "backgrounds")
META_DB_FILE = os.path.join(DATA_DIR, "stories_meta.json")

# Ensure directories exist
os.makedirs(STORY_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKGROUND_DIR, exist_ok=True)

# ---------------------------------------------------------
# METADATA DB
# ---------------------------------------------------------
def load_meta():
    if not os.path.exists(META_DB_FILE): return {}
    try:
        with open(META_DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}

def save_meta(data):
    with open(META_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def get_story_meta(rel_path):
    db = load_meta()
    
    # Create default if missing
    if rel_path not in db:
        db[rel_path] = {
            "display_title": os.path.basename(rel_path).replace(".txt", ""),
            "synopsis": "No synopsis written.",
            "tags": [],
            "rating": 0,
            "format_type": "star_rp",
            "background_file": None,
            "created_at": datetime.now().strftime("%Y-%m-%d")
        }
        save_meta(db)
    
    # Backwards compatibility checks
    entry = db[rel_path]
    dirty = False
    
    if "rating" not in entry:
        entry["rating"] = 0
        dirty = True
        
    if "format_type" not in entry:
        entry["format_type"] = "star_rp"
        dirty = True
        
    if dirty:
        save_meta(db)
        
    return entry

def update_story_meta(rel_path, title, synopsis, tags, rating=0, format_type="star_rp", background_file=None):
    db = load_meta()
    if rel_path not in db: db[rel_path] = {}
    
    db[rel_path]["display_title"] = title
    db[rel_path]["synopsis"] = synopsis
    db[rel_path]["tags"] = tags
    db[rel_path]["rating"] = int(rating)
    db[rel_path]["format_type"] = format_type
    
    if background_file: 
        db[rel_path]["background_file"] = background_file
        
    save_meta(db)

def save_story_background(rel_path, file_object, original_filename):
    ext = os.path.splitext(original_filename)[1]
    safe_name = hashlib.md5(rel_path.encode()).hexdigest() + ext
    file_path = os.path.join(BACKGROUND_DIR, safe_name)
    
    with open(file_path, "wb+") as dest:
        shutil.copyfileobj(file_object, dest)
        
    db = load_meta()
    if rel_path not in db: get_story_meta(rel_path)
    db = load_meta() # Reload to be safe
    db[rel_path]["background_file"] = safe_name
    save_meta(db)
    return safe_name

# ---------------------------------------------------------
# ORACLE: SEARCH ENGINE
# ---------------------------------------------------------
def search_stories(query):
    results = []
    query = query.lower()
    all_files = get_all_stories_flat()
    
    for rel_path in all_files:
        full_path = os.path.join(STORY_DIR, rel_path)
        matches = []
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    if query in line.lower():
                        clean_line = line.strip()
                        # Truncate extremely long lines for display
                        if len(clean_line) > 150:
                            idx = clean_line.lower().find(query)
                            start = max(0, idx - 50)
                            end = min(len(clean_line), idx + 100)
                            clean_line = "..." + clean_line[start:end] + "..."
                        matches.append(clean_line)
                        if len(matches) >= 3: break # Limit matches per file
            if matches:
                meta = get_story_meta(rel_path)
                results.append({
                    "path": rel_path, 
                    "title": meta.get("display_title", rel_path), 
                    "matches": matches
                })
        except: continue
    return results

# ---------------------------------------------------------
# FILE OPERATIONS
# ---------------------------------------------------------
def get_campaigns():
    items = os.listdir(STORY_DIR)
    campaigns = [d for d in items if os.path.isdir(os.path.join(STORY_DIR, d))]
    return ["Unsorted"] + campaigns

def create_campaign(name):
    safe_name = "".join([c for c in name if c.isalnum() or c in " _-"]).strip()
    path = os.path.join(STORY_DIR, safe_name)
    if not os.path.exists(path): os.makedirs(path)

def list_stories_by_campaign():
    structure = {"Unsorted": []}
    for f in os.listdir(STORY_DIR):
        if f.endswith(".txt"): structure["Unsorted"].append(f)
    
    campaigns = get_campaigns()
    for camp in campaigns:
        if camp == "Unsorted": continue
        camp_path = os.path.join(STORY_DIR, camp)
        structure[camp] = []
        for f in os.listdir(camp_path):
            if f.endswith(".txt"): structure[camp].append(os.path.join(camp, f))
    return structure

def get_all_stories_flat():
    files = []
    # Root
    for f in os.listdir(STORY_DIR):
        if f.endswith(".txt"): files.append(f)
    # Campaigns
    for d in os.listdir(STORY_DIR):
        d_path = os.path.join(STORY_DIR, d)
        if os.path.isdir(d_path):
            for f in os.listdir(d_path):
                if f.endswith(".txt"): files.append(os.path.join(d, f))
    return files

def get_recent_stories(limit=5):
    all_files = get_all_stories_flat()
    all_files.sort(key=lambda x: os.path.getmtime(os.path.join(STORY_DIR, x)), reverse=True)
    return all_files[:limit]

def get_total_story_count():
    return len(get_all_stories_flat())

def move_story_to_campaign(current_rel_path, target_campaign):
    src_path = os.path.join(STORY_DIR, current_rel_path)
    filename = os.path.basename(current_rel_path)
    if target_campaign == "Unsorted":
        dest_rel = filename
        dest_path = os.path.join(STORY_DIR, filename)
    else:
        dest_rel = os.path.join(target_campaign, filename)
        dest_path = os.path.join(STORY_DIR, target_campaign, filename)
        
    if src_path != dest_path:
        shutil.move(src_path, dest_path)
        db = load_meta()
        if current_rel_path in db:
            db[dest_rel] = db.pop(current_rel_path)
            save_meta(db)
    return dest_rel

# ---------------------------------------------------------
# IMPORT SAVING
# ---------------------------------------------------------
def sanitize_filename(name):
    safe = "".join(c for c in name if c.isalnum() or c in " -_").strip()
    safe = safe.replace(" ", "_")
    return safe + ".txt"

def save_story_from_text(title, content):
    filename = sanitize_filename(title)
    file_path = os.path.join(STORY_DIR, filename)
    base, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(file_path):
        file_path = os.path.join(STORY_DIR, f"{base}_{counter}{ext}")
        counter += 1
    with open(file_path, "w", encoding="utf-8") as f: f.write(content)
    return os.path.basename(file_path)

def save_story_from_file(file_object, original_filename):
    title_part = os.path.splitext(original_filename)[0]
    filename = sanitize_filename(title_part)
    file_path = os.path.join(STORY_DIR, filename)
    base, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(file_path):
        file_path = os.path.join(STORY_DIR, f"{base}_{counter}{ext}")
        counter += 1
    with open(file_path, "wb+") as dest: shutil.copyfileobj(file_object, dest)
    return os.path.basename(file_path)
