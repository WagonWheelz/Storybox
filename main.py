# main.py
import os
import json
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Template

# MODULE IMPORTS
import character_manager
import story_parser
import story_manager
import prompt_manager
from templates import HTML_TEMPLATE_STRING # IMPORT THE HTML

app = FastAPI()

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(story_manager.STORY_DIR, exist_ok=True)
os.makedirs(character_manager.AVATAR_DIR, exist_ok=True)
os.makedirs(character_manager.GALLERY_DIR, exist_ok=True)
os.makedirs(story_manager.BACKGROUND_DIR, exist_ok=True)

app.mount("/avatars", StaticFiles(directory=character_manager.AVATAR_DIR), name="avatars")
app.mount("/gallery", StaticFiles(directory=character_manager.GALLERY_DIR), name="gallery")
app.mount("/backgrounds", StaticFiles(directory=story_manager.BACKGROUND_DIR), name="backgrounds")

jinja_template = Template(HTML_TEMPLATE_STRING)

# --------------------------------------------------------------------------
# ROUTES
# --------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    total_stories = story_manager.get_total_story_count()
    all_chars = character_manager.get_all_characters()
    all_prompts = prompt_manager.get_all_prompts()
    campaigns = story_manager.get_campaigns()
    recent_files = story_manager.get_recent_stories(limit=5)
    recent_data = []
    for rel_path in recent_files:
        full_path = os.path.join(story_manager.STORY_DIR, rel_path)
        recent_data.append({
            "path": rel_path,
            "meta": story_manager.get_story_meta(rel_path),
            "stats": story_parser.get_file_stats(full_path)
        })
    stats = {
        "total_stories": total_stories,
        "total_chars": len(all_chars),
        "total_campaigns": len(campaigns) - 1,
        "total_prompts": len(all_prompts)
    }
    return jinja_template.render(
        mode="dashboard", 
        stats=stats, 
        recent_stories=recent_data, 
        campaigns=campaigns
    )

@app.get("/stories", response_class=HTMLResponse)
async def stories_list(request: Request):
    active_campaign = request.query_params.get("campaign", None)
    structure = story_manager.list_stories_by_campaign()
    target_files = []
    if active_campaign and active_campaign in structure: 
        target_files = structure[active_campaign]
    else:
        for camp_name, files in structure.items(): 
            target_files.extend(files)
    
    stories_data = []
    for rel_path in target_files:
        full_path = os.path.join(story_manager.STORY_DIR, rel_path)
        stories_data.append({
            "path": rel_path, 
            "meta": story_manager.get_story_meta(rel_path), 
            "stats": story_parser.get_file_stats(full_path)
        })
    return jinja_template.render(
        mode="stories_list", 
        campaigns=story_manager.get_campaigns(), 
        active_campaign=active_campaign, 
        stories=stories_data
    )

@app.get("/prompts", response_class=HTMLResponse)
async def prompts_list(request: Request):
    prompts = prompt_manager.get_all_prompts()
    all_chars = character_manager.get_all_characters()
    return jinja_template.render(mode="prompts_list", prompts=prompts, all_chars=all_chars)

@app.get("/search", response_class=HTMLResponse)
async def search_results(q: str):
    results = story_manager.search_stories(q)
    return jinja_template.render(mode="search", query=q, results=results)

@app.get("/characters", response_class=HTMLResponse)
async def char_list():
    all_chars = character_manager.get_all_characters()
    return jinja_template.render(mode="char_list", all_chars=all_chars)

@app.get("/character/{char_id}", response_class=HTMLResponse)
async def char_profile(char_id: str):
    char = character_manager.get_character(char_id)
    if not char: raise HTTPException(404, "Character not found")
    
    char['id'] = char_id
    linked_stories = character_manager.get_character_stories(char_id)
    assigned_prompts = prompt_manager.get_prompts_for_character(char_id)
    played_by_list = character_manager.get_players_for_character(char_id)
    
    return jinja_template.render(
        mode="char_profile", 
        char=char, 
        char_id=char_id, 
        stories=linked_stories, 
        assigned_prompts=assigned_prompts, 
        played_by_list=played_by_list
    )

@app.get("/read/{path:path}", response_class=HTMLResponse)
async def read_story(path: str):
    full_path = os.path.join(story_manager.STORY_DIR, path)
    if not os.path.exists(full_path): raise HTTPException(404, "File not found")
    
    meta = story_manager.get_story_meta(path)
    format_type = meta.get("format_type", "star_rp")
    background_file = meta.get("background_file")
    
    blocks, local_stats = story_parser.parse_file(full_path, format_type=format_type)
    characters = character_manager.get_cast_for_story(path, local_stats)
    all_db_chars = character_manager.get_all_characters()
    char_map = {c['raw_name']: c for c in characters}
    player_map = character_manager.get_story_player_map(path)
    
    return jinja_template.render(
        mode="read", 
        blocks=blocks, 
        characters=characters, 
        all_db_chars=all_db_chars, 
        filename=path, 
        char_map=char_map, 
        background_file=background_file, 
        player_map=player_map
    )

@app.get("/edit_story/{path:path}", response_class=HTMLResponse)
async def edit_story_view(path: str):
    content = story_manager.read_raw_story(path)
    return jinja_template.render(mode="edit_story", filename=path, content=content)

@app.post("/save_story_text")
async def save_story_text(path: str = Form(...), content: str = Form(...)):
    story_manager.overwrite_story_content(path, content)
    return RedirectResponse(url=f"/read/{path}", status_code=303)

# --- ACTIONS ---

@app.post("/create_campaign")
async def create_campaign(name: str = Form(...)):
    story_manager.create_campaign(name)
    return RedirectResponse(url="/", status_code=303)

@app.post("/update_story_meta")
async def update_story_meta(
    current_path: str = Form(...), title: str = Form(...), synopsis: str = Form(""), 
    tags: str = Form(""), campaign: str = Form(...), rating: int = Form(0), format_type: str = Form("star_rp")
):
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    story_manager.update_story_meta(current_path, title, synopsis, tag_list, rating=rating, format_type=format_type)
    
    parts = current_path.replace("\\", "/").split("/")
    current_camp = parts[0] if len(parts) > 1 else "Unsorted"
    if campaign != current_camp: 
        story_manager.move_story_to_campaign(current_path, campaign)
        
    return RedirectResponse(url="/", status_code=303)

@app.post("/upload_story_background")
async def upload_story_background(return_path: str = Form(...), file: UploadFile = File(...)):
    if file.filename: 
        story_manager.save_story_background(return_path, file.file, file.filename)
    return RedirectResponse(url=f"/read/{return_path}", status_code=303)

@app.post("/create_character_quick")
async def create_character_quick(name: str = Form(...)):
    new_id = character_manager.create_character(name)
    return RedirectResponse(url=f"/character/{new_id}", status_code=303)

@app.post("/link_character")
async def link_character(filename: str = Form(...), raw_name: str = Form(...), char_id: str = Form(...)):
    if char_id == "NEW": 
        char_id = character_manager.create_character(raw_name)
    character_manager.update_story_map(filename, raw_name, char_id)
    return RedirectResponse(url=f"/read/{filename}", status_code=303)

@app.post("/update_character_details")
async def update_character_details(
    char_id: str = Form(...), name: str = Form(...), description: str = Form(""),
    return_file: str = Form(None), bubble_color: str = Form("#1e293b"),
    avatar: Optional[UploadFile] = File(None),
    attr_keys: List[str] = Form([]), attr_values: List[str] = Form([])
):
    avatar_filename = None
    if avatar and avatar.filename: 
        avatar_filename = character_manager.save_avatar(char_id, avatar.file, avatar.filename)
    
    attributes = {}
    for k, v in zip(attr_keys, attr_values):
        if k.strip() and v.strip(): 
            attributes[k.strip()] = v.strip()
            
    character_manager.update_character_data(char_id, name, description, attributes, bubble_color, avatar_filename)
    
    if return_file: return RedirectResponse(url=f"/read/{return_file}", status_code=303)
    else: return RedirectResponse(url=f"/character/{char_id}", status_code=303)

@app.post("/upload_gallery")
async def upload_gallery(char_id: str = Form(...), image: UploadFile = File(...)):
    if image.filename: 
        character_manager.add_gallery_image(char_id, image.file, image.filename)
    return RedirectResponse(url=f"/character/{char_id}", status_code=303)

@app.post("/delete_character")
async def delete_char_endpoint(char_id: str = Form(...)):
    character_manager.delete_character(char_id)
    return RedirectResponse(url="/characters", status_code=303)

@app.get("/export_character/{char_id}")
async def export_character(char_id: str):
    png_buffer = character_manager.export_character_card(char_id)
    if not png_buffer: raise HTTPException(404, "Character not found")
    
    char_name = character_manager.get_character(char_id).get("name", "character")
    safe_name = "".join(c for c in char_name if c.isalnum() or c in " _-").strip()
    return StreamingResponse(png_buffer, media_type="image/png", headers={"Content-Disposition": f"attachment; filename={safe_name}.png"})

@app.post("/import_character")
async def import_character(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".png"): 
        raise HTTPException(400, "Only PNG files allowed")
    
    contents = await file.read()
    new_id = character_manager.import_character_card(contents)
    if not new_id: raise HTTPException(400, "Invalid Character Card")
    return RedirectResponse(url=f"/character/{new_id}", status_code=303)

@app.post("/import_story_file")
async def import_story_file(file: UploadFile = File(...), campaign: str = Form(...)):
    if not (file.filename.lower().endswith(".txt") or file.filename.lower().endswith(".json")):
        raise HTTPException(400, "Only .txt and .json files allowed")
        
    filename = story_manager.save_story_from_file(file.file, file.filename)
    if campaign != "Unsorted": 
        story_manager.move_story_to_campaign(filename, campaign)
    return RedirectResponse(url="/stories", status_code=303)

@app.post("/import_story_text")
async def import_story_text(title: str = Form(...), content: str = Form(...), campaign: str = Form(...)):
    filename = story_manager.save_story_from_text(title, content)
    if campaign != "Unsorted": 
        story_manager.move_story_to_campaign(filename, campaign)
    return RedirectResponse(url="/stories", status_code=303)

@app.post("/create_prompt")
async def create_prompt(title: str = Form(...), content: str = Form(...), tags: str = Form(""), linked_chars: List[str] = Form([])):
    tag_list = tags.split(",")
    prompt_manager.create_prompt(title, content, tag_list, linked_chars)
    return RedirectResponse(url="/prompts", status_code=303)

@app.post("/delete_prompt")
async def delete_prompt(pid: str = Form(...)):
    prompt_manager.delete_prompt(pid)
    return RedirectResponse(url="/prompts", status_code=303)

@app.post("/set_story_player")
async def set_story_player(filename: str = Form(...), char_id: str = Form(...), player_name: str = Form("")):
    character_manager.update_story_player_map(filename, char_id, player_name)
    return RedirectResponse(url=f"/read/{filename}", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, loop="asyncio")
