import os
import json
import hashlib
import shutil
import uuid
import base64
import io
from PIL import Image
from PIL.PngImagePlugin import PngInfo

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
AVATAR_DIR = os.path.join(BASE_DIR, "avatars")
GALLERY_DIR = os.path.join(BASE_DIR, "gallery")
CHAR_DB_FILE = os.path.join(DATA_DIR, "characters.json")
MAP_DB_FILE = os.path.join(DATA_DIR, "story_map.json")
PLAYER_MAP_DB_FILE = os.path.join(DATA_DIR, "story_player_map.json") # NEW DB

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(AVATAR_DIR, exist_ok=True)
os.makedirs(GALLERY_DIR, exist_ok=True)

# ---------------------------------------------------------
# DB OPS
# ---------------------------------------------------------
def sanitize_data(data):
    dirty = False
    cleaned_data = {}
    for key, val in data.items():
        if not isinstance(val, dict): 
            val = {"name": key, "description": "", "attributes": {}}
            dirty = True
        
        if "name" not in val or not val["name"]: val["name"] = key; dirty = True
        if "attributes" not in val: val["attributes"] = {}; dirty = True
        if "gallery" not in val: val["gallery"] = []; dirty = True
        if "bubble_color" not in val: val["bubble_color"] = "#1e293b"; dirty = True
            
        cleaned_data[key] = val
        
    if dirty: save_json(CHAR_DB_FILE, cleaned_data)
    return cleaned_data

def load_json(filepath):
    if not os.path.exists(filepath): return {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if filepath == CHAR_DB_FILE: return sanitize_data(data)
            return data
    except: return {}

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)

# ---------------------------------------------------------
# PLAYER MAPPING (NEW)
# ---------------------------------------------------------
def get_story_player_map(filename):
    """Returns {char_id: player_name} for a specific story."""
    full_map = load_json(PLAYER_MAP_DB_FILE)
    return full_map.get(filename, {})

def update_story_player_map(filename, char_id, player_name):
    """Sets the player name for a character in a specific story."""
    full_map = load_json(PLAYER_MAP_DB_FILE)
    if filename not in full_map: full_map[filename] = {}
    
    if player_name and player_name.strip():
        full_map[filename][char_id] = player_name.strip()
    else:
        # Remove if empty to keep DB clean
        if char_id in full_map[filename]:
            del full_map[filename][char_id]
            
    save_json(PLAYER_MAP_DB_FILE, full_map)

def get_players_for_character(char_id):
    """Returns a list of unique usernames who have played this character across all stories."""
    full_map = load_json(PLAYER_MAP_DB_FILE)
    players = set()
    for filename, char_map in full_map.items():
        if char_id in char_map:
            players.add(char_map[char_id])
    return sorted(list(players))

# ---------------------------------------------------------
# CHARACTER LOGIC
# ---------------------------------------------------------
def create_character(name):
    char_id = str(uuid.uuid4())
    db = load_json(CHAR_DB_FILE)
    db[char_id] = {
        "name": name, "description": "",
        "attributes": {"Age": "Unknown", "Gender": "Unknown", "Race": "Unknown", "Orientation": "Unknown"},
        "avatar_file": None, "gallery": [], "bubble_color": "#1e293b"
    }
    save_json(CHAR_DB_FILE, db)
    return char_id

def get_character(char_id):
    db = load_json(CHAR_DB_FILE)
    return db.get(char_id)

def get_all_characters():
    return load_json(CHAR_DB_FILE)

def update_character_data(char_id, name, description, attributes, bubble_color, avatar_filename=None):
    db = load_json(CHAR_DB_FILE)
    if char_id in db:
        db[char_id]["name"] = name
        db[char_id]["description"] = description
        db[char_id]["attributes"] = attributes
        db[char_id]["bubble_color"] = bubble_color
        if avatar_filename: db[char_id]["avatar_file"] = avatar_filename
        save_json(CHAR_DB_FILE, db)

def delete_character(char_id):
    db = load_json(CHAR_DB_FILE)
    if char_id in db:
        del db[char_id]
        save_json(CHAR_DB_FILE, db)

# ---------------------------------------------------------
# IMAGES
# ---------------------------------------------------------
def get_avatar_color(name):
    if not name: return "#333"
    hash_object = hashlib.md5(name.encode())
    return "#" + hash_object.hexdigest()[:6]

def save_avatar(char_id, file_object, original_filename):
    ext = os.path.splitext(original_filename)[1]
    safe_filename = f"{char_id}_avatar{ext}"
    file_location = os.path.join(AVATAR_DIR, safe_filename)
    with open(file_location, "wb+") as dest: shutil.copyfileobj(file_object, dest)
    return safe_filename

def add_gallery_image(char_id, file_object, original_filename):
    ext = os.path.splitext(original_filename)[1]
    img_id = str(uuid.uuid4())[:8]
    safe_filename = f"{char_id}_{img_id}{ext}"
    file_location = os.path.join(GALLERY_DIR, safe_filename)
    with open(file_location, "wb+") as dest: shutil.copyfileobj(file_object, dest)
    db = load_json(CHAR_DB_FILE)
    if char_id in db:
        if "gallery" not in db[char_id]: db[char_id]["gallery"] = []
        db[char_id]["gallery"].append(safe_filename)
        save_json(CHAR_DB_FILE, db)

# ---------------------------------------------------------
# EXPORT / IMPORT
# ---------------------------------------------------------
def export_character_card(char_id):
    try:
        char_data = get_character(char_id)
        if not char_data: return None
        img = None
        if char_data.get("avatar_file"):
            path = os.path.join(AVATAR_DIR, char_data["avatar_file"])
            if os.path.exists(path):
                try: img = Image.open(path).convert("RGBA")
                except: img = None
        if not img: img = Image.new('RGB', (400, 600), color=get_avatar_color(char_data.get('name')))
        name = char_data.get('name', 'Unknown')
        desc = char_data.get('description') or ""
        attrs = char_data.get('attributes') or {}
        bubble_color = char_data.get('bubble_color', '#1e293b')
        attr_text = "\n".join([f"{k}: {v}" for k, v in attrs.items()])
        full_desc = f"{desc}\n\n[Attributes]\n{attr_text}"
        card_data = {
            "spec": "chara_card_v2", "spec_version": "2.0",
            "data": {
                "name": name, "description": full_desc, "creator_notes": "Exported from StoryStash",
                "extensions": {"storystash": {"raw_attributes": attrs, "raw_description": desc, "bubble_color": bubble_color}}
            }
        }
        json_str = json.dumps(card_data)
        base64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        metadata = PngInfo()
        metadata.add_text("chara", base64_str)
        output_buffer = io.BytesIO()
        img.save(output_buffer, format="PNG", pnginfo=metadata)
        output_buffer.seek(0)
        return output_buffer
    except Exception as e:
        print(f"Export Error: {e}")
        return None

def import_character_card(file_bytes):
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.load() 
        raw_data = img.info.get("chara")
        if not raw_data: return None
        decoded_json = base64.b64decode(raw_data).decode('utf-8')
        card_json = json.loads(decoded_json)
        data_block = card_json.get("data", card_json)
        new_id = str(uuid.uuid4())
        name = data_block.get("name", "Imported Character")
        extensions = data_block.get("extensions", {})
        if "storystash" in extensions:
            desc = extensions["storystash"].get("raw_description", "")
            attrs = extensions["storystash"].get("raw_attributes", {})
            bubble_color = extensions["storystash"].get("bubble_color", "#1e293b")
        else:
            desc = data_block.get("description", "")
            attrs = {"Age": "Unknown"}
            bubble_color = "#1e293b"
        avatar_filename = f"{new_id}_avatar.png"
        img.save(os.path.join(AVATAR_DIR, avatar_filename), format="PNG")
        db = load_json(CHAR_DB_FILE)
        db[new_id] = {
            "name": name, "description": desc, "attributes": attrs,
            "avatar_file": avatar_filename, "gallery": [], "bubble_color": bubble_color
        }
        save_json(CHAR_DB_FILE, db)
        return new_id
    except: return None

# ---------------------------------------------------------
# MAPPING
# ---------------------------------------------------------
def get_story_map(filename):
    filename = filename.replace("\\", "/")
    full_map = load_json(MAP_DB_FILE)
    return full_map.get(filename, {})

def update_story_map(filename, raw_name, char_id):
    filename = filename.replace("\\", "/")
    full_map = load_json(MAP_DB_FILE)
    if filename not in full_map: full_map[filename] = {}
    full_map[filename][raw_name] = char_id
    save_json(MAP_DB_FILE, full_map)

def get_character_stories(char_id):
    full_map = load_json(MAP_DB_FILE)
    found_stories = []
    for filename, mapping in full_map.items():
        if char_id in mapping.values(): found_stories.append(filename)
    return found_stories

def get_cast_for_story(filename, local_stats):
    char_db = load_json(CHAR_DB_FILE)
    story_map = get_story_map(filename)
    final_cast = []
    sorted_raw_names = sorted(local_stats.keys(), key=lambda n: local_stats[n], reverse=True)
    for raw_name in sorted_raw_names:
        mapped_id = story_map.get(raw_name)
        char_obj = {
            "raw_name": raw_name, "msg_count": local_stats[raw_name], "id": None,
            "display_name": raw_name, "description": "", "attributes": {}, "avatar_url": None,
            "color": get_avatar_color(raw_name), "bubble_color": "#1e293b"
        }
        if mapped_id and mapped_id in char_db:
            db_char = char_db[mapped_id]
            char_obj["id"] = mapped_id
            char_obj["display_name"] = db_char.get("name", raw_name)
            char_obj["description"] = db_char.get("description", "")
            char_obj["attributes"] = db_char.get("attributes", {})
            char_obj["bubble_color"] = db_char.get("bubble_color", "#1e293b")
            if db_char.get("avatar_file"): char_obj["avatar_url"] = f"/avatars/{db_char['avatar_file']}"
        final_cast.append(char_obj)
    return final_cast
