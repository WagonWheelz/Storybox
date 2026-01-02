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

app = FastAPI()

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(story_manager.STORY_DIR, exist_ok=True)
os.makedirs(character_manager.AVATAR_DIR, exist_ok=True)
os.makedirs(character_manager.GALLERY_DIR, exist_ok=True)

app.mount("/avatars", StaticFiles(directory=character_manager.AVATAR_DIR), name="avatars")
app.mount("/gallery", StaticFiles(directory=character_manager.GALLERY_DIR), name="gallery")

# --------------------------------------------------------------------------
# HTML COMPONENTS (MODALS)
# --------------------------------------------------------------------------
MODALS_HTML = """
<dialog id="campaignModal" class="rounded-xl bg-slate-900 border border-slate-700 text-gray-200 w-96 backdrop:bg-black/80">
    <form action="/create_campaign" method="post" class="p-6">
        <h2 class="text-lg font-bold text-indigo-400 mb-4">New Campaign</h2>
        <input type="text" name="name" placeholder="Campaign Name" class="input-dark mb-4" required>
        <div class="flex justify-end gap-2"><button type="button" onclick="this.closest('dialog').close()" class="text-gray-400 text-sm px-3 py-2">Cancel</button><button type="submit" class="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-bold">Create</button></div>
    </form>
</dialog>

<dialog id="storyMetaModal" class="rounded-xl bg-slate-900 border border-slate-700 text-gray-200 w-[500px] backdrop:bg-black/80">
    <form action="/update_story_meta" method="post" class="flex flex-col h-full">
        <div class="p-6 border-b border-slate-800"><h2 class="text-lg font-bold text-indigo-400">Edit Details</h2><input type="hidden" name="current_path" id="metaPathInput"></div>
        <div class="p-6 space-y-4">
            <div><label class="text-xs font-bold text-gray-500 uppercase">Display Title</label><input type="text" name="title" id="metaTitleInput" class="input-dark mt-1"></div>
            <div><label class="text-xs font-bold text-gray-500 uppercase">Synopsis</label><textarea name="synopsis" id="metaSynopsisInput" rows="3" class="input-dark mt-1"></textarea></div>
            <div><label class="text-xs font-bold text-gray-500 uppercase">Tags</label><input type="text" name="tags" id="metaTagsInput" class="input-dark mt-1"></div>
            <div><label class="text-xs font-bold text-gray-500 uppercase">Campaign</label><select name="campaign" id="metaCampaignInput" class="input-dark mt-1">{% for camp in campaigns %}<option value="{{ camp }}">{{ camp }}</option>{% endfor %}</select></div>
        </div>
        <div class="p-4 border-t border-slate-800 flex justify-end gap-2 bg-slate-900"><button type="button" onclick="this.closest('dialog').close()" class="text-gray-400 text-sm px-3 py-2">Cancel</button><button type="submit" class="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-bold">Save</button></div>
    </form>
</dialog>

<dialog id="editModal" class="rounded-xl shadow-2xl bg-slate-900 border border-slate-700 text-gray-200 w-[500px] backdrop:bg-black/80 max-h-[90vh]">
    <form action="/update_character_details" method="post" enctype="multipart/form-data" class="flex flex-col h-full">
        <div class="p-6 border-b border-slate-800 bg-slate-900 sticky top-0 z-10">
            <h2 class="text-lg font-bold text-indigo-400">Edit <span id="modalCharNameDisplay"></span></h2>
            <input type="hidden" id="modalCharIdInput" name="char_id" value="">
            <input type="hidden" name="return_file" value="{{ filename or '' }}">
        </div>

        <div class="p-6 overflow-y-auto space-y-4">
            <div><label class="text-xs text-gray-500 uppercase font-bold">Display Name</label><input type="text" id="modalNameInput" name="name" class="input-dark mt-1"></div>
            <div><label class="text-xs text-gray-500 uppercase font-bold">Avatar</label><input type="file" name="avatar" accept="image/*" class="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-indigo-900 file:text-indigo-300 hover:file:bg-indigo-800 cursor-pointer mt-2 bg-slate-950 rounded border border-slate-700 p-1"/></div>
            <div><label class="text-xs text-gray-500 uppercase font-bold">Bio</label><textarea name="description" id="modalDescription" rows="3" class="input-dark mt-1"></textarea></div>
            
            <div class="p-3 bg-slate-950 rounded border border-slate-800">
                <label class="text-xs text-gray-500 uppercase font-bold block mb-2">Core Stats</label>
                <div class="grid grid-cols-2 gap-2">
                    <input type="text" name="attr_keys" value="Age" class="hidden">
                    <input type="text" id="modalAge" name="attr_values" placeholder="Age" class="input-dark text-xs">
                    <input type="text" name="attr_keys" value="Gender" class="hidden">
                    <input type="text" id="modalGender" name="attr_values" placeholder="Gender" class="input-dark text-xs">
                    <input type="text" name="attr_keys" value="Race" class="hidden">
                    <input type="text" id="modalRace" name="attr_values" placeholder="Race" class="input-dark text-xs">
                    <input type="text" name="attr_keys" value="Orientation" class="hidden">
                    <input type="text" id="modalOrient" name="attr_values" placeholder="Orientation" class="input-dark text-xs">
                </div>
            </div>

            <div>
                <div class="flex justify-between items-center mb-2"><label class="text-xs text-gray-500 uppercase font-bold">Extra Attributes</label><button type="button" onclick="addAttrRow()" class="text-xs bg-indigo-900 text-indigo-300 px-2 py-1 rounded hover:bg-indigo-800 transition"><i class="fas fa-plus mr-1"></i> Add</button></div>
                <div id="attributesContainer" class="space-y-2"></div>
            </div>
        </div>
        <div class="p-4 border-t border-slate-800 flex justify-end gap-2 bg-slate-900 sticky bottom-0">
            <button type="button" onclick="document.getElementById('editModal').close()" class="px-4 py-2 text-sm text-gray-400 hover:text-white transition">Cancel</button>
            <button type="submit" class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded text-sm font-bold">Save Changes</button>
        </div>
    </form>
</dialog>

<dialog id="castModal" class="rounded-xl shadow-2xl bg-slate-900 border border-slate-700 text-gray-200 w-[600px] backdrop:bg-black/80">
    <div class="p-6 border-b border-slate-800 flex justify-between items-center"><h2 class="text-lg font-bold text-indigo-400">Manage Cast</h2><button onclick="document.getElementById('castModal').close()" class="text-gray-500 hover:text-white"><i class="fas fa-times"></i></button></div>
    <div class="p-6 max-h-[70vh] overflow-y-auto">
        <table class="w-full text-left text-sm">
            <thead class="text-xs text-gray-500 uppercase border-b border-slate-700"><tr><th class="py-2">Name in Story</th><th class="py-2">Database Character</th></tr></thead>
            <tbody class="divide-y divide-slate-800">
                {% for char in characters %}
                <tr>
                    <td class="py-3 font-bold text-gray-300">{{ char.raw_name }}</td>
                    <td class="py-3">
                        <form action="/link_character" method="POST" class="flex gap-2">
                            <input type="hidden" name="filename" value="{{ filename }}">
                            <input type="hidden" name="raw_name" value="{{ char.raw_name }}">
                            <select name="char_id" class="input-dark text-xs py-1">
                                <option value="">-- Unlinked --</option>
                                <option value="NEW">➕ Create New</option>
                                {% for db_id, db_data in all_db_chars.items() %}<option value="{{ db_id }}" {% if char.id == db_id %}selected{% endif %}>{{ db_data.get('name', 'Unknown') }}</option>{% endfor %}
                            </select>
                            <button type="submit" class="bg-indigo-900 hover:bg-indigo-700 text-indigo-200 px-2 rounded text-xs">Save</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</dialog>

<script>
    function openStoryMetaModal(item) {
        document.getElementById('metaPathInput').value = item.path;
        document.getElementById('metaTitleInput').value = item.meta.display_title;
        document.getElementById('metaSynopsisInput').value = item.meta.synopsis;
        document.getElementById('metaTagsInput').value = item.meta.tags.join(", ");
        const parts = item.path.split('/');
        const currentCamp = parts.length > 1 ? parts[0] : "Unsorted";
        document.getElementById('metaCampaignInput').value = currentCamp;
        document.getElementById('storyMetaModal').showModal();
    }

    function openEditModal(charData) {
        const name = charData.display_name || charData.name || "Unknown";
        document.getElementById('modalCharNameDisplay').innerText = name;
        document.getElementById('modalNameInput').value = name;
        document.getElementById('modalCharIdInput').value = charData.id;
        document.getElementById('modalDescription').value = charData.description || '';
        const attrs = charData.attributes || {};
        document.getElementById('modalAge').value = attrs.Age || '';
        document.getElementById('modalGender').value = attrs.Gender || '';
        document.getElementById('modalRace').value = attrs.Race || '';
        document.getElementById('modalOrient').value = attrs.Orientation || '';
        const container = document.getElementById('attributesContainer');
        container.innerHTML = '';
        const standard = ['Age', 'Gender', 'Race', 'Orientation'];
        for (const [key, value] of Object.entries(attrs)) {
            if (!standard.includes(key)) { addAttrRow(key, value); }
        }
        document.getElementById('editModal').showModal();
    }

    function addAttrRow(key = '', value = '') {
        const container = document.getElementById('attributesContainer');
        const div = document.createElement('div');
        div.className = 'flex gap-2 items-center';
        div.innerHTML = `
            <input type="text" name="attr_keys" value="${key}" placeholder="Label" class="input-dark w-1/3 text-xs font-bold text-indigo-300">
            <input type="text" name="attr_values" value="${value}" placeholder="Value" class="input-dark flex-1">
            <button type="button" onclick="this.parentElement.remove()" class="text-red-500 hover:text-red-400 px-2"><i class="fas fa-times"></i></button>
        `;
        container.appendChild(div);
    }
</script>
"""

# --------------------------------------------------------------------------
# MAIN HTML TEMPLATE
# --------------------------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html class="dark">
<head>
    <title>StoryStash RP</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" />
    <style>
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
        .sidebar-container { position: sticky; top: 20px; max-height: 90vh; overflow-y: auto; }
        dialog::backdrop { background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(2px); }
        dialog { background: transparent; border: none; padding: 0; max-width: 100%; color: inherit; }
        .input-dark { background-color: #020617; border: 1px solid #334155; color: #e2e8f0; padding: 0.5rem; border-radius: 0.375rem; font-size: 0.875rem; width: 100%; outline: none; }
        .input-dark:focus { border-color: #6366f1; }
        .tag { font-size: 0.65rem; padding: 2px 6px; border-radius: 99px; text-transform: uppercase; font-weight: bold; letter-spacing: 0.05em; }
        .tag-blue { background: #1e3a8a; color: #93c5fd; border: 1px solid #3b82f6; }
        .tag-gray { background: #1f2937; color: #9ca3af; border: 1px solid #374151; }
    </style>
</head>
<body class="bg-slate-950 text-gray-200 font-sans h-screen flex flex-col">

    <header class="bg-slate-900 border-b border-slate-800 p-4 shadow-lg flex justify-between items-center z-10 shrink-0">
        <div class="flex items-center gap-6">
            <h1 class="text-xl font-bold text-indigo-400">StoryStash <span class="text-xs text-gray-500">Wiki</span></h1>
            <nav class="flex gap-4 text-sm font-medium">
                <a href="/" class="{{ 'text-white font-bold' if mode == 'dashboard' else 'text-gray-400 hover:text-white' }}">Dashboard</a>
                <a href="/characters" class="{{ 'text-white font-bold' if mode in ['char_list', 'char_profile'] else 'text-gray-400 hover:text-white' }}">Characters</a>
            </nav>
        </div>
        
        {% if mode == 'read' %}
        <button onclick="document.getElementById('castModal').showModal()" class="bg-slate-800 hover:bg-slate-700 text-gray-300 px-3 py-1 rounded text-sm border border-slate-700">
            <i class="fas fa-users-cog mr-2"></i> Manage Cast
        </button>
        {% endif %}
    </header>

    <main class="flex-1 overflow-hidden w-full flex justify-center p-6 gap-6 relative">
        
        {% if mode == 'dashboard' %}
            <aside class="w-64 shrink-0 bg-slate-900/50 rounded-xl border border-slate-800 p-4 h-full overflow-y-auto">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xs font-bold text-gray-500 uppercase tracking-widest">Campaigns</h2>
                    <button onclick="document.getElementById('campaignModal').showModal()" class="text-xs text-indigo-400 hover:text-indigo-300"><i class="fas fa-plus"></i></button>
                </div>
                <nav class="space-y-1">
                    <a href="/" class="block px-3 py-2 rounded text-sm {{ 'bg-indigo-900/50 text-indigo-200' if not active_campaign else 'text-gray-400 hover:bg-slate-800 hover:text-white' }}"><i class="fas fa-layer-group w-5"></i> All Stories</a>
                    {% for camp in campaigns %}
                        {% if camp != "Unsorted" %}
                        <a href="/?campaign={{ camp }}" class="block px-3 py-2 rounded text-sm {{ 'bg-indigo-900/50 text-indigo-200' if active_campaign == camp else 'text-gray-400 hover:bg-slate-800 hover:text-white' }}"><i class="fas fa-folder w-5 text-yellow-600"></i> {{ camp }}</a>
                        {% endif %}
                    {% endfor %}
                </nav>
            </aside>

            <div class="flex-1 h-full overflow-y-auto pr-2">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {% for item in stories %}
                    <div class="bg-slate-900 rounded-xl border border-slate-800 shadow-lg hover:border-indigo-500/50 transition flex flex-col h-[280px] group relative">
                        <button onclick='openStoryMetaModal({{ item | tojson }})' class="absolute top-2 right-2 z-10 text-gray-500 hover:text-indigo-400 opacity-0 group-hover:opacity-100 transition p-2"><i class="fas fa-cog"></i></button>
                        <a href="/read/{{ item.path }}" class="flex-1 flex flex-col p-5">
                            <div class="mb-3">
                                <h3 class="font-bold text-lg text-gray-100 leading-tight line-clamp-1" title="{{ item.meta.display_title }}">{{ item.meta.display_title }}</h3>
                                <div class="text-[10px] text-gray-500 mt-1 flex gap-2"><span><i class="far fa-clock"></i> {{ item.stats.date }}</span><span><i class="far fa-comment-alt"></i> {{ item.stats.msg_count }}</span></div>
                            </div>
                            <div class="flex-1 text-xs text-gray-400 italic line-clamp-4 leading-relaxed overflow-hidden">{{ item.meta.synopsis }}</div>
                            {% if item.stats.top_characters %}
                            <div class="mt-3 flex -space-x-2 overflow-hidden py-1">
                                {% for char in item.stats.top_characters %}
                                    <div class="inline-block h-6 w-6 rounded-full ring-2 ring-slate-900 bg-indigo-500 flex items-center justify-center text-[8px] font-bold text-white">{{ char[:1] }}</div>
                                {% endfor %}
                            </div>
                            {% endif %}
                        </a>
                        <div class="p-3 border-t border-slate-800 bg-slate-950/30 rounded-b-xl flex gap-2 overflow-x-auto">
                            {% if item.meta.tags %}{% for tag in item.meta.tags %}<span class="tag tag-blue">{{ tag }}</span>{% endfor %}{% else %}<span class="tag tag-gray">No Tags</span>{% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

        {% elif mode == 'char_list' %}
            <div class="flex-1 h-full overflow-y-auto">
                <div class="flex justify-between items-center mb-6">
                    <h2 class="text-2xl font-bold text-white">Character Database</h2>
                    
                    <div class="flex gap-4 items-center">
                        <form action="/import_character" method="post" enctype="multipart/form-data" class="flex gap-2">
                            <label class="cursor-pointer bg-slate-800 hover:bg-slate-700 text-gray-300 px-3 py-1 rounded text-sm border border-slate-700 font-medium">
                                <i class="fas fa-file-import mr-1"></i> Import Card (PNG)
                                <input type="file" name="file" accept=".png" class="hidden" onchange="this.form.submit()">
                            </label>
                        </form>

                        <form action="/create_character_quick" method="post" class="flex gap-2 border-l border-slate-700 pl-4">
                            <input type="text" name="name" placeholder="New Character Name" class="input-dark py-1 px-3 w-64" required>
                            <button type="submit" class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-1 rounded text-sm font-bold">Create</button>
                        </form>
                    </div>
                </div>

                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
                    {% for id, char in all_chars.items() %}
                    <a href="/character/{{ id }}" class="block bg-slate-900 rounded-xl border border-slate-800 overflow-hidden hover:border-indigo-500 hover:shadow-lg transition group">
                        <div class="aspect-square bg-slate-800 w-full relative">
                            {% if char.get('avatar_file') %}
                                <img src="/avatars/{{ char.avatar_file }}" class="w-full h-full object-cover">
                            {% else %}
                                <div class="w-full h-full flex items-center justify-center text-4xl font-bold text-white/20">{{ char.get('name', '?')[:1] }}</div>
                            {% endif %}
                            <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-3 pt-8">
                                <h3 class="font-bold text-white truncate">{{ char.get('name', 'Unknown') }}</h3>
                            </div>
                        </div>
                    </a>
                    {% endfor %}
                </div>
            </div>

        {% elif mode == 'char_profile' %}
            <div class="flex-1 h-full overflow-hidden flex gap-8">
                <aside class="w-80 shrink-0 h-full overflow-y-auto space-y-6">
                    <div class="bg-slate-900 rounded-xl border border-slate-800 p-6 flex flex-col items-center shadow-lg relative group">
                        
                        <button onclick='openEditModal({{ char | tojson }})' class="absolute top-2 right-2 text-gray-500 hover:text-indigo-400" title="Edit Profile"><i class="fas fa-pencil-alt"></i></button>

                        <form action="/delete_character" method="post" onsubmit="return confirm('Are you sure you want to delete this character? This cannot be undone.');">
                            <input type="hidden" name="char_id" value="{{ char_id }}">
                            <button type="submit" class="absolute top-2 left-2 text-gray-600 hover:text-red-500 transition" title="Delete Character"><i class="fas fa-trash"></i></button>
                        </form>
                        
                        <a href="/export_character/{{ char_id }}" target="_blank" class="absolute bottom-2 right-2 text-gray-600 hover:text-blue-400 transition" title="Export Card (PNG)">
                            <i class="fas fa-address-card"></i>
                        </a>

                        <div class="w-48 h-48 rounded-lg shadow-2xl border-2 border-slate-700 overflow-hidden mb-4 bg-slate-800">
                            {% if char.get('avatar_file') %}
                                <img src="/avatars/{{ char.avatar_file }}" class="w-full h-full object-cover">
                            {% else %}
                                <div class="w-full h-full flex items-center justify-center text-6xl font-bold text-white/20">{{ char.get('name', '?')[:1] }}</div>
                            {% endif %}
                        </div>
                        <h1 class="text-2xl font-bold text-white text-center">{{ char.get('name', 'Unknown') }}</h1>
                        <div class="w-full mt-6 space-y-3">
                            <div class="flex justify-between border-b border-slate-800 pb-1"><span class="text-xs uppercase text-gray-500 font-bold">Age</span><span class="text-sm text-gray-200">{{ char.attributes.get('Age', 'Unknown') }}</span></div>
                            <div class="flex justify-between border-b border-slate-800 pb-1"><span class="text-xs uppercase text-gray-500 font-bold">Gender</span><span class="text-sm text-gray-200">{{ char.attributes.get('Gender', 'Unknown') }}</span></div>
                            <div class="flex justify-between border-b border-slate-800 pb-1"><span class="text-xs uppercase text-gray-500 font-bold">Race</span><span class="text-sm text-gray-200">{{ char.attributes.get('Race', 'Unknown') }}</span></div>
                            <div class="flex justify-between border-b border-slate-800 pb-1"><span class="text-xs uppercase text-gray-500 font-bold">Orientation</span><span class="text-sm text-gray-200">{{ char.attributes.get('Orientation', 'Unknown') }}</span></div>
                            {% for key, val in char.attributes.items() %}
                                {% if key not in ['Age', 'Gender', 'Race', 'Orientation'] %}
                                <div class="flex justify-between border-b border-slate-800 pb-1"><span class="text-xs uppercase text-gray-500 font-bold truncate max-w-[100px]">{{ key }}</span><span class="text-sm text-gray-400 truncate">{{ val }}</span></div>
                                {% endif %}
                            {% endfor %}
                        </div>
                    </div>
                </aside>

                <div class="flex-1 h-full overflow-y-auto space-y-8 pr-4">
                    <section>
                        <h2 class="text-xl font-bold text-indigo-400 mb-2 border-b border-slate-800 pb-2">Biography</h2>
                        <div class="bg-slate-900/50 p-6 rounded-xl border border-slate-800 text-gray-300 leading-relaxed italic">
                            {{ char.description or "No biography written yet." }}
                        </div>
                    </section>
                    <section>
                        <h2 class="text-xl font-bold text-indigo-400 mb-2 border-b border-slate-800 pb-2">Appears In</h2>
                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {% for story_path in stories %}
                            <a href="/read/{{ story_path }}" class="block bg-slate-900 p-4 rounded-lg border border-slate-800 hover:border-indigo-500 transition"><i class="fas fa-file-alt text-indigo-500 mr-2"></i> {{ story_path }}</a>
                            {% endfor %}
                            {% if not stories %}<p class="text-gray-500 text-sm">Not linked to any stories yet.</p>{% endif %}
                        </div>
                    </section>
                    <section>
                        <div class="flex justify-between items-center mb-2 border-b border-slate-800 pb-2">
                            <h2 class="text-xl font-bold text-indigo-400">Gallery</h2>
                            <form action="/upload_gallery" method="post" enctype="multipart/form-data">
                                <input type="hidden" name="char_id" value="{{ char_id }}">
                                <label class="cursor-pointer bg-slate-800 hover:bg-slate-700 text-xs px-3 py-1 rounded border border-slate-700 text-gray-300"><i class="fas fa-upload mr-1"></i> Add Image<input type="file" name="image" class="hidden" onchange="this.form.submit()"></label>
                            </form>
                        </div>
                        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                            {% for img in char.get('gallery', []) %}
                            <div class="aspect-square rounded-lg overflow-hidden border border-slate-800 bg-black cursor-pointer hover:border-indigo-500 transition" onclick="window.open('/gallery/{{ img }}', '_blank')"><img src="/gallery/{{ img }}" class="w-full h-full object-cover"></div>
                            {% endfor %}
                        </div>
                    </section>
                </div>
            </div>

        {% elif mode == 'read' %}
            <aside class="w-80 hidden md:block shrink-0 sidebar-container space-y-6">
                {% for char in characters %}
                <div class="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden shadow-lg flex flex-col relative group">
                    {% if char.id %}
                        <a href="/character/{{ char.id }}" class="absolute top-2 left-2 z-10 bg-black/50 hover:bg-indigo-600 text-white p-2 rounded-full opacity-0 group-hover:opacity-100 transition"><i class="fas fa-external-link-alt text-xs"></i></a>
                        <button onclick='openEditModal({{ char | tojson }})' class="absolute top-2 right-2 z-10 bg-black/50 hover:bg-indigo-600 text-white p-2 rounded-full opacity-0 group-hover:opacity-100 transition"><i class="fas fa-pencil-alt text-xs"></i></button>
                    {% else %}
                        <div class="absolute top-2 right-2 z-10 bg-black/50 text-xs text-gray-400 px-2 py-1 rounded pointer-events-none">Unlinked</div>
                    {% endif %}

                    <div class="w-full flex justify-center pt-4 pb-2 bg-slate-800/50">
                        {% if char.avatar_url %}
                            <img src="{{ char.avatar_url }}" class="w-[200px] h-[200px] object-cover rounded shadow-md border border-gray-700">
                        {% else %}
                            <div class="w-[200px] h-[200px] flex items-center justify-center font-bold text-white shadow-md rounded border border-gray-700 text-6xl select-none" style="background-color: {{ char.color }};">{{ char.display_name[:1] }}</div>
                        {% endif %}
                    </div>

                    <div class="p-4 border-t border-gray-800 bg-gray-900">
                        <h3 class="font-bold text-lg text-gray-100 truncate text-center mb-3">{{ char.display_name }}</h3>
                        <div class="grid grid-cols-2 gap-2 text-xs text-gray-400 mb-3 bg-slate-950/50 p-2 rounded">
                            <div><span class="block text-[9px] uppercase font-bold text-gray-600">Age</span>{{ char.attributes.get('Age', '-') }}</div>
                            <div><span class="block text-[9px] uppercase font-bold text-gray-600">Gender</span>{{ char.attributes.get('Gender', '-') }}</div>
                            <div><span class="block text-[9px] uppercase font-bold text-gray-600">Race</span>{{ char.attributes.get('Race', '-') }}</div>
                            <div><span class="block text-[9px] uppercase font-bold text-gray-600">Orient.</span>{{ char.attributes.get('Orientation', '-') }}</div>
                        </div>
                        <div class="space-y-1">
                        {% for key, val in char.attributes.items() %}
                            {% if key not in ['Age', 'Gender', 'Race', 'Orientation'] and loop.index < 4 %}
                                <div class="flex justify-between text-xs text-gray-500 border-b border-gray-800/50 pb-1"><span class="font-bold">{{ key }}</span><span>{{ val }}</span></div>
                            {% endif %}
                        {% endfor %}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </aside>

            <div class="flex-1 max-w-4xl h-full overflow-y-auto pr-2">
                <div class="bg-gray-900 rounded-xl shadow-2xl border border-gray-800 p-8 min-h-full">
                    <div class="space-y-6">
                    {% for block in blocks %}
                        {% if block.type == 'ooc' %}
                            <div class="flex justify-center my-4 opacity-75"><div class="bg-gray-800 border border-gray-600 text-gray-400 text-xs px-4 py-1 rounded-full uppercase tracking-wider">(( {{ block.text | safe }} ))</div></div>
                        {% elif block.type == 'dialogue' %}
                            <div class="flex flex-col space-y-1">
                                <span class="text-xs font-bold text-indigo-400 ml-1">{{ block.speaker }}</span>
                                <div class="bg-gray-800 text-gray-100 p-3 rounded-2xl rounded-tl-none inline-block max-w-[85%] self-start shadow-sm leading-relaxed border border-gray-700/50">
                                    {% for line in block.lines %}
                                        <div class="{{ 'my-1' if line.is_action_line else 'min-h-[1.2em]' }}">{{ line.content | safe }}</div>
                                    {% endfor %}
                                </div>
                            </div>
                        {% else %}
                            <div class="text-gray-300 leading-relaxed bg-black/20 p-4 rounded-lg border-l-2 border-indigo-500/50">{{ block.text | safe }}</div>
                        {% endif %}
                    {% endfor %}
                    </div>
                    <div class="mt-20 pt-10 border-t border-gray-800 text-center text-gray-600 text-sm">End of File</div>
                </div>
            </div>
            <div class="w-10 hidden xl:block shrink-0"></div>
        {% endif %}

    </main>
    
    {{ modals | safe }}

</body>
</html>
"""

jinja_template = Template(HTML_TEMPLATE)

# --------------------------------------------------------------------------
# ROUTES
# --------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
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
    return jinja_template.render(mode="dashboard", campaigns=story_manager.get_campaigns(), active_campaign=active_campaign, stories=stories_data, modals=MODALS_HTML)

@app.get("/characters", response_class=HTMLResponse)
async def char_list():
    all_chars = character_manager.get_all_characters()
    return jinja_template.render(mode="char_list", all_chars=all_chars, modals=MODALS_HTML)

@app.get("/character/{char_id}", response_class=HTMLResponse)
async def char_profile(char_id: str):
    char = character_manager.get_character(char_id)
    if not char: raise HTTPException(404, "Character not found")
    char['id'] = char_id
    linked_stories = character_manager.get_character_stories(char_id)
    return jinja_template.render(mode="char_profile", char=char, char_id=char_id, stories=linked_stories, modals=MODALS_HTML)

@app.get("/read/{path:path}", response_class=HTMLResponse)
async def read_story(path: str):
    full_path = os.path.join(story_manager.STORY_DIR, path)
    if not os.path.exists(full_path): raise HTTPException(404, "File not found")
    blocks, local_stats = story_parser.parse_file(full_path)
    characters = character_manager.get_cast_for_story(path, local_stats)
    all_db_chars = character_manager.get_all_characters()
    return jinja_template.render(mode="read", blocks=blocks, characters=characters, all_db_chars=all_db_chars, filename=path, modals=MODALS_HTML)

# --- EXPORT / IMPORT ROUTES ---

@app.get("/export_character/{char_id}")
async def export_character(char_id: str):
    png_buffer = character_manager.export_character_card(char_id)
    if not png_buffer: raise HTTPException(404, "Character not found")
    
    char_name = character_manager.get_character(char_id).get("name", "character")
    safe_name = "".join(c for c in char_name if c.isalnum() or c in " _-").strip()
    
    return StreamingResponse(
        png_buffer, 
        media_type="image/png", 
        headers={"Content-Disposition": f"attachment; filename={safe_name}.png"}
    )

@app.post("/import_character")
async def import_character(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".png"):
        raise HTTPException(400, "Only PNG files allowed")
        
    contents = await file.read()
    new_id = character_manager.import_character_card(contents)
    
    if not new_id: raise HTTPException(400, "Invalid Character Card (No Data Found)")
    return RedirectResponse(url=f"/character/{new_id}", status_code=303)

# --- ACTIONS ---

@app.post("/create_campaign")
async def create_campaign(name: str = Form(...)):
    story_manager.create_campaign(name)
    return RedirectResponse(url="/", status_code=303)

@app.post("/update_story_meta")
async def update_story_meta(current_path: str = Form(...), title: str = Form(...), synopsis: str = Form(""), tags: str = Form(""), campaign: str = Form(...)):
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    story_manager.update_story_meta(current_path, title, synopsis, tag_list)
    parts = current_path.replace("\\", "/").split("/")
    current_camp = parts[0] if len(parts) > 1 else "Unsorted"
    if campaign != current_camp: story_manager.move_story_to_campaign(current_path, campaign)
    return RedirectResponse(url="/", status_code=303)

@app.post("/create_character_quick")
async def create_character_quick(name: str = Form(...)):
    new_id = character_manager.create_character(name)
    return RedirectResponse(url=f"/character/{new_id}", status_code=303)

@app.post("/link_character")
async def link_character(filename: str = Form(...), raw_name: str = Form(...), char_id: str = Form(...)):
    if char_id == "NEW": char_id = character_manager.create_character(raw_name)
    character_manager.update_story_map(filename, raw_name, char_id)
    return RedirectResponse(url=f"/read/{filename}", status_code=303)

@app.post("/update_character_details")
async def update_character_details(char_id: str = Form(...), name: str = Form(...), description: str = Form(""), return_file: str = Form(None), avatar: Optional[UploadFile] = File(None), attr_keys: List[str] = Form([]), attr_values: List[str] = Form([])):
    avatar_filename = None
    if avatar and avatar.filename: avatar_filename = character_manager.save_avatar(char_id, avatar.file, avatar.filename)
    attributes = {}
    for k, v in zip(attr_keys, attr_values):
        if k.strip() and v.strip(): attributes[k.strip()] = v.strip()
    character_manager.update_character_data(char_id, name, description, attributes, avatar_filename)
    if return_file: return RedirectResponse(url=f"/read/{return_file}", status_code=303)
    else: return RedirectResponse(url=f"/character/{char_id}", status_code=303)

@app.post("/upload_gallery")
async def upload_gallery(char_id: str = Form(...), image: UploadFile = File(...)):
    if image.filename: character_manager.add_gallery_image(char_id, image.file, image.filename)
    return RedirectResponse(url=f"/character/{char_id}", status_code=303)

@app.post("/delete_character")
async def delete_char_endpoint(char_id: str = Form(...)):
    character_manager.delete_character(char_id)
    return RedirectResponse(url="/characters", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, loop="asyncio")