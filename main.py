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
import prompt_manager  # NEW IMPORT

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
        .tag-purple { background: #581c87; color: #d8b4fe; border: 1px solid #7e22ce; }
        .tag-gray { background: #1f2937; color: #9ca3af; border: 1px solid #374151; }
        .glass-panel { background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(8px); border: 1px solid rgba(51, 65, 85, 0.5); }
    </style>
</head>
<body class="bg-slate-950 text-gray-200 font-sans h-screen flex flex-col">

    <header class="bg-slate-900 border-b border-slate-800 p-4 shadow-lg flex justify-between items-center z-10 shrink-0 relative">
        <div class="flex items-center gap-6">
            <h1 class="text-xl font-bold text-indigo-400">StoryStash <span class="text-xs text-gray-500">v4</span></h1>
            <nav class="flex gap-4 text-sm font-medium">
                <a href="/" class="{{ 'text-white font-bold' if mode == 'dashboard' else 'text-gray-400 hover:text-white' }}">Dashboard</a>
                <a href="/stories" class="{{ 'text-white font-bold' if mode == 'stories_list' else 'text-gray-400 hover:text-white' }}">Stories</a>
                <a href="/characters" class="{{ 'text-white font-bold' if mode in ['char_list', 'char_profile'] else 'text-gray-400 hover:text-white' }}">Characters</a>
                <a href="/prompts" class="{{ 'text-white font-bold' if mode == 'prompts_list' else 'text-gray-400 hover:text-white' }}">Prompts</a>
            </nav>
        </div>
        
        <div class="absolute left-1/2 transform -translate-x-1/2 w-96">
            <form action="/search" method="get" class="relative">
                <i class="fas fa-search absolute left-3 top-2.5 text-gray-500 text-xs"></i>
                <input type="search" name="q" placeholder="Search stories..." value="{{ query or '' }}" class="w-full bg-slate-950 border border-slate-700 rounded-full py-1.5 pl-8 pr-4 text-sm focus:border-indigo-500 focus:outline-none transition">
            </form>
        </div>
        
        {% if mode == 'read' %}
        <div class="flex gap-2">
            <button onclick="document.getElementById('bgModal').showModal()" class="bg-slate-800 hover:bg-slate-700 text-gray-300 px-3 py-1 rounded text-sm border border-slate-700" title="Change Background">
                <i class="fas fa-image"></i>
            </button>
            <button onclick="document.getElementById('castModal').showModal()" class="bg-slate-800 hover:bg-slate-700 text-gray-300 px-3 py-1 rounded text-sm border border-slate-700">
                <i class="fas fa-users-cog mr-2"></i> Manage Cast
            </button>
        </div>
        {% elif mode == 'prompts_list' %}
        <button onclick="document.getElementById('createPromptModal').showModal()" class="bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1 rounded text-sm font-bold shadow-lg shadow-indigo-500/20">
            <i class="fas fa-plus mr-2"></i> New Prompt
        </button>
        {% endif %}
    </header>

    <main class="flex-1 overflow-hidden w-full flex justify-center p-6 gap-6 relative" 
          style="{{ 'background-image: url(/backgrounds/' + background_file + '); background-size: cover; background-position: center;' if background_file else '' }}">
        
        {% if background_file %}
        <div class="absolute inset-0 bg-slate-950/80 backdrop-blur-sm pointer-events-none z-0"></div>
        {% endif %}

        {% if mode == 'dashboard' %}
            <div class="flex-1 max-w-6xl h-full overflow-y-auto space-y-8 z-10">
                <div><h2 class="text-3xl font-bold text-white mb-2">Welcome back.</h2><p class="text-gray-400">Here is an overview of your roleplay universe.</p></div>
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div class="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow-lg flex items-center gap-4"><div class="w-12 h-12 rounded-full bg-indigo-900/50 text-indigo-400 flex items-center justify-center text-xl"><i class="fas fa-book"></i></div><div><div class="text-2xl font-bold text-white">{{ stats.total_stories }}</div><div class="text-xs uppercase text-gray-500 font-bold tracking-wider">Stories</div></div></div>
                    <div class="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow-lg flex items-center gap-4"><div class="w-12 h-12 rounded-full bg-purple-900/50 text-purple-400 flex items-center justify-center text-xl"><i class="fas fa-users"></i></div><div><div class="text-2xl font-bold text-white">{{ stats.total_chars }}</div><div class="text-xs uppercase text-gray-500 font-bold tracking-wider">Characters</div></div></div>
                    <div class="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow-lg flex items-center gap-4"><div class="w-12 h-12 rounded-full bg-emerald-900/50 text-emerald-400 flex items-center justify-center text-xl"><i class="fas fa-layer-group"></i></div><div><div class="text-2xl font-bold text-white">{{ stats.total_campaigns }}</div><div class="text-xs uppercase text-gray-500 font-bold tracking-wider">Campaigns</div></div></div>
                    <div class="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow-lg flex items-center gap-4"><div class="w-12 h-12 rounded-full bg-amber-900/50 text-amber-400 flex items-center justify-center text-xl"><i class="fas fa-lightbulb"></i></div><div><div class="text-2xl font-bold text-white">{{ stats.total_prompts }}</div><div class="text-xs uppercase text-gray-500 font-bold tracking-wider">Prompts</div></div></div>
                </div>
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div class="lg:col-span-2">
                        <div class="flex justify-between items-center mb-4"><h3 class="text-lg font-bold text-white">Recent Updates</h3><a href="/stories" class="text-xs text-indigo-400 hover:text-indigo-300">View All</a></div>
                        <div class="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                            {% for story in recent_stories %}
                            <a href="/read/{{ story.path }}" class="flex items-center justify-between p-4 border-b border-slate-800 hover:bg-slate-800/50 transition last:border-0"><div class="flex items-center gap-4"><div class="w-8 h-8 rounded bg-slate-800 flex items-center justify-center text-gray-500"><i class="fas fa-file-alt"></i></div><div><div class="font-bold text-gray-200">{{ story.meta.display_title }}</div><div class="text-xs text-gray-500">{{ story.path }}</div></div></div><div class="text-xs text-gray-500">{{ story.stats.date }}</div></a>
                            {% endfor %}
                        </div>
                    </div>
                    <div>
                        <h3 class="text-lg font-bold text-white mb-4">Quick Actions</h3>
                        <div class="space-y-3">
                            <button onclick="document.getElementById('importStoryModal').showModal()" class="w-full text-left p-4 bg-slate-900 border border-slate-800 rounded-xl hover:border-indigo-500 transition flex items-center gap-3"><div class="w-10 h-10 rounded-full bg-green-900/30 text-green-400 flex items-center justify-center"><i class="fas fa-plus"></i></div><div><div class="font-bold text-gray-200">Import Story</div><div class="text-xs text-gray-500">Upload .txt or Paste</div></div></button>
                            <form action="/create_character_quick" method="post" class="block w-full"><div class="p-4 bg-slate-900 border border-slate-800 rounded-xl hover:border-purple-500 transition flex flex-col gap-2"><div class="flex items-center gap-3 text-purple-400 font-bold"><i class="fas fa-user-plus"></i> New Character</div><div class="flex gap-2"><input type="text" name="name" placeholder="Name" class="input-dark py-1 text-sm" required><button type="submit" class="bg-purple-600 hover:bg-purple-500 text-white px-3 rounded text-sm font-bold">Go</button></div></div></form>
                        </div>
                    </div>
                </div>
            </div>
            {{ modals | safe }}

        {% elif mode == 'prompts_list' %}
            <div class="flex-1 max-w-6xl h-full overflow-y-auto z-10">
                <div class="flex justify-between items-center mb-6"><h2 class="text-2xl font-bold text-white">Roleplay Prompts</h2></div>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {% for pid, prompt in prompts.items() %}
                    <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-indigo-500 transition flex flex-col h-[300px] relative group">
                        <form action="/delete_prompt" method="post" class="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition" onsubmit="return confirm('Delete prompt?');">
                            <input type="hidden" name="pid" value="{{ pid }}">
                            <button class="text-gray-600 hover:text-red-500"><i class="fas fa-trash"></i></button>
                        </form>
                        <h3 class="text-lg font-bold text-indigo-400 mb-2 truncate">{{ prompt.title }}</h3>
                        <div class="flex flex-wrap gap-2 mb-4">
                            {% for tag in prompt.tags %}<span class="tag tag-purple">{{ tag }}</span>{% endfor %}
                        </div>
                        <div class="flex-1 bg-slate-950/50 p-3 rounded text-sm text-gray-300 overflow-y-auto mb-4 font-serif leading-relaxed italic whitespace-pre-wrap">{{ prompt.content }}</div>
                        <div class="border-t border-slate-800 pt-3 flex items-center gap-2 overflow-x-auto">
                            <span class="text-[10px] uppercase font-bold text-gray-600 shrink-0">Assigned:</span>
                            {% if prompt.linked_chars %}
                                {% for cid in prompt.linked_chars %}
                                    {% if all_chars.get(cid) %}
                                    <div class="w-6 h-6 rounded-full bg-slate-800 border border-slate-600 overflow-hidden shrink-0" title="{{ all_chars[cid].name }}">
                                        {% if all_chars[cid].avatar_file %}
                                        <img src="/avatars/{{ all_chars[cid].avatar_file }}" class="w-full h-full object-cover">
                                        {% else %}
                                        <div class="w-full h-full flex items-center justify-center text-[8px]">{{ all_chars[cid].name[:1] }}</div>
                                        {% endif %}
                                    </div>
                                    {% endif %}
                                {% endfor %}
                            {% else %}
                                <span class="text-[10px] text-gray-600 italic">None</span>
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <dialog id="createPromptModal" class="rounded-xl bg-slate-900 border border-slate-700 text-gray-200 w-[600px] backdrop:bg-black/80">
                <form action="/create_prompt" method="post" class="flex flex-col h-[80vh]">
                    <div class="p-6 border-b border-slate-800"><h2 class="text-lg font-bold text-indigo-400">Create New Prompt</h2></div>
                    <div class="p-6 overflow-y-auto space-y-4 flex-1">
                        <div><label class="text-xs font-bold text-gray-500 uppercase">Title</label><input type="text" name="title" class="input-dark mt-1" required></div>
                        <div><label class="text-xs font-bold text-gray-500 uppercase">Prompt Content</label><textarea name="content" rows="8" class="input-dark mt-1 font-serif text-sm" required></textarea></div>
                        <div><label class="text-xs font-bold text-gray-500 uppercase">Tags (comma separated)</label><input type="text" name="tags" class="input-dark mt-1" placeholder="e.g. Romance, Sci-Fi, Conflict"></div>
                        
                        <div>
                            <label class="text-xs font-bold text-gray-500 uppercase block mb-2">Assign Characters</label>
                            <div class="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto bg-slate-950 p-2 rounded border border-slate-800">
                                {% for cid, char in all_chars.items() %}
                                <label class="flex items-center gap-2 text-sm text-gray-300 hover:bg-slate-900 p-1 rounded cursor-pointer">
                                    <input type="checkbox" name="linked_chars" value="{{ cid }}" class="accent-indigo-500">
                                    <div class="w-5 h-5 rounded-full bg-slate-800 overflow-hidden">
                                        {% if char.avatar_file %}<img src="/avatars/{{ char.avatar_file }}" class="w-full h-full object-cover">{% else %}<div class="w-full h-full flex items-center justify-center text-[8px]">{{ char.name[:1] }}</div>{% endif %}
                                    </div>
                                    <span class="truncate">{{ char.name }}</span>
                                </label>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                    <div class="p-4 border-t border-slate-800 flex justify-end gap-2 bg-slate-900"><button type="button" onclick="this.closest('dialog').close()" class="text-gray-400 text-sm px-3 py-2">Cancel</button><button type="submit" class="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-bold">Create Prompt</button></div>
                </form>
            </dialog>

        {% elif mode == 'char_profile' %}
            <div class="flex-1 h-full overflow-hidden flex gap-8 z-10">
                <aside class="w-80 shrink-0 h-full overflow-y-auto space-y-6">
                    <div class="bg-slate-900 rounded-xl border border-slate-800 p-6 flex flex-col items-center shadow-lg relative group">
                        <button onclick='openEditModal({{ char | tojson }})' class="absolute top-2 right-2 text-gray-500 hover:text-indigo-400" title="Edit"><i class="fas fa-pencil-alt"></i></button>
                        <form action="/delete_character" method="post" onsubmit="return confirm('Delete?');"><input type="hidden" name="char_id" value="{{ char_id }}"><button type="submit" class="absolute top-2 left-2 text-gray-600 hover:text-red-500 transition" title="Delete"><i class="fas fa-trash"></i></button></form>
                        <a href="/export_character/{{ char_id }}" target="_blank" class="absolute bottom-2 right-2 text-gray-600 hover:text-blue-400 transition" title="Export Card"><i class="fas fa-address-card"></i></a>
                        <div class="w-48 h-48 rounded-lg shadow-2xl border-2 border-slate-700 overflow-hidden mb-4 bg-slate-800">
                            {% if char.get('avatar_file') %}<img src="/avatars/{{ char.avatar_file }}" class="w-full h-full object-cover">{% else %}<div class="w-full h-full flex items-center justify-center text-6xl font-bold text-white/20">{{ char.get('name', '?')[:1] }}</div>{% endif %}
                        </div>
                        <h1 class="text-2xl font-bold text-white text-center">{{ char.get('name', 'Unknown') }}</h1>
                        <div class="w-full mt-6 space-y-3">
                            <div class="flex justify-between border-b border-slate-800 pb-1"><span class="text-xs uppercase text-gray-500 font-bold">Age</span><span class="text-sm text-gray-200">{{ char.attributes.get('Age', 'Unknown') }}</span></div>
                            <div class="flex justify-between border-b border-slate-800 pb-1"><span class="text-xs uppercase text-gray-500 font-bold">Gender</span><span class="text-sm text-gray-200">{{ char.attributes.get('Gender', 'Unknown') }}</span></div>
                            <div class="flex justify-between border-b border-slate-800 pb-1"><span class="text-xs uppercase text-gray-500 font-bold">Race</span><span class="text-sm text-gray-200">{{ char.attributes.get('Race', 'Unknown') }}</span></div>
                            <div class="flex justify-between border-b border-slate-800 pb-1"><span class="text-xs uppercase text-gray-500 font-bold">Orientation</span><span class="text-sm text-gray-200">{{ char.attributes.get('Orientation', 'Unknown') }}</span></div>
                            {% for key, val in char.attributes.items() %}{% if key not in ['Age', 'Gender', 'Race', 'Orientation'] %}<div class="flex justify-between border-b border-slate-800 pb-1"><span class="text-xs uppercase text-gray-500 font-bold truncate max-w-[100px]">{{ key }}</span><span class="text-sm text-gray-400 truncate">{{ val }}</span></div>{% endif %}{% endfor %}
                        </div>
                    </div>
                </aside>
                <div class="flex-1 h-full overflow-y-auto space-y-8 pr-4">
                    {% if assigned_prompts %}
                    <section>
                        <h2 class="text-xl font-bold text-amber-400 mb-2 border-b border-slate-800 pb-2"><i class="fas fa-lightbulb mr-2"></i> Assigned Prompts</h2>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {% for p in assigned_prompts %}
                            <div class="bg-slate-900 border border-slate-800 p-4 rounded-lg hover:border-amber-500/50 transition">
                                <h3 class="font-bold text-gray-200 mb-2">{{ p.title }}</h3>
                                <div class="text-xs text-gray-400 italic line-clamp-3 mb-2">{{ p.content }}</div>
                                <div class="flex flex-wrap gap-1">
                                    {% for tag in p.tags %}<span class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-gray-500 border border-slate-700">{{ tag }}</span>{% endfor %}
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </section>
                    {% endif %}

                    <section><h2 class="text-xl font-bold text-indigo-400 mb-2 border-b border-slate-800 pb-2">Biography</h2><div class="bg-slate-900/50 p-6 rounded-xl border border-slate-800 text-gray-300 leading-relaxed italic">{{ char.description or "No biography." }}</div></section>
                    <section><h2 class="text-xl font-bold text-indigo-400 mb-2 border-b border-slate-800 pb-2">Appears In</h2><div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">{% for story_path in stories %}<a href="/read/{{ story_path }}" class="block bg-slate-900 p-4 rounded-lg border border-slate-800 hover:border-indigo-500 transition"><i class="fas fa-file-alt text-indigo-500 mr-2"></i> {{ story_path }}</a>{% endfor %}{% if not stories %}<p class="text-gray-500 text-sm">Not linked to any stories.</p>{% endif %}</div></section>
                    <section><div class="flex justify-between items-center mb-2 border-b border-slate-800 pb-2"><h2 class="text-xl font-bold text-indigo-400">Gallery</h2><form action="/upload_gallery" method="post" enctype="multipart/form-data"><input type="hidden" name="char_id" value="{{ char_id }}"><label class="cursor-pointer bg-slate-800 hover:bg-slate-700 text-xs px-3 py-1 rounded border border-slate-700 text-gray-300"><i class="fas fa-upload mr-1"></i> Add Image<input type="file" name="image" class="hidden" onchange="this.form.submit()"></label></form></div><div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">{% for img in char.get('gallery', []) %}<div class="aspect-square rounded-lg overflow-hidden border border-slate-800 bg-black cursor-pointer hover:border-indigo-500 transition" onclick="window.open('/gallery/{{ img }}', '_blank')"><img src="/gallery/{{ img }}" class="w-full h-full object-cover"></div>{% endfor %}</div></section>
                </div>
            </div>
            {{ modals | safe }}

        {% elif mode == 'search' %}
            <div class="flex-1 max-w-4xl h-full overflow-y-auto z-10">
                <h2 class="text-2xl font-bold text-white mb-6">Search Results for "<span class="text-indigo-400">{{ query }}</span>"</h2>
                <div class="space-y-4">{% for result in results %}<div class="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-indigo-500 transition"><a href="/read/{{ result.path }}" class="block"><h3 class="font-bold text-lg text-indigo-400 mb-1"><i class="fas fa-file-alt mr-2"></i> {{ result.title }}</h3><div class="text-xs text-gray-500 mb-3">{{ result.path }}</div><div class="space-y-2">{% for match in result.matches %}<div class="text-sm text-gray-300 font-mono bg-slate-950 p-2 rounded border-l-2 border-indigo-500/50">...{{ match }}...</div>{% endfor %}</div></a></div>{% endfor %}{% if not results %}<div class="text-center text-gray-500 mt-20"><i class="fas fa-ghost text-4xl mb-4 opacity-50"></i><p>No results found.</p></div>{% endif %}</div>
            </div>
        {% elif mode == 'stories_list' %}
            <aside class="w-64 shrink-0 bg-slate-900/50 rounded-xl border border-slate-800 p-4 h-full overflow-y-auto z-10">
                <div class="flex justify-between items-center mb-4"><h2 class="text-xs font-bold text-gray-500 uppercase tracking-widest">Campaigns</h2><button onclick="document.getElementById('campaignModal').showModal()" class="text-xs text-indigo-400 hover:text-indigo-300"><i class="fas fa-plus"></i></button></div>
                <nav class="space-y-1"><a href="/stories" class="block px-3 py-2 rounded text-sm {{ 'bg-indigo-900/50 text-indigo-200' if not active_campaign else 'text-gray-400 hover:bg-slate-800 hover:text-white' }}"><i class="fas fa-layer-group w-5"></i> All Stories</a>{% for camp in campaigns %}{% if camp != "Unsorted" %}<a href="/stories?campaign={{ camp }}" class="block px-3 py-2 rounded text-sm {{ 'bg-indigo-900/50 text-indigo-200' if active_campaign == camp else 'text-gray-400 hover:bg-slate-800 hover:text-white' }}"><i class="fas fa-folder w-5 text-yellow-600"></i> {{ camp }}</a>{% endif %}{% endfor %}</nav>
                <div class="mt-6 border-t border-slate-800 pt-4"><button onclick="document.getElementById('importStoryModal').showModal()" class="block w-full text-left px-3 py-2 rounded text-sm text-gray-400 hover:bg-slate-800 hover:text-white transition"><i class="fas fa-file-import w-5 text-green-500"></i> Import / Write</button></div>
            </aside>
            <div class="flex-1 h-full overflow-y-auto pr-2 z-10"><div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">{% for item in stories %}<div class="bg-slate-900 rounded-xl border border-slate-800 shadow-lg hover:border-indigo-500/50 transition flex flex-col h-[280px] group relative"><button onclick='openStoryMetaModal({{ item | tojson }})' class="absolute top-2 right-2 z-10 text-gray-500 hover:text-indigo-400 opacity-0 group-hover:opacity-100 transition p-2"><i class="fas fa-cog"></i></button><a href="/read/{{ item.path }}" class="flex-1 flex flex-col p-5"><div class="mb-3"><h3 class="font-bold text-lg text-gray-100 leading-tight line-clamp-1" title="{{ item.meta.display_title }}">{{ item.meta.display_title }}</h3><div class="text-[10px] text-gray-500 mt-1 flex gap-2"><span><i class="far fa-clock"></i> {{ item.stats.date }}</span><span><i class="far fa-comment-alt"></i> {{ item.stats.msg_count }}</span></div></div><div class="flex-1 text-xs text-gray-400 italic line-clamp-4 leading-relaxed overflow-hidden">{{ item.meta.synopsis }}</div>{% if item.stats.top_characters %}<div class="mt-3 flex -space-x-2 overflow-hidden py-1">{% for char in item.stats.top_characters %}<div class="inline-block h-6 w-6 rounded-full ring-2 ring-slate-900 bg-indigo-500 flex items-center justify-center text-[8px] font-bold text-white">{{ char[:1] }}</div>{% endfor %}</div>{% endif %}</a><div class="p-3 border-t border-slate-800 bg-slate-950/30 rounded-b-xl flex gap-2 overflow-x-auto">{% if item.meta.tags %}{% for tag in item.meta.tags %}<span class="tag tag-blue">{{ tag }}</span>{% endfor %}{% else %}<span class="tag tag-gray">No Tags</span>{% endif %}</div></div>{% endfor %}</div></div>
            {{ modals | safe }}

        {% elif mode == 'char_list' %}
            <div class="flex-1 h-full overflow-y-auto z-10">
                <div class="flex justify-between items-center mb-6"><h2 class="text-2xl font-bold text-white">Character Database</h2><div class="flex gap-4 items-center"><form action="/import_character" method="post" enctype="multipart/form-data" class="flex gap-2"><label class="cursor-pointer bg-slate-800 hover:bg-slate-700 text-gray-300 px-3 py-1 rounded text-sm border border-slate-700 font-medium"><i class="fas fa-file-import mr-1"></i> Import Card (PNG)<input type="file" name="file" accept=".png" class="hidden" onchange="this.form.submit()"></label></form><form action="/create_character_quick" method="post" class="flex gap-2 border-l border-slate-700 pl-4"><input type="text" name="name" placeholder="New Character Name" class="input-dark py-1 px-3 w-64" required><button type="submit" class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-1 rounded text-sm font-bold">Create</button></form></div></div>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">{% for id, char in all_chars.items() %}<a href="/character/{{ id }}" class="block bg-slate-900 rounded-xl border border-slate-800 overflow-hidden hover:border-indigo-500 hover:shadow-lg transition group"><div class="aspect-square bg-slate-800 w-full relative">{% if char.get('avatar_file') %}<img src="/avatars/{{ char.avatar_file }}" class="w-full h-full object-cover">{% else %}<div class="w-full h-full flex items-center justify-center text-4xl font-bold text-white/20">{{ char.get('name', '?')[:1] }}</div>{% endif %}<div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-3 pt-8"><h3 class="font-bold text-white truncate">{{ char.get('name', 'Unknown') }}</h3></div></div></a>{% endfor %}</div>
            </div>

        {% elif mode == 'read' %}
            <aside class="w-80 hidden md:block shrink-0 sidebar-container space-y-6 z-10">{% for char in characters %}<div class="glass-panel rounded-xl overflow-hidden shadow-lg flex flex-col relative group">{% if char.id %}<a href="/character/{{ char.id }}" class="absolute top-2 left-2 z-10 bg-black/50 hover:bg-indigo-600 text-white p-2 rounded-full opacity-0 group-hover:opacity-100 transition"><i class="fas fa-external-link-alt text-xs"></i></a><button onclick='openEditModal({{ char | tojson }})' class="absolute top-2 right-2 z-10 bg-black/50 hover:bg-indigo-600 text-white p-2 rounded-full opacity-0 group-hover:opacity-100 transition"><i class="fas fa-pencil-alt text-xs"></i></button>{% else %}<div class="absolute top-2 right-2 z-10 bg-black/50 text-xs text-gray-400 px-2 py-1 rounded pointer-events-none">Unlinked</div>{% endif %}<div class="w-full flex justify-center pt-4 pb-2 bg-slate-800/50">{% if char.avatar_url %}<img src="{{ char.avatar_url }}" class="w-[200px] h-[200px] object-cover rounded shadow-md border border-gray-700">{% else %}<div class="w-[200px] h-[200px] flex items-center justify-center font-bold text-white shadow-md rounded border border-gray-700 text-6xl select-none" style="background-color: {{ char.color }};">{{ char.display_name[:1] }}</div>{% endif %}</div><div class="p-4 border-t border-gray-800 bg-gray-900/90"><h3 class="font-bold text-lg text-gray-100 truncate text-center mb-3">{{ char.display_name }}</h3><div class="grid grid-cols-2 gap-2 text-xs text-gray-400 mb-3 bg-slate-950/50 p-2 rounded"><div><span class="block text-[9px] uppercase font-bold text-gray-600">Age</span>{{ char.attributes.get('Age', '-') }}</div><div><span class="block text-[9px] uppercase font-bold text-gray-600">Gender</span>{{ char.attributes.get('Gender', '-') }}</div><div><span class="block text-[9px] uppercase font-bold text-gray-600">Race</span>{{ char.attributes.get('Race', '-') }}</div><div><span class="block text-[9px] uppercase font-bold text-gray-600">Orient.</span>{{ char.attributes.get('Orientation', '-') }}</div></div></div></div>{% endfor %}</aside>
            <div class="flex-1 max-w-4xl h-full overflow-y-auto pr-2 z-10"><div class="glass-panel rounded-xl shadow-2xl p-8 min-h-full"><div class="space-y-6">{% for block in blocks %}{% if block.type == 'ooc' %}<div class="flex justify-center my-4 opacity-75"><div class="bg-gray-800 border border-gray-600 text-gray-400 text-xs px-4 py-1 rounded-full uppercase tracking-wider">(( {{ block.text | safe }} ))</div></div>{% elif block.type == 'dialogue' %}<div class="flex flex-col space-y-1"><span class="text-xs font-bold text-indigo-400 ml-1 drop-shadow-md">{{ block.speaker }}</span>{% set speaker_char = char_map.get(block.speaker) %}{% set bubble_color = speaker_char.bubble_color if speaker_char else '#1f2937' %}<div class="text-gray-100 p-3 rounded-2xl rounded-tl-none inline-block max-w-[85%] self-start shadow-sm leading-relaxed border" style="background-color: {{ bubble_color }}DD; border-color: {{ bubble_color }};">{% for line in block.lines %}<div class="{{ 'my-1' if line.is_action_line else 'min-h-[1.2em]' }}">{{ line.content | safe }}</div>{% endfor %}</div></div>{% else %}<div class="text-gray-300 leading-relaxed bg-black/40 p-4 rounded-lg border-l-2 border-indigo-500/50 backdrop-blur-sm">{{ block.text | safe }}</div>{% endif %}{% endfor %}</div><div class="mt-20 pt-10 border-t border-gray-800 text-center text-gray-600 text-sm">End of File</div></div></div><div class="w-10 hidden xl:block shrink-0"></div>
            <dialog id="castModal" class="rounded-xl shadow-2xl bg-slate-900 border border-slate-700 text-gray-200 w-[600px] backdrop:bg-black/80"><div class="p-6 border-b border-slate-800 flex justify-between items-center"><h2 class="text-lg font-bold text-indigo-400">Manage Cast</h2><button onclick="document.getElementById('castModal').close()" class="text-gray-500 hover:text-white"><i class="fas fa-times"></i></button></div><div class="p-6 max-h-[70vh] overflow-y-auto"><table class="w-full text-left text-sm"><thead class="text-xs text-gray-500 uppercase border-b border-slate-700"><tr><th class="py-2">Name in Story</th><th class="py-2">Database Character</th></tr></thead><tbody class="divide-y divide-slate-800">{% for char in characters %}<tr><td class="py-3 font-bold text-gray-300">{{ char.raw_name }}</td><td class="py-3"><form action="/link_character" method="POST" class="flex gap-2"><input type="hidden" name="filename" value="{{ filename }}"><input type="hidden" name="raw_name" value="{{ char.raw_name }}"><select name="char_id" class="input-dark text-xs py-1"><option value="">-- Unlinked --</option><option value="NEW">➕ Create New</option>{% for db_id, db_data in all_db_chars.items() %}<option value="{{ db_id }}" {% if char.id == db_id %}selected{% endif %}>{{ db_data.get('name', 'Unknown') }}</option>{% endfor %}</select><button type="submit" class="bg-indigo-900 hover:bg-indigo-700 text-indigo-200 px-2 rounded text-xs">Save</button></form></td></tr>{% endfor %}</tbody></table></div></dialog>
            <dialog id="bgModal" class="rounded-xl bg-slate-900 border border-slate-700 text-gray-200 w-96 backdrop:bg-black/80"><form action="/upload_story_background" method="post" enctype="multipart/form-data" class="p-6"><h2 class="text-lg font-bold text-indigo-400 mb-4">Change Story Background</h2><input type="hidden" name="return_path" value="{{ filename }}"><input type="file" name="file" accept="image/*" class="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-indigo-900 file:text-indigo-300 hover:file:bg-indigo-800 cursor-pointer mb-4 bg-slate-950 rounded border border-slate-700 p-1"/><div class="flex justify-end gap-2"><button type="button" onclick="this.closest('dialog').close()" class="text-gray-400 text-sm px-3 py-2">Cancel</button><button type="submit" class="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-bold">Upload</button></div></form></dialog>
        {% endif %}

    </main>
    
    <dialog id="campaignModal" class="rounded-xl bg-slate-900 border border-slate-700 text-gray-200 w-96 backdrop:bg-black/80"><form action="/create_campaign" method="post" class="p-6"><h2 class="text-lg font-bold text-indigo-400 mb-4">New Campaign</h2><input type="text" name="name" placeholder="Name" class="input-dark mb-4" required><div class="flex justify-end gap-2"><button type="button" onclick="this.closest('dialog').close()" class="text-gray-400 text-sm px-3 py-2">Cancel</button><button type="submit" class="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-bold">Create</button></div></form></dialog>
    <dialog id="storyMetaModal" class="rounded-xl bg-slate-900 border border-slate-700 text-gray-200 w-[500px] backdrop:bg-black/80"><form action="/update_story_meta" method="post" class="flex flex-col h-full"><div class="p-6 border-b border-slate-800"><h2 class="text-lg font-bold text-indigo-400">Edit Details</h2><input type="hidden" name="current_path" id="metaPathInput"></div><div class="p-6 space-y-4"><div><label class="text-xs font-bold text-gray-500 uppercase">Display Title</label><input type="text" name="title" id="metaTitleInput" class="input-dark mt-1"></div><div><label class="text-xs font-bold text-gray-500 uppercase">Synopsis</label><textarea name="synopsis" id="metaSynopsisInput" rows="3" class="input-dark mt-1"></textarea></div><div><label class="text-xs font-bold text-gray-500 uppercase">Tags</label><input type="text" name="tags" id="metaTagsInput" class="input-dark mt-1"></div><div><label class="text-xs font-bold text-gray-500 uppercase">Campaign</label><select name="campaign" id="metaCampaignInput" class="input-dark mt-1">{% for camp in campaigns %}<option value="{{ camp }}">{{ camp }}</option>{% endfor %}</select></div></div><div class="p-4 border-t border-slate-800 flex justify-end gap-2 bg-slate-900"><button type="button" onclick="this.closest('dialog').close()" class="text-gray-400 text-sm px-3 py-2">Cancel</button><button type="submit" class="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-bold">Save</button></div></form></dialog>
    <dialog id="editModal" class="rounded-xl shadow-2xl bg-slate-900 border border-slate-700 text-gray-200 w-[500px] backdrop:bg-black/80 max-h-[90vh]"><form action="/update_character_details" method="post" enctype="multipart/form-data" class="flex flex-col h-full"><div class="p-6 border-b border-slate-800 bg-slate-900 sticky top-0 z-10"><h2 class="text-lg font-bold text-indigo-400">Edit <span id="modalCharNameDisplay"></span></h2><input type="hidden" id="modalCharIdInput" name="char_id" value=""><input type="hidden" name="return_file" value="{{ filename | default('') }}"></div><div class="p-6 overflow-y-auto space-y-4"><div class="flex gap-4"><div class="flex-1"><label class="text-xs text-gray-500 uppercase font-bold">Display Name</label><input type="text" id="modalNameInput" name="name" class="input-dark mt-1"></div><div><label class="text-xs text-gray-500 uppercase font-bold">Chat Color</label><div class="flex items-center gap-2 mt-1"><input type="color" id="modalBubbleColor" name="bubble_color" class="h-9 w-9 bg-transparent cursor-pointer rounded"></div></div></div><div><label class="text-xs text-gray-500 uppercase font-bold">Avatar</label><input type="file" name="avatar" accept="image/*" class="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-indigo-900 file:text-indigo-300 hover:file:bg-indigo-800 cursor-pointer mt-2 bg-slate-950 rounded border border-slate-700 p-1"/></div><div><label class="text-xs text-gray-500 uppercase font-bold">Bio</label><textarea name="description" id="modalDescription" rows="3" class="input-dark mt-1"></textarea></div><div class="p-3 bg-slate-950 rounded border border-slate-800"><label class="text-xs text-gray-500 uppercase font-bold block mb-2">Core Stats</label><div class="grid grid-cols-2 gap-2"><input type="text" name="attr_keys" value="Age" class="hidden"><input type="text" id="modalAge" name="attr_values" placeholder="Age" class="input-dark text-xs"><input type="text" name="attr_keys" value="Gender" class="hidden"><input type="text" id="modalGender" name="attr_values" placeholder="Gender" class="input-dark text-xs"><input type="text" name="attr_keys" value="Race" class="hidden"><input type="text" id="modalRace" name="attr_values" placeholder="Race" class="input-dark text-xs"><input type="text" name="attr_keys" value="Orientation" class="hidden"><input type="text" id="modalOrient" name="attr_values" placeholder="Orientation" class="input-dark text-xs"></div></div><div><div class="flex justify-between items-center mb-2"><label class="text-xs text-gray-500 uppercase font-bold">Extra Attributes</label><button type="button" onclick="addAttrRow()" class="text-xs bg-indigo-900 text-indigo-300 px-2 py-1 rounded hover:bg-indigo-800 transition"><i class="fas fa-plus mr-1"></i> Add</button></div><div id="attributesContainer" class="space-y-2"></div></div></div><div class="p-4 border-t border-slate-800 flex justify-end gap-2 bg-slate-900 sticky bottom-0"><button type="button" onclick="document.getElementById('editModal').close()" class="px-4 py-2 text-sm text-gray-400 hover:text-white transition">Cancel</button><button type="submit" class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded text-sm font-bold">Save Changes</button></div></form></dialog>
    <dialog id="importStoryModal" class="rounded-xl bg-slate-900 border border-slate-700 text-gray-200 w-[500px] backdrop:bg-black/80"><div class="p-6"><h2 class="text-lg font-bold text-indigo-400 mb-4">Add New Story</h2><div class="flex gap-2 mb-4 border-b border-slate-700 pb-2"><button onclick="showImportTab('file')" id="tab-file" class="px-3 py-1 text-sm font-bold text-white border-b-2 border-indigo-500 transition">Upload File</button><button onclick="showImportTab('text')" id="tab-text" class="px-3 py-1 text-sm text-gray-400 hover:text-white transition">Write / Paste</button></div><form id="form-file" action="/import_story_file" method="post" enctype="multipart/form-data" class="space-y-4"><div><label class="text-xs font-bold text-gray-500 uppercase">Select File (.txt)</label><input type="file" name="file" accept=".txt" class="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-indigo-900 file:text-indigo-300 hover:file:bg-indigo-800 cursor-pointer mt-2 bg-slate-950 rounded border border-slate-700 p-1"/></div><div><label class="text-xs font-bold text-gray-500 uppercase">Campaign</label><select name="campaign" class="input-dark mt-1"><option value="Unsorted">Unsorted</option>{% for camp in campaigns %}{% if camp != "Unsorted" %}<option value="{{ camp }}">{{ camp }}</option>{% endif %}{% endfor %}</select></div><div class="flex justify-end gap-2 pt-2"><button type="button" onclick="this.closest('dialog').close()" class="text-gray-400 text-sm px-3 py-2">Cancel</button><button type="submit" class="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-bold">Upload</button></div></form><form id="form-text" action="/import_story_text" method="post" class="space-y-4 hidden"><div><label class="text-xs font-bold text-gray-500 uppercase">Story Title</label><input type="text" name="title" class="input-dark mt-1" placeholder="e.g. The Tavern Brawl" required></div><div><label class="text-xs font-bold text-gray-500 uppercase">Content</label><textarea name="content" rows="10" class="input-dark mt-1 font-mono text-xs" placeholder="Paste your log here..." required></textarea></div><div><label class="text-xs font-bold text-gray-500 uppercase">Campaign</label><select name="campaign" class="input-dark mt-1"><option value="Unsorted">Unsorted</option>{% for camp in campaigns %}{% if camp != "Unsorted" %}<option value="{{ camp }}">{{ camp }}</option>{% endif %}{% endfor %}</select></div><div class="flex justify-end gap-2 pt-2"><button type="button" onclick="this.closest('dialog').close()" class="text-gray-400 text-sm px-3 py-2">Cancel</button><button type="submit" class="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-bold">Save Story</button></div></form></div></dialog>

    <script>
        function showImportTab(tab) {
            if(tab === 'file') {
                document.getElementById('form-file').classList.remove('hidden'); document.getElementById('form-text').classList.add('hidden');
                document.getElementById('tab-file').classList.add('text-white', 'border-indigo-500', 'border-b-2'); document.getElementById('tab-file').classList.remove('text-gray-400');
                document.getElementById('tab-text').classList.add('text-gray-400'); document.getElementById('tab-text').classList.remove('text-white', 'border-indigo-500', 'border-b-2');
            } else {
                document.getElementById('form-file').classList.add('hidden'); document.getElementById('form-text').classList.remove('hidden');
                document.getElementById('tab-text').classList.add('text-white', 'border-indigo-500', 'border-b-2'); document.getElementById('tab-text').classList.remove('text-gray-400');
                document.getElementById('tab-file').classList.add('text-gray-400'); document.getElementById('tab-file').classList.remove('text-white', 'border-indigo-500', 'border-b-2');
            }
        }
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
            document.getElementById('modalBubbleColor').value = charData.bubble_color || '#1e293b'; 
            const attrs = charData.attributes || {};
            document.getElementById('modalAge').value = attrs.Age || '';
            document.getElementById('modalGender').value = attrs.Gender || '';
            document.getElementById('modalRace').value = attrs.Race || '';
            document.getElementById('modalOrient').value = attrs.Orientation || '';
            const container = document.getElementById('attributesContainer');
            container.innerHTML = '';
            const standard = ['Age', 'Gender', 'Race', 'Orientation'];
            for (const [key, value] of Object.entries(attrs)) { if (!standard.includes(key)) { addAttrRow(key, value); } }
            document.getElementById('editModal').showModal();
        }
        function addAttrRow(key = '', value = '') {
            const container = document.getElementById('attributesContainer');
            const div = document.createElement('div');
            div.className = 'flex gap-2 items-center';
            div.innerHTML = `<input type="text" name="attr_keys" value="${key}" placeholder="Label" class="input-dark w-1/3 text-xs font-bold text-indigo-300"><input type="text" name="attr_values" value="${value}" placeholder="Value" class="input-dark flex-1"><button type="button" onclick="this.parentElement.remove()" class="text-red-500 hover:text-red-400 px-2"><i class="fas fa-times"></i></button>`;
            container.appendChild(div);
        }
    </script>

</body>
</html>
"""

jinja_template = Template(HTML_TEMPLATE)

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
        campaigns=campaigns, 
        modals=MODALS_HTML # This variable no longer exists, Jinja will ignore it or you can remove this arg. 
                           # Actually, removing it is safer:
                           # modals=None
    )

@app.get("/stories", response_class=HTMLResponse)
async def stories_list(request: Request):
    active_campaign = request.query_params.get("campaign", None)
    structure = story_manager.list_stories_by_campaign()
    target_files = []
    if active_campaign and active_campaign in structure: target_files = structure[active_campaign]
    else:
        for camp_name, files in structure.items(): target_files.extend(files)
    stories_data = []
    for rel_path in target_files:
        full_path = os.path.join(story_manager.STORY_DIR, rel_path)
        stories_data.append({"path": rel_path, "meta": story_manager.get_story_meta(rel_path), "stats": story_parser.get_file_stats(full_path)})
    return jinja_template.render(mode="stories_list", campaigns=story_manager.get_campaigns(), active_campaign=active_campaign, stories=stories_data)

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
    
    # NEW: Fetch assigned prompts
    assigned_prompts = prompt_manager.get_prompts_for_character(char_id)
    
    return jinja_template.render(
        mode="char_profile", 
        char=char, 
        char_id=char_id, 
        stories=linked_stories,
        assigned_prompts=assigned_prompts # Pass to template
    )

@app.get("/read/{path:path}", response_class=HTMLResponse)
async def read_story(path: str):
    full_path = os.path.join(story_manager.STORY_DIR, path)
    if not os.path.exists(full_path): raise HTTPException(404, "File not found")
    blocks, local_stats = story_parser.parse_file(full_path)
    characters = character_manager.get_cast_for_story(path, local_stats)
    all_db_chars = character_manager.get_all_characters()
    char_map = {c['raw_name']: c for c in characters}
    meta = story_manager.get_story_meta(path)
    background_file = meta.get("background_file")
    return jinja_template.render(mode="read", blocks=blocks, characters=characters, all_db_chars=all_db_chars, filename=path, char_map=char_map, background_file=background_file)

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

@app.post("/upload_story_background")
async def upload_story_background(return_path: str = Form(...), file: UploadFile = File(...)):
    if file.filename: story_manager.save_story_background(return_path, file.file, file.filename)
    return RedirectResponse(url=f"/read/{return_path}", status_code=303)

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
async def update_character_details(char_id: str = Form(...), name: str = Form(...), description: str = Form(""), return_file: str = Form(None), bubble_color: str = Form("#1e293b"), avatar: Optional[UploadFile] = File(None), attr_keys: List[str] = Form([]), attr_values: List[str] = Form([])):
    avatar_filename = None
    if avatar and avatar.filename: avatar_filename = character_manager.save_avatar(char_id, avatar.file, avatar.filename)
    attributes = {}
    for k, v in zip(attr_keys, attr_values):
        if k.strip() and v.strip(): attributes[k.strip()] = v.strip()
    character_manager.update_character_data(char_id, name, description, attributes, bubble_color, avatar_filename)
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

@app.get("/export_character/{char_id}")
async def export_character(char_id: str):
    png_buffer = character_manager.export_character_card(char_id)
    if not png_buffer: raise HTTPException(404, "Character not found")
    char_name = character_manager.get_character(char_id).get("name", "character")
    safe_name = "".join(c for c in char_name if c.isalnum() or c in " _-").strip()
    return StreamingResponse(png_buffer, media_type="image/png", headers={"Content-Disposition": f"attachment; filename={safe_name}.png"})

@app.post("/import_character")
async def import_character(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".png"): raise HTTPException(400, "Only PNG files allowed")
    contents = await file.read()
    new_id = character_manager.import_character_card(contents)
    if not new_id: raise HTTPException(400, "Invalid Character Card")
    return RedirectResponse(url=f"/character/{new_id}", status_code=303)

@app.post("/import_story_file")
async def import_story_file(file: UploadFile = File(...), campaign: str = Form(...)):
    if not file.filename.lower().endswith(".txt"): raise HTTPException(400, "Only .txt files allowed")
    filename = story_manager.save_story_from_file(file.file, file.filename)
    if campaign != "Unsorted": story_manager.move_story_to_campaign(filename, campaign)
    return RedirectResponse(url="/stories", status_code=303)

@app.post("/import_story_text")
async def import_story_text(title: str = Form(...), content: str = Form(...), campaign: str = Form(...)):
    filename = story_manager.save_story_from_text(title, content)
    if campaign != "Unsorted": story_manager.move_story_to_campaign(filename, campaign)
    return RedirectResponse(url="/stories", status_code=303)

# NEW: Prompt Actions
@app.post("/create_prompt")
async def create_prompt(title: str = Form(...), content: str = Form(...), tags: str = Form(""), linked_chars: List[str] = Form([])):
    tag_list = tags.split(",")
    prompt_manager.create_prompt(title, content, tag_list, linked_chars)
    return RedirectResponse(url="/prompts", status_code=303)

@app.post("/delete_prompt")
async def delete_prompt(pid: str = Form(...)):
    prompt_manager.delete_prompt(pid)
    return RedirectResponse(url="/prompts", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, loop="asyncio")
