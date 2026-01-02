import os
import json
import shutil
from datetime import datetime

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORY_DIR = os.path.join(BASE_DIR, "stories")
DATA_DIR = os.path.join(BASE_DIR, "data")
META_DB_FILE = os.path.join(DATA_DIR, "stories_meta.json")

os.makedirs(STORY_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

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
    """Retrieves metadata for a specific file path (e.g., 'Campaign1/session1.txt')."""
    db = load_meta()
    if rel_path not in db:
        # Create default entry if missing
        db[rel_path] = {
            "display_title": os.path.basename(rel_path).replace(".txt", ""),
            "synopsis": "No synopsis written.",
            "tags": [],
            "created_at": datetime.now().strftime("%Y-%m-%d")
        }
        save_meta(db)
    return db[rel_path]

def update_story_meta(rel_path, title, synopsis, tags):
    db = load_meta()
    if rel_path not in db: db[rel_path] = {}
    
    db[rel_path]["display_title"] = title
    db[rel_path]["synopsis"] = synopsis
    db[rel_path]["tags"] = tags
    save_meta(db)

# ---------------------------------------------------------
# CAMPAIGN / FILE OPERATIONS
# ---------------------------------------------------------
def get_campaigns():
    """Returns a list of folder names in the stories directory."""
    items = os.listdir(STORY_DIR)
    campaigns = [d for d in items if os.path.isdir(os.path.join(STORY_DIR, d))]
    return ["Unsorted"] + campaigns

def create_campaign(name):
    """Creates a new folder."""
    safe_name = "".join([c for c in name if c.isalnum() or c in " _-"]).strip()
    path = os.path.join(STORY_DIR, safe_name)
    if not os.path.exists(path):
        os.makedirs(path)

def list_stories_by_campaign():
    """
    Returns a dict structure:
    { 
      "Unsorted": [file1, file2], 
      "D&D": [file3] 
    }
    """
    structure = {"Unsorted": []}
    
    # 1. Get root files (Unsorted)
    for f in os.listdir(STORY_DIR):
        if f.endswith(".txt"):
            structure["Unsorted"].append(f)
            
    # 2. Get Campaign folders
    campaigns = get_campaigns()
    for camp in campaigns:
        if camp == "Unsorted": continue
        camp_path = os.path.join(STORY_DIR, camp)
        structure[camp] = []
        for f in os.listdir(camp_path):
            if f.endswith(".txt"):
                # Store relative path: "CampaignName/filename.txt"
                structure[camp].append(os.path.join(camp, f))
                
    return structure

def move_story_to_campaign(current_rel_path, target_campaign):
    """Moves a .txt file into a campaign folder."""
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
        
        # MIGRATE METADATA KEY
        db = load_meta()
        if current_rel_path in db:
            db[dest_rel] = db.pop(current_rel_path)
            save_meta(db)
            
    return dest_rel