from jinja2 import Template

HTML_TEMPLATE_STRING = """
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
        .tag-emerald { background: #064e3b; color: #6ee7b7; border: 1px solid #059669; }
        .glass-panel { background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(8px); border: 1px solid rgba(51, 65, 85, 0.5); }
        
        .markdown-content p { margin-bottom: 0.5em; }
        .markdown-content strong { color: #fff; font-weight: bold; }
        .markdown-content em { color: #a5b4fc; font-style: italic; }
        .markdown-content ul { list-style-type: disc; padding-left: 1.5em; }
        .markdown-content h1, .markdown-content h2, .markdown-content h3 { font-weight: bold; color: #e0e7ff; margin-top: 0.5em; }

        /* Custom Color Grid */
        .color-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 0.5rem; }
        .color-btn { width: 100%; aspect-ratio: 1; border-radius: 0.375rem; border: 1px solid rgba(255,255,255,0.1); cursor: pointer; transition: transform 0.1s; }
        .color-btn:hover { transform: scale(1.1); z-index: 10; border-color: white; }
        .color-btn.selected { border: 2px solid white; transform: scale(1.1); box-shadow: 0 0 10px rgba(0,0,0,0.5); }
    </style>
</head>
<body class="bg-slate-950 text-gray-200 font-sans h-screen flex flex-col">

    <header class="bg-slate-900 border-b border-slate-800 p-4 shadow-lg flex justify-between items-center z-10 shrink-0 relative">
        <div class="flex items-center gap-6">
            <h1 class="text-xl font-bold text-indigo-400">StoryStash <span class="text-xs text-gray-500">v7.0</span></h1>
            <nav class="flex gap-4 text-sm font-medium">
                <a href="/" class="{{ 'text-white font-bold' if mode == 'dashboard' else 'text-gray-400 hover:text-white' }}">Dashboard</a>
                <a href="/stories" class="{{ 'text-white font-bold' if mode == 'stories_list' else 'text-gray-400 hover:text-white' }}">Stories</a>
                <a href="/characters" class="{{ 'text-white font-bold' if mode in ['char_list', 'char_profile'] else 'text-gray-400 hover:text-white' }}">Characters</a>
                <a href="/lore" class="{{ 'text-white font-bold' if mode in ['lore_list', 'lore_detail'] else 'text-gray-400 hover:text-white' }}">Lore</a>
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
            <a href="/edit_story/{{ filename }}" class="bg-slate-800 hover:bg-slate-700 text-gray-300 px-3 py-1 rounded text-sm border border-slate-700" title="Edit Raw Text"><i class="fas fa-edit"></i></a>
            <button onclick="document.getElementById('bgModal').showModal()" class="bg-slate-800 hover:bg-slate-700 text-gray-300 px-3 py-1 rounded text-sm border border-slate-700" title="Change Background"><i class="fas fa-image"></i></button>
            <button onclick="document.getElementById('castModal').showModal()" class="bg-slate-800 hover:bg-slate-700 text-gray-300 px-3 py-1 rounded text-sm border border-slate-700"><i class="fas fa-users-cog mr-2"></i> Manage Cast</button>
        </div>
        {% elif mode == 'prompts_list' %}
        <button onclick="document.getElementById('createPromptModal').showModal()" class="bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1 rounded text-sm font-bold shadow-lg shadow-indigo-500/20"><i class="fas fa-plus mr-2"></i> New Prompt</button>
        {% elif mode == 'lore_list' %}
        <button onclick="document.getElementById('createLoreModal').showModal()" class="bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1 rounded text-sm font-bold shadow-lg shadow-emerald-500/20"><i class="fas fa-plus mr-2"></i> New Object</button>
        {% endif %}
    </header>

    <main class="flex-1 overflow-hidden w-full flex justify-center p-6 gap-6 relative" style="{{ 'background-image: url(/backgrounds/' + background_file + '); background-size: cover; background-position: center;' if background_file else '' }}">
        {% if background_file %}<div class="absolute inset-0 bg-slate-950/80 backdrop-blur-sm pointer-events-none z-0"></div>{% endif %}

        {% if mode == 'dashboard' %}
            <div class="flex-1 max-w-6xl h-full overflow-y-auto space-y-8 z-10">
                <div><h2 class="text-3xl font-bold text-white mb-2">Welcome back.</h2><p class="text-gray-400">Here is an overview of your roleplay universe.</p></div>
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div class="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow-lg flex items-center gap-4"><div class="w-12 h-12 rounded-full bg-indigo-900/50 text-indigo-400 flex items-center justify-center text-xl"><i class="fas fa-book"></i></div><div><div class="text-2xl font-bold text-white">{{ stats.total_stories }}</div><div class="text-xs uppercase text-gray-500 font-bold tracking-wider">Stories</div></div></div>
                    <div class="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow-lg flex items-center gap-4"><div class="w-12 h-12 rounded-full bg-purple-900/50 text-purple-400 flex items-center justify-center text-xl"><i class="fas fa-users"></i></div><div><div class="text-2xl font-bold text-white">{{ stats.total_chars }}</div><div class="text-xs uppercase text-gray-500 font-bold tracking-wider">Characters</div></div></div>
                    <div class="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow-lg flex items-center gap-4"><div class="w-12 h-12 rounded-full bg-emerald-900/50 text-emerald-400 flex items-center justify-center text-xl"><i class="fas fa-globe"></i></div><div><div class="text-2xl font-bold text-white">{{ stats.total_lore }}</div><div class="text-xs uppercase text-gray-500 font-bold tracking-wider">Lore Objects</div></div></div>
                    <div class="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow-lg flex items-center gap-4"><div class="w-12 h-12 rounded-full bg-amber-900/50 text-amber-400 flex items-center justify-center text-xl"><i class="fas fa-lightbulb"></i></div><div><div class="text-2xl font-bold text-white">{{ stats.total_prompts }}</div><div class="text-xs uppercase text-gray-500 font-bold tracking-wider">Prompts</div></div></div>
                </div>
                </div>
            {{ modals | safe }}

        {% elif mode == 'lore_list' %}
            <div class="flex-1 max-w-6xl h-full overflow-y-auto z-10">
                <div class="flex justify-between items-center mb-6"><h2 class="text-2xl font-bold text-white">World Lore</h2></div>
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                    {% for lid, item in lore_items.items() %}
                    <a href="/lore/{{ lid }}" class="block bg-slate-900 border border-slate-800 rounded-xl overflow-hidden hover:border-emerald-500 transition group h-64 flex flex-col">
                        <div class="h-32 bg-slate-800 w-full relative">
                            {% if item.image %}
                            <img src="/lore_images/{{ item.image }}" class="w-full h-full object-cover">
                            {% else %}
                            <div class="w-full h-full flex items-center justify-center text-4xl text-white/10"><i class="fas fa-book-open"></i></div>
                            {% endif %}
                            <div class="absolute top-2 right-2 bg-black/60 text-white text-[10px] px-2 py-1 rounded uppercase font-bold backdrop-blur-sm border border-white/10">{{ item.type }}</div>
                        </div>
                        <div class="p-4 flex-1 flex flex-col">
                            <h3 class="font-bold text-gray-200 mb-1 truncate">{{ item.title }}</h3>
                            <div class="text-xs text-gray-500 mb-2 line-clamp-2 italic">{{ item.content }}</div>
                            <div class="mt-auto flex flex-wrap gap-1">
                                {% for tag in item.tags[:3] %}<span class="tag tag-emerald">{{ tag }}</span>{% endfor %}
                            </div>
                        </div>
                    </a>
                    {% endfor %}
                </div>
            </div>
            
            <dialog id="createLoreModal" class="rounded-xl bg-slate-900 border border-slate-700 text-gray-200 w-[600px] backdrop:bg-black/80">
                <form action="/create_lore" method="post" class="flex flex-col h-[80vh]">
                    <div class="p-6 border-b border-slate-800"><h2 class="text-lg font-bold text-emerald-400">Create Lore Object</h2></div>
                    <div class="p-6 overflow-y-auto space-y-4 flex-1">
                        <div class="grid grid-cols-2 gap-4">
                            <div><label class="text-xs font-bold text-gray-500 uppercase">Title</label><input type="text" name="title" class="input-dark mt-1" required></div>
                            <div>
                                <label class="text-xs font-bold text-gray-500 uppercase">Type</label>
                                <select name="type_category" class="input-dark mt-1">
                                    <option value="Item">Item</option>
                                    <option value="Location">Location</option>
                                    <option value="History">History</option>
                                    <option value="Faction">Faction</option>
                                    <option value="NPC">NPC</option>
                                    <option value="Note">Note</option>
                                    <option value="Other">Other</option>
                                </select>
                            </div>
                        </div>
                        <div><label class="text-xs font-bold text-gray-500 uppercase">Content</label><textarea name="content" rows="10" class="input-dark mt-1 font-serif text-sm" required></textarea></div>
                        <div><label class="text-xs font-bold text-gray-500 uppercase">Tags</label><input type="text" name="tags" class="input-dark mt-1" placeholder="e.g. Magic, Rare, Ancient"></div>
                    </div>
                    <div class="p-4 border-t border-slate-800 flex justify-end gap-2 bg-slate-900">
                        <button type="button" onclick="this.closest('dialog').close()" class="text-gray-400 text-sm px-3 py-2">Cancel</button>
                        <button type="submit" class="bg-emerald-600 text-white px-4 py-2 rounded text-sm font-bold">Create</button>
                    </div>
                </form>
            </dialog>

        {% elif mode == 'lore_detail' %}
            <div class="flex-1 h-full overflow-hidden flex gap-8 z-10">
                <aside class="w-80 shrink-0 h-full overflow-y-auto space-y-6">
                    <div class="bg-slate-900 rounded-xl border border-slate-800 p-6 flex flex-col shadow-lg relative group">
                         <button onclick="document.getElementById('editLoreModal').showModal()" class="absolute top-2 right-2 text-gray-500 hover:text-emerald-400" title="Edit"><i class="fas fa-pencil-alt"></i></button>
                         <form action="/delete_lore" method="post" onsubmit="return confirm('Delete?');" class="absolute top-2 left-2">
                            <input type="hidden" name="lid" value="{{ item.id }}">
                            <button type="submit" class="text-gray-600 hover:text-red-500"><i class="fas fa-trash"></i></button>
                        </form>
                        
                        <div class="w-full aspect-video bg-slate-800 rounded-lg overflow-hidden border border-slate-700 mb-4">
                            {% if item.image %}
                            <img src="/lore_images/{{ item.image }}" class="w-full h-full object-cover">
                            {% else %}
                            <div class="w-full h-full flex items-center justify-center text-4xl text-white/10"><i class="fas fa-image"></i></div>
                            {% endif %}
                        </div>
                        
                        <h1 class="text-2xl font-bold text-white mb-2">{{ item.title }}</h1>
                        <div class="flex items-center gap-2 mb-4">
                            <span class="px-2 py-0.5 rounded bg-emerald-900/50 text-emerald-400 border border-emerald-800 text-xs font-bold uppercase">{{ item.type }}</span>
                            <span class="text-xs text-gray-500">{{ item.created_at }}</span>
                        </div>
                        
                        <div class="border-t border-slate-800 pt-4">
                            <h3 class="text-xs font-bold text-gray-500 uppercase mb-2">Tags</h3>
                            <div class="flex flex-wrap gap-1">
                                {% for tag in item.tags %}<span class="tag tag-gray">{{ tag }}</span>{% endfor %}
                            </div>
                        </div>
                    </div>
                </aside>
                
                <div class="flex-1 h-full overflow-y-auto bg-slate-900/50 rounded-xl border border-slate-800 p-8">
                     <div class="markdown-content text-gray-300 leading-relaxed font-serif text-lg whitespace-pre-wrap">{{ item.content }}</div>
                </div>
            </div>
            
            <dialog id="editLoreModal" class="rounded-xl bg-slate-900 border border-slate-700 text-gray-200 w-[600px] backdrop:bg-black/80">
                <form action="/update_lore" method="post" enctype="multipart/form-data" class="flex flex-col h-[80vh]">
                    <input type="hidden" name="lid" value="{{ item.id }}">
                    <div class="p-6 border-b border-slate-800"><h2 class="text-lg font-bold text-emerald-400">Edit Object</h2></div>
                    <div class="p-6 overflow-y-auto space-y-4 flex-1">
                        <div class="grid grid-cols-2 gap-4">
                            <div><label class="text-xs font-bold text-gray-500 uppercase">Title</label><input type="text" name="title" value="{{ item.title }}" class="input-dark mt-1"></div>
                            <div>
                                <label class="text-xs font-bold text-gray-500 uppercase">Type</label>
                                <select name="type_category" class="input-dark mt-1">
                                    <option value="Item" {% if item.type == 'Item' %}selected{% endif %}>Item</option>
                                    <option value="Location" {% if item.type == 'Location' %}selected{% endif %}>Location</option>
                                    <option value="History" {% if item.type == 'History' %}selected{% endif %}>History</option>
                                    <option value="Faction" {% if item.type == 'Faction' %}selected{% endif %}>Faction</option>
                                    <option value="NPC" {% if item.type == 'NPC' %}selected{% endif %}>NPC</option>
                                    <option value="Note" {% if item.type == 'Note' %}selected{% endif %}>Note</option>
                                    <option value="Other" {% if item.type == 'Other' %}selected{% endif %}>Other</option>
                                </select>
                            </div>
                        </div>
                        <div><label class="text-xs font-bold text-gray-500 uppercase">Image</label><input type="file" name="image" accept="image/*" class="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-indigo-900 file:text-indigo-300 hover:file:bg-indigo-800 cursor-pointer mt-2 bg-slate-950 rounded border border-slate-700 p-1"/></div>
                        <div><label class="text-xs font-bold text-gray-500 uppercase">Content</label><textarea name="content" rows="10" class="input-dark mt-1 font-serif text-sm">{{ item.content }}</textarea></div>
                        <div><label class="text-xs font-bold text-gray-500 uppercase">Tags</label><input type="text" name="tags" value="{{ ', '.join(item.tags) }}" class="input-dark mt-1"></div>
                    </div>
                    <div class="p-4 border-t border-slate-800 flex justify-end gap-2 bg-slate-900">
                        <button type="button" onclick="this.closest('dialog').close()" class="text-gray-400 text-sm px-3 py-2">Cancel</button>
                        <button type="submit" class="bg-emerald-600 text-white px-4 py-2 rounded text-sm font-bold">Save Changes</button>
                    </div>
                </form>
            </dialog>

        {% elif mode == 'prompts_list' %}
            <div class="flex-1 max-w-6xl h-full overflow-y-auto z-10">
                <div class="flex justify-between items-center mb-6"><h2 class="text-2xl font-bold text-white">Roleplay Prompts</h2></div>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">{% for pid, prompt in prompts.items() %}<div class="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-indigo-500 transition flex flex-col h-[300px] relative group"><form action="/delete_prompt" method="post" class="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition" onsubmit="return confirm('Delete prompt?');"><input type="hidden" name="pid" value="{{ pid }}"><button class="text-gray-600 hover:text-red-500"><i class="fas fa-trash"></i></button></form><h3 class="text-lg font-bold text-indigo-400 mb-2 truncate">{{ prompt.title }}</h3><div class="flex flex-wrap gap-2 mb-4">{% for tag in prompt.tags %}<span class="tag tag-purple">{{ tag }}</span>{% endfor %}</div><div class="flex-1 bg-slate-950/50 p-3 rounded text-sm text-gray-300 overflow-y-auto mb-4 font-serif leading-relaxed italic whitespace-pre-wrap">{{ prompt.content }}</div><div class="border-t border-slate-800 pt-3 flex items-center gap-2 overflow-x-auto"><span class="text-[10px] uppercase font-bold text-gray-600 shrink-0">Assigned:</span>{% if prompt.linked_chars %}{% for cid in prompt.linked_chars %}{% if all_chars.get(cid) %}<div class="w-6 h-6 rounded-full bg-slate-800 border border-slate-600 overflow-hidden shrink-0" title="{{ all_chars[cid].name }}">{% if all_chars[cid].avatar_file %}<img src="/avatars/{{ all_chars[cid].avatar_file }}" class="w-full h-full object-cover">{% else %}<div class="w-full h-full flex items-center justify-center text-[8px]">{{ all_chars[cid].name[:1] }}</div>{% endif %}</div>{% endif %}{% endfor %}{% else %}<span class="text-[10px] text-gray-600 italic">None</span>{% endif %}</div></div>{% endfor %}</div>
            </div>
            <dialog id="createPromptModal" class="rounded-xl bg-slate-900 border border-slate-700 text-gray-200 w-[600px] backdrop:bg-black/80"><form action="/create_prompt" method="post" class="flex flex-col h-[80vh]"><div class="p-6 border-b border-slate-800"><h2 class="text-lg font-bold text-indigo-400">Create New Prompt</h2></div><div class="p-6 overflow-y-auto space-y-4 flex-1"><div><label class="text-xs font-bold text-gray-500 uppercase">Title</label><input type="text" name="title" class="input-dark mt-1" required></div><div><label class="text-xs font-bold text-gray-500 uppercase">Prompt Content</label><textarea name="content" rows="8" class="input-dark mt-1 font-serif text-sm" required></textarea></div><div><label class="text-xs font-bold text-gray-500 uppercase">Tags (comma separated)</label><input type="text" name="tags" class="input-dark mt-1" placeholder="e.g. Romance, Sci-Fi, Conflict"></div><div><label class="text-xs font-bold text-gray-500 uppercase block mb-2">Assign Characters</label><div class="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto bg-slate-950 p-2 rounded border border-slate-800">{% for cid, char in all_chars.items() %}<label class="flex items-center gap-2 text-sm text-gray-300 hover:bg-slate-900 p-1 rounded cursor-pointer"><input type="checkbox" name="linked_chars" value="{{ cid }}" class="accent-indigo-500"><div class="w-5 h-5 rounded-full bg-slate-800 overflow-hidden">{% if char.avatar_file %}<img src="/avatars/{{ char.avatar_file }}" class="w-full h-full object-cover">{% else %}<div class="w-full h-full flex items-center justify-center text-[8px]">{{ char.name[:1] }}</div>{% endif %}</div><span class="truncate">{{ char.name }}</span></label>{% endfor %}</div></div></div><div class="p-4 border-t border-slate-800 flex justify-end gap-2 bg-slate-900"><button type="button" onclick="this.closest('dialog').close()" class="text-gray-400 text-sm px-3 py-2">Cancel</button><button type="submit" class="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-bold">Create Prompt</button></div></form></dialog>

        {% elif mode == 'char_list' %}
            <div class="flex-1 h-full overflow-y-auto z-10"><div class="flex justify-between items-center mb-6"><h2 class="text-2xl font-bold text-white">Character Database</h2><div class="flex gap-4 items-center"><form action="/import_character" method="post" enctype="multipart/form-data" class="flex gap-2"><label class="cursor-pointer bg-slate-800 hover:bg-slate-700 text-gray-300 px-3 py-1 rounded text-sm border border-slate-700 font-medium"><i class="fas fa-file-import mr-1"></i> Import Card (PNG)<input type="file" name="file" accept=".png" class="hidden" onchange="this.form.submit()"></label></form><form action="/create_character_quick" method="post" class="flex gap-2 border-l border-slate-700 pl-4"><input type="text" name="name" placeholder="New Character Name" class="input-dark py-1 px-3 w-64" required><button type="submit" class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-1 rounded text-sm font-bold">Create</button></form></div></div><div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">{% for id, char in all_chars.items() %}<a href="/character/{{ id }}" class="block bg-slate-900 rounded-xl border border-slate-800 overflow-hidden hover:border-indigo-500 hover:shadow-lg transition group"><div class="aspect-square bg-slate-800 w-full relative">{% if char.get('avatar_file') %}<img src="/avatars/{{ char.avatar_file }}" class="w-full h-full object-cover">{% else %}<div class="w-full h-full flex items-center justify-center text-4xl font-bold text-white/20">{{ char.get('name', '?')[:1] }}</div>{% endif %}<div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-3 pt-8"><h3 class="font-bold text-white truncate">{{ char.get('name', 'Unknown') }}</h3></div></div></a>{% endfor %}</div></div>

        {% elif mode == 'char_profile' %}
            <div class="flex-1 h-full overflow-hidden flex gap-8 z-10">
                <aside class="w-80 shrink-0 h-full overflow-y-auto space-y-6">
                    <div class="bg-slate-900 rounded-xl border border-slate-800 p-6 flex flex-col items-center shadow-lg relative group">
                        <button onclick='openEditModal({{ char | tojson }})' class="absolute top-2 right-2 text-gray-500 hover:text-indigo-400" title="Edit"><i class="fas fa-pencil-alt"></i></button>
                        <form action="/delete_character" method="post" onsubmit="return confirm('Delete?');"><input type="hidden" name="char_id" value="{{ char_id }}"><button type="submit" class="absolute top-2 left-2 text-gray-600 hover:text-red-500 transition" title="Delete"><i class="fas fa-trash"></i></button></form>
                        <a href="/export_character/{{ char_id }}" target="_blank" class="absolute bottom-2 right-2 text-gray-600 hover:text-blue-400 transition" title="Export Card"><i class="fas fa-address-card"></i></a>
                        <div class="w-48 h-48 rounded-lg shadow-2xl border-2 border-slate-700 overflow-hidden mb-4 bg-slate-800">{% if char.get('avatar_file') %}<img src="/avatars/{{ char.avatar_file }}" class="w-full h-full object-cover">{% else %}<div class="w-full h-full flex items-center justify-center text-6xl font-bold text-white/20">{{ char.get('name', '?')[:1] }}</div>{% endif %}</div>
                        <h1 class="text-2xl font-bold text-white text-center">{{ char.get('name', 'Unknown') }}</h1>
                        <div class="w-full mt-6 space-y-3">
                            <div class="flex justify-between border-b border-slate-800 pb-1"><span class="text-xs uppercase text-gray-500 font-bold">Age</span><span class="text-sm text-gray-200">{{ char.attributes.get('Age', 'Unknown') }}</span></div>
                            <div class="flex justify-between border-b border-slate-800 pb-1"><span class="text-xs uppercase text-gray-500 font-bold">Gender</span><span class="text-sm text-gray-200">{{ char.attributes.get('Gender', 'Unknown') }}</span></div>
                            <div class="flex justify-between border-b border-slate-800 pb-1"><span class="text-xs uppercase text-gray-500 font-bold">Race</span><span class="text-sm text-gray-200">{{ char.attributes.get('Race', 'Unknown') }}</span></div>
                            <div class="flex justify-between border-b border-slate-800 pb-1"><span class="text-xs uppercase text-gray-500 font-bold">Orientation</span><span class="text-sm text-gray-200">{{ char.attributes.get('Orientation', 'Unknown') }}</span></div>
                            {% for key, val in char.attributes.items() %}{% if key not in ['Age', 'Gender', 'Race', 'Orientation'] %}<div class="flex justify-between border-b border-slate-800 pb-1"><span class="text-xs uppercase text-gray-500 font-bold truncate max-w-[100px]">{{ key }}</span><span class="text-sm text-gray-400 truncate">{{ val }}</span></div>{% endif %}{% endfor %}
                        </div>
                    </div>
                    {% if played_by_list %}
                    <div class="bg-slate-900 rounded-xl border border-slate-800 p-4 shadow-lg">
                        <h2 class="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3 border-b border-slate-800 pb-2">Played By</h2>
                        <div class="flex flex-wrap gap-2">{% for player in played_by_list %}<span class="px-2 py-1 rounded bg-slate-800 border border-slate-700 text-xs text-indigo-300 font-mono">{{ player }}</span>{% endfor %}</div>
                    </div>
                    {% endif %}
                </aside>
                <div class="flex-1 h-full overflow-y-auto space-y-8 pr-4">
                    {% if assigned_prompts %}<section><h2 class="text-xl font-bold text-amber-400 mb-2 border-b border-slate-800 pb-2"><i class="fas fa-lightbulb mr-2"></i> Assigned Prompts</h2><div class="grid grid-cols-1 md:grid-cols-2 gap-4">{% for p in assigned_prompts %}<div class="bg-slate-900 border border-slate-800 p-4 rounded-lg hover:border-amber-500/50 transition"><h3 class="font-bold text-gray-200 mb-2">{{ p.title }}</h3><div class="text-xs text-gray-400 italic line-clamp-3 mb-2">{{ p.content }}</div><div class="flex flex-wrap gap-1">{% for tag in p.tags %}<span class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-gray-500 border border-slate-700">{{ tag }}</span>{% endfor %}</div></div>{% endfor %}</div></section>{% endif %}
                    <section><h2 class="text-xl font-bold text-indigo-400 mb-2 border-b border-slate-800 pb-2">Biography</h2><div class="bg-slate-900/50 p-6 rounded-xl border border-slate-800 text-gray-300 leading-relaxed italic whitespace-pre-wrap">{{ char.description or "No biography." }}</div></section>
                    <section><h2 class="text-xl font-bold text-indigo-400 mb-2 border-b border-slate-800 pb-2">Appears In</h2><div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">{% for story_path in stories %}<a href="/read/{{ story_path }}" class="block bg-slate-900 p-4 rounded-lg border border-slate-800 hover:border-indigo-500 transition"><i class="fas fa-file-alt text-indigo-500 mr-2"></i> {{ story_path }}</a>{% endfor %}{% if not stories %}<p class="text-gray-500 text-sm">Not linked to any stories.</p>{% endif %}</div></section>
                    <section><div class="flex justify-between items-center mb-2 border-b border-slate-800 pb-2"><h2 class="text-xl font-bold text-indigo-400">Gallery</h2><form action="/upload_gallery" method="post" enctype="multipart/form-data"><input type="hidden" name="char_id" value="{{ char_id }}"><label class="cursor-pointer bg-slate-800 hover:bg-slate-700 text-xs px-3 py-1 rounded border border-slate-700 text-gray-300"><i class="fas fa-upload mr-1"></i> Add Image<input type="file" name="image" class="hidden" onchange="this.form.submit()"></label></form></div><div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">{% for img in char.get('gallery', []) %}<div class="aspect-square rounded-lg overflow-hidden border border-slate-800 bg-black cursor-pointer hover:border-indigo-500 transition" onclick="window.open('/gallery/{{ img }}', '_blank')"><img src="/gallery/{{ img }}" class="w-full h-full object-cover"></div>{% endfor %}</div></section>
                </div>
            </div>
            {{ modals | safe }}

        {% elif mode == 'edit_story' %}
            <div class="flex-1 max-w-4xl h-full overflow-hidden flex flex-col z-10">
                <div class="flex justify-between items-center mb-4"><h2 class="text-2xl font-bold text-white">Edit Story Content</h2><div class="flex gap-2"><a href="/read/{{ filename }}" class="text-gray-400 hover:text-white px-4 py-2 text-sm font-medium">Cancel</a><button form="editForm" type="submit" class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded text-sm font-bold shadow-lg shadow-indigo-500/20">Save Changes</button></div></div>
                <form id="editForm" action="/save_story_text" method="post" class="flex-1 border border-slate-700 rounded-xl overflow-hidden shadow-2xl"><input type="hidden" name="path" value="{{ filename }}"><textarea name="content" class="w-full h-full bg-slate-950 text-gray-300 p-6 font-mono text-sm resize-none focus:outline-none leading-relaxed">{{ content }}</textarea></form>
            </div>

        {% elif mode == 'search' %}
            <div class="flex-1 max-w-4xl h-full overflow-y-auto z-10"><h2 class="text-2xl font-bold text-white mb-6">Search Results for "<span class="text-indigo-400">{{ query }}</span>"</h2><div class="space-y-4">{% for result in results %}<div class="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-indigo-500 transition"><a href="/read/{{ result.path }}" class="block"><h3 class="font-bold text-lg text-indigo-400 mb-1"><i class="fas fa-file-alt mr-2"></i> {{ result.title }}</h3><div class="text-xs text-gray-500 mb-3">{{ result.path }}</div><div class="space-y-2">{% for match in result.matches %}<div class="text-sm text-gray-300 font-mono bg-slate-950 p-2 rounded border-l-2 border-indigo-500/50">...{{ match }}...</div>{% endfor %}</div></a></div>{% endfor %}{% if not results %}<div class="text-center text-gray-500 mt-20"><i class="fas fa-ghost text-4xl mb-4 opacity-50"></i><p>No results found.</p></div>{% endif %}</div></div>
        
        {% elif mode == 'stories_list' %}
            <aside class="w-64 shrink-0 bg-slate-900/50 rounded-xl border border-slate-800 p-4 h-full overflow-y-auto z-10">
                <div class="flex justify-between items-center mb-4"><h2 class="text-xs font-bold text-gray-500 uppercase tracking-widest">Campaigns</h2><button onclick="document.getElementById('campaignModal').showModal()" class="text-xs text-indigo-400 hover:text-indigo-300"><i class="fas fa-plus"></i></button></div>
                <nav class="space-y-1"><a href="/stories" class="block px-3 py-2 rounded text-sm {{ 'bg-indigo-900/50 text-indigo-200' if not active_campaign else 'text-gray-400 hover:bg-slate-800 hover:text-white' }}"><i class="fas fa-layer-group w-5"></i> All Stories</a>{% for camp in campaigns %}{% if camp != "Unsorted" %}<a href="/stories?campaign={{ camp }}" class="block px-3 py-2 rounded text-sm {{ 'bg-indigo-900/50 text-indigo-200' if active_campaign == camp else 'text-gray-400 hover:bg-slate-800 hover:text-white' }}"><i class="fas fa-folder w-5 text-yellow-600"></i> {{ camp }}</a>{% endif %}{% endfor %}</nav>
                <div class="mt-6 border-t border-slate-800 pt-4"><button onclick="document.getElementById('importStoryModal').showModal()" class="block w-full text-left px-3 py-2 rounded text-sm text-gray-400 hover:bg-slate-800 hover:text-white transition"><i class="fas fa-file-import w-5 text-green-500"></i> Import / Write</button></div>
            </aside>
            <div class="flex-1 h-full overflow-y-auto pr-2 z-10"><div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">{% for item in stories %}<div class="bg-slate-900 rounded-xl border border-slate-800 shadow-lg hover:border-indigo-500/50 transition flex flex-col h-[280px] group relative"><button onclick='openStoryMetaModal({{ item | tojson }})' class="absolute top-2 right-2 z-10 text-gray-500 hover:text-indigo-400 opacity-0 group-hover:opacity-100 transition p-2"><i class="fas fa-cog"></i></button><a href="/read/{{ item.path }}" class="flex-1 flex flex-col p-5"><div class="mb-3"><h3 class="font-bold text-lg text-gray-100 leading-tight line-clamp-1" title="{{ item.meta.display_title }}">{{ item.meta.display_title }}</h3><div class="text-[10px] text-gray-500 mt-1 flex gap-2"><span><i class="far fa-clock"></i> {{ item.stats.date }}</span><span><i class="far fa-comment-alt"></i> {{ item.stats.msg_count }}</span></div></div><div class="text-yellow-500 text-xs mb-1">{% for i in range(item.meta.rating) %}<i class="fas fa-star"></i>{% endfor %}</div><div class="flex-1 text-xs text-gray-400 italic line-clamp-4 leading-relaxed overflow-hidden">{{ item.meta.synopsis }}</div>{% if item.stats.top_characters %}<div class="mt-3 flex -space-x-2 overflow-hidden py-1">{% for char in item.stats.top_characters %}<div class="inline-block h-6 w-6 rounded-full ring-2 ring-slate-900 bg-indigo-500 flex items-center justify-center text-[8px] font-bold text-white">{{ char[:1] }}</div>{% endfor %}</div>{% endif %}</a><div class="p-3 border-t border-slate-800 bg-slate-950/30 rounded-b-xl flex gap-2 overflow-x-auto">{% if item.meta.tags %}{% for tag in item.meta.tags %}<span class="tag tag-blue">{{ tag }}</span>{% endfor %}{% else %}<span class="tag tag-gray">No Tags</span>{% endif %}</div></div>{% endfor %}</div></div>
            {{ modals | safe }}

        {% elif mode == 'edit_story' %}
            <div class="flex-1 max-w-4xl h-full overflow-hidden flex flex-col z-10">
                <div class="flex justify-between items-center mb-4"><h2 class="text-2xl font-bold text-white">Edit Story Content</h2><div class="flex gap-2"><a href="/read/{{ filename }}" class="text-gray-400 hover:text-white px-4 py-2 text-sm font-medium">Cancel</a><button form="editForm" type="submit" class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded text-sm font-bold shadow-lg shadow-indigo-500/20">Save Changes</button></div></div>
                <form id="editForm" action="/save_story_text" method="post" class="flex-1 border border-slate-700 rounded-xl overflow-hidden shadow-2xl"><input type="hidden" name="path" value="{{ filename }}"><textarea name="content" class="w-full h-full bg-slate-950 text-gray-300 p-6 font-mono text-sm resize-none focus:outline-none leading-relaxed">{{ content }}</textarea></form>
            </div>

        {% elif mode == 'read' %}
            <aside class="w-80 hidden md:block shrink-0 sidebar-container space-y-6 z-10">
                {% for char in characters %}
                <div class="glass-panel rounded-xl overflow-hidden shadow-lg flex flex-col relative group">
                    {% if char.id %}<a href="/character/{{ char.id }}" class="absolute top-2 left-2 z-10 bg-black/50 hover:bg-indigo-600 text-white p-2 rounded-full opacity-0 group-hover:opacity-100 transition"><i class="fas fa-external-link-alt text-xs"></i></a><button onclick='openEditModal({{ char | tojson }})' class="absolute top-2 right-2 z-10 bg-black/50 hover:bg-indigo-600 text-white p-2 rounded-full opacity-0 group-hover:opacity-100 transition"><i class="fas fa-pencil-alt text-xs"></i></button>{% else %}<div class="absolute top-2 right-2 z-10 bg-black/50 text-xs text-gray-400 px-2 py-1 rounded pointer-events-none">Unlinked</div>{% endif %}
                    <div class="w-full flex justify-center pt-4 pb-2 bg-slate-800/50">{% if char.avatar_url %}<img src="{{ char.avatar_url }}" class="w-[200px] h-[200px] object-cover rounded shadow-md border border-gray-700">{% else %}<div class="w-[200px] h-[200px] flex items-center justify-center font-bold text-white shadow-md rounded border border-gray-700 text-6xl select-none" style="background-color: {{ char.color }};">{{ char.display_name[:1] }}</div>{% endif %}</div>
                    <div class="p-4 border-t border-gray-800 bg-gray-900/90">
                        <h3 class="font-bold text-lg text-gray-100 truncate text-center mb-3">{{ char.display_name }}</h3>
                        <div class="grid grid-cols-2 gap-2 text-xs text-gray-400 mb-3 bg-slate-950/50 p-2 rounded"><div><span class="block text-[9px] uppercase font-bold text-gray-600">Age</span>{{ char.attributes.get('Age', '-') }}</div><div><span class="block text-[9px] uppercase font-bold text-gray-600">Gender</span>{{ char.attributes.get('Gender', '-') }}</div><div><span class="block text-[9px] uppercase font-bold text-gray-600">Race</span>{{ char.attributes.get('Race', '-') }}</div><div><span class="block text-[9px] uppercase font-bold text-gray-600">Orient.</span>{{ char.attributes.get('Orientation', '-') }}</div></div>
                        {% if char.id %}
                        <form action="/set_story_player" method="post" class="mt-2 pt-2 border-t border-gray-800">
                            <input type="hidden" name="filename" value="{{ filename }}">
                            <input type="hidden" name="char_id" value="{{ char.id }}">
                            <div class="flex items-center gap-1">
                                <label class="text-[9px] uppercase font-bold text-gray-600 shrink-0">Played By</label>
                                <input type="text" name="player_name" value="{{ player_map.get(char.id, '') }}" class="bg-transparent text-xs text-indigo-300 border-b border-gray-700 w-full focus:outline-none focus:border-indigo-500 ml-1" placeholder="Username" onchange="this.form.submit()">
                            </div>
                        </form>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </aside>
            <div class="flex-1 max-w-4xl h-full overflow-y-auto pr-2 z-10"><div class="glass-panel rounded-xl shadow-2xl p-8 min-h-full"><div class="space-y-6">{% for block in blocks %}{% if block.type == 'ooc' %}<div class="flex justify-center my-4 opacity-75"><div class="bg-gray-800 border border-gray-600 text-gray-400 text-xs px-4 py-1 rounded-full uppercase tracking-wider">(( {{ block.text | safe }} ))</div></div>{% elif block.type == 'dialogue' %}<div class="flex flex-col space-y-1"><span class="text-xs font-bold text-indigo-400 ml-1 drop-shadow-md">{{ block.speaker }}</span>{% set speaker_char = char_map.get(block.speaker) %}{% set bubble_color = speaker_char.bubble_color if speaker_char else '#1f2937' %}<div class="text-gray-100 p-3 rounded-2xl rounded-tl-none inline-block max-w-[85%] self-start shadow-sm leading-relaxed border" style="background-color: {{ bubble_color }}DD; border-color: {{ bubble_color }};"><div class="markdown-content">{% for line in block.lines %}{{ line.content | safe }}{% endfor %}</div></div></div>{% else %}<div class="text-gray-300 leading-relaxed bg-black/40 p-4 rounded-lg border-l-2 border-indigo-500/50 backdrop-blur-sm"><div class="markdown-content">{{ block.text | safe }}</div></div>{% endif %}{% endfor %}</div><div class="mt-20 pt-10 border-t border-gray-800 text-center text-gray-600 text-sm">End of File</div></div></div><div class="w-10 hidden xl:block shrink-0"></div>
            <dialog id="castModal" class="rounded-xl shadow-2xl bg-slate-900 border border-slate-700 text-gray-200 w-[600px] backdrop:bg-black/80"><div class="p-6 border-b border-slate-800 flex justify-between items-center"><h2 class="text-lg font-bold text-indigo-400">Manage Cast</h2><button onclick="document.getElementById('castModal').close()" class="text-gray-500 hover:text-white"><i class="fas fa-times"></i></button></div><div class="p-6 max-h-[70vh] overflow-y-auto"><table class="w-full text-left text-sm"><thead class="text-xs text-gray-500 uppercase border-b border-slate-700"><tr><th class="py-2">Name in Story</th><th class="py-2">Database Character</th></tr></thead><tbody class="divide-y divide-slate-800">{% for char in characters %}<tr><td class="py-3 font-bold text-gray-300">{{ char.raw_name }}</td><td class="py-3"><form action="/link_character" method="POST" class="flex gap-2"><input type="hidden" name="filename" value="{{ filename }}"><input type="hidden" name="raw_name" value="{{ char.raw_name }}"><select name="char_id" class="input-dark text-xs py-1"><option value="">-- Unlinked --</option><option value="NEW">➕ Create New</option>{% for db_id, db_data in all_db_chars.items() %}<option value="{{ db_id }}" {% if char.id == db_id %}selected{% endif %}>{{ db_data.get('name', 'Unknown') }}</option>{% endfor %}</select><button type="submit" class="bg-indigo-900 hover:bg-indigo-700 text-indigo-200 px-2 rounded text-xs">Save</button></form></td></tr>{% endfor %}</tbody></table></div></dialog>
            <dialog id="bgModal" class="rounded-xl bg-slate-900 border border-slate-700 text-gray-200 w-96 backdrop:bg-black/80"><form action="/upload_story_background" method="post" enctype="multipart/form-data" class="p-6"><h2 class="text-lg font-bold text-indigo-400 mb-4">Change Story Background</h2><input type="hidden" name="return_path" value="{{ filename }}"><input type="file" name="file" accept="image/*" class="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-indigo-900 file:text-indigo-300 hover:file:bg-indigo-800 cursor-pointer mb-4 bg-slate-950 rounded border border-slate-700 p-1"/><div class="flex justify-end gap-2"><button type="button" onclick="this.closest('dialog').close()" class="text-gray-400 text-sm px-3 py-2">Cancel</button><button type="submit" class="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-bold">Upload</button></div></form></dialog>
        {% endif %}

    </main>
    
    <dialog id="campaignModal" class="rounded-xl bg-slate-900 border border-slate-700 text-gray-200 w-96 backdrop:bg-black/80"><form action="/create_campaign" method="post" class="p-6"><h2 class="text-lg font-bold text-indigo-400 mb-4">New Campaign</h2><input type="text" name="name" placeholder="Name" class="input-dark mb-4" required><div class="flex justify-end gap-2"><button type="button" onclick="this.closest('dialog').close()" class="text-gray-400 text-sm px-3 py-2">Cancel</button><button type="submit" class="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-bold">Create</button></div></form></dialog>
    <dialog id="storyMetaModal" class="rounded-xl bg-slate-900 border border-slate-700 text-gray-200 w-[500px] backdrop:bg-black/80"><form action="/update_story_meta" method="post" class="flex flex-col h-full"><div class="p-6 border-b border-slate-800"><h2 class="text-lg font-bold text-indigo-400">Edit Details</h2><input type="hidden" name="current_path" id="metaPathInput"></div><div class="p-6 space-y-4"><div><label class="text-xs font-bold text-gray-500 uppercase">Display Title</label><input type="text" name="title" id="metaTitleInput" class="input-dark mt-1"></div><div><label class="text-xs font-bold text-gray-500 uppercase">Rating</label><select name="rating" id="metaRatingInput" class="input-dark mt-1"><option value="0">Unrated</option><option value="1">1 Star</option><option value="2">2 Stars</option><option value="3">3 Stars</option><option value="4">4 Stars</option><option value="5">5 Stars</option></select></div><div><label class="text-xs font-bold text-gray-500 uppercase">Format</label><select name="format_type" id="metaFormatInput" class="input-dark mt-1"><option value="star_rp">Star RP (*action*)</option><option value="markdown">Markdown (**bold**)</option><option value="novel">Novel Style ("quote")</option></select></div><div><label class="text-xs font-bold text-gray-500 uppercase">Synopsis</label><textarea name="synopsis" id="metaSynopsisInput" rows="3" class="input-dark mt-1"></textarea></div><div><label class="text-xs font-bold text-gray-500 uppercase">Tags</label><input type="text" name="tags" id="metaTagsInput" class="input-dark mt-1"></div><div><label class="text-xs font-bold text-gray-500 uppercase">Campaign</label><select name="campaign" id="metaCampaignInput" class="input-dark mt-1">{% for camp in campaigns %}<option value="{{ camp }}">{{ camp }}</option>{% endfor %}</select></div></div><div class="p-4 border-t border-slate-800 flex justify-end gap-2 bg-slate-900"><button type="button" onclick="this.closest('dialog').close()" class="text-gray-400 text-sm px-3 py-2">Cancel</button><button type="submit" class="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-bold">Save</button></div></form></dialog>
    
    <dialog id="editModal" class="rounded-xl shadow-2xl bg-slate-900 border border-slate-700 text-gray-200 w-[500px] backdrop:bg-black/80 max-h-[90vh]">
        <form action="/update_character_details" method="post" enctype="multipart/form-data" class="flex flex-col h-full">
            <div class="p-6 border-b border-slate-800 bg-slate-900 sticky top-0 z-10">
                <h2 class="text-lg font-bold text-indigo-400">Edit <span id="modalCharNameDisplay"></span></h2>
                <input type="hidden" id="modalCharIdInput" name="char_id" value="">
                <input type="hidden" name="return_file" value="{{ filename | default('') }}">
            </div>
            
            <div class="p-6 overflow-y-auto space-y-4">
                <div class="flex gap-4">
                    <div class="flex-1">
                        <label class="text-xs text-gray-500 uppercase font-bold">Display Name</label>
                        <input type="text" id="modalNameInput" name="name" class="input-dark mt-1">
                    </div>
                    
                    <div>
                        <label class="text-xs text-gray-500 uppercase font-bold">Chat Color</label>
                        <input type="hidden" id="modalBubbleColor" name="bubble_color">
                        <div class="color-grid mt-1" id="colorPaletteContainer">
                            <button type="button" onclick="selectColor('#1e293b')" class="color-btn bg-[#1e293b]"></button>
                            <button type="button" onclick="selectColor('#374151')" class="color-btn bg-[#374151]"></button>
                            <button type="button" onclick="selectColor('#7f1d1d')" class="color-btn bg-[#7f1d1d]"></button>
                            <button type="button" onclick="selectColor('#991b1b')" class="color-btn bg-[#991b1b]"></button>
                            <button type="button" onclick="selectColor('#9a3412')" class="color-btn bg-[#9a3412]"></button>
                            <button type="button" onclick="selectColor('#854d0e')" class="color-btn bg-[#854d0e]"></button>
                            <button type="button" onclick="selectColor('#3f6212')" class="color-btn bg-[#3f6212]"></button>
                            <button type="button" onclick="selectColor('#166534')" class="color-btn bg-[#166534]"></button>
                            <button type="button" onclick="selectColor('#065f46')" class="color-btn bg-[#065f46]"></button>
                            <button type="button" onclick="selectColor('#115e59')" class="color-btn bg-[#115e59]"></button>
                            <button type="button" onclick="selectColor('#155e75')" class="color-btn bg-[#155e75]"></button>
                            <button type="button" onclick="selectColor('#075985')" class="color-btn bg-[#075985]"></button>
                            <button type="button" onclick="selectColor('#1e40af')" class="color-btn bg-[#1e40af]"></button>
                            <button type="button" onclick="selectColor('#1e3a8a')" class="color-btn bg-[#1e3a8a]"></button>
                            <button type="button" onclick="selectColor('#3730a3')" class="color-btn bg-[#3730a3]"></button>
                            <button type="button" onclick="selectColor('#5b21b6')" class="color-btn bg-[#5b21b6]"></button>
                            <button type="button" onclick="selectColor('#6b21a8')" class="color-btn bg-[#6b21a8]"></button>
                            <button type="button" onclick="selectColor('#86198f')" class="color-btn bg-[#86198f]"></button>
                            <button type="button" onclick="selectColor('#9d174d')" class="color-btn bg-[#9d174d]"></button>
                            <button type="button" onclick="selectColor('#9f1239')" class="color-btn bg-[#9f1239]"></button>
                            <button type="button" onclick="selectColor('#881337')" class="color-btn bg-[#881337]"></button>
                            <button type="button" onclick="selectColor('#4c0519')" class="color-btn bg-[#4c0519]"></button>
                            <button type="button" onclick="selectColor('#000000')" class="color-btn bg-[#000000]"></button>
                            <button type="button" onclick="selectColor('#ffffff')" class="color-btn bg-[#ffffff]"></button>
                        </div>
                    </div>
                </div>
                
                <div><label class="text-xs text-gray-500 uppercase font-bold">Avatar</label><input type="file" name="avatar" accept="image/*" class="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-indigo-900 file:text-indigo-300 hover:file:bg-indigo-800 cursor-pointer mt-2 bg-slate-950 rounded border border-slate-700 p-1"/></div>
                <div><label class="text-xs text-gray-500 uppercase font-bold">Bio</label><textarea name="description" id="modalDescription" rows="3" class="input-dark mt-1"></textarea></div>
                <div class="p-3 bg-slate-950 rounded border border-slate-800">
                    <label class="text-xs text-gray-500 uppercase font-bold block mb-2">Core Stats</label>
                    <div class="grid grid-cols-2 gap-2">
                        <input type="text" name="attr_keys" value="Age" class="hidden"><input type="text" id="modalAge" name="attr_values" placeholder="Age" class="input-dark text-xs">
                        <input type="text" name="attr_keys" value="Gender" class="hidden"><input type="text" id="modalGender" name="attr_values" placeholder="Gender" class="input-dark text-xs">
                        <input type="text" name="attr_keys" value="Race" class="hidden"><input type="text" id="modalRace" name="attr_values" placeholder="Race" class="input-dark text-xs">
                        <input type="text" name="attr_keys" value="Orientation" class="hidden"><input type="text" id="modalOrient" name="attr_values" placeholder="Orientation" class="input-dark text-xs">
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
    
    <dialog id="importStoryModal" class="rounded-xl bg-slate-900 border border-slate-700 text-gray-200 w-[500px] backdrop:bg-black/80">
        <div class="p-6"><h2 class="text-lg font-bold text-indigo-400 mb-4">Add New Story</h2>
        <div class="flex gap-2 mb-4 border-b border-slate-700 pb-2">
            <button onclick="showImportTab('file')" id="tab-file" class="px-3 py-1 text-sm font-bold text-white border-b-2 border-indigo-500 transition">Upload File</button>
            <button onclick="showImportTab('text')" id="tab-text" class="px-3 py-1 text-sm text-gray-400 hover:text-white transition">Write / Paste</button>
        </div>
        <form id="form-file" action="/import_story_file" method="post" enctype="multipart/form-data" class="space-y-4">
            <div>
                <label class="text-xs font-bold text-gray-500 uppercase">Select File (.txt, .json)</label>
                <input type="file" name="file" accept=".txt,.json" class="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-indigo-900 file:text-indigo-300 hover:file:bg-indigo-800 cursor-pointer mt-2 bg-slate-950 rounded border border-slate-700 p-1"/>
            </div>
            <div>
                <label class="text-xs font-bold text-gray-500 uppercase">Campaign</label>
                <select name="campaign" class="input-dark mt-1"><option value="Unsorted">Unsorted</option>{% for camp in campaigns %}{% if camp != "Unsorted" %}<option value="{{ camp }}">{{ camp }}</option>{% endif %}{% endfor %}</select>
            </div>
            <div class="flex justify-end gap-2 pt-2">
                <button type="button" onclick="this.closest('dialog').close()" class="text-gray-400 text-sm px-3 py-2">Cancel</button>
                <button type="submit" class="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-bold">Upload</button>
            </div>
        </form>
        <form id="form-text" action="/import_story_text" method="post" class="space-y-4 hidden">
            <div><label class="text-xs font-bold text-gray-500 uppercase">Story Title</label><input type="text" name="title" class="input-dark mt-1" placeholder="e.g. The Tavern Brawl" required></div>
            <div><label class="text-xs font-bold text-gray-500 uppercase">Content</label><textarea name="content" rows="10" class="input-dark mt-1 font-mono text-xs" placeholder="Paste your log here..." required></textarea></div>
            <div><label class="text-xs font-bold text-gray-500 uppercase">Campaign</label><select name="campaign" class="input-dark mt-1"><option value="Unsorted">Unsorted</option>{% for camp in campaigns %}{% if camp != "Unsorted" %}<option value="{{ camp }}">{{ camp }}</option>{% endif %}{% endfor %}</select></div><div class="flex justify-end gap-2 pt-2"><button type="button" onclick="this.closest('dialog').close()" class="text-gray-400 text-sm px-3 py-2">Cancel</button><button type="submit" class="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-bold">Save Story</button></div></form></div></dialog>

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
            // Set Rating
            document.getElementById('metaRatingInput').value = item.meta.rating || 0;
            // Set Format
            document.getElementById('metaFormatInput').value = item.meta.format_type || 'star_rp';
            
            const parts = item.path.split('/');
            const currentCamp = parts.length > 1 ? parts[0] : "Unsorted";
            document.getElementById('metaCampaignInput').value = currentCamp;
            document.getElementById('storyMetaModal').showModal();
        }
        
        // --- CUSTOM COLOR GRID LOGIC ---
        function selectColor(color) {
            document.getElementById('modalBubbleColor').value = color;
            // Remove selected state from all
            document.querySelectorAll('.color-btn').forEach(btn => {
                btn.classList.remove('selected');
                btn.style.borderColor = "rgba(255,255,255,0.1)";
            });
            // Add selected state to clicked button
            const buttons = document.querySelectorAll('.color-btn');
            for (let btn of buttons) {
                if(btn.getAttribute('onclick').includes(color)) {
                    btn.classList.add('selected');
                    btn.style.borderColor = "white";
                }
            }
        }

        function openEditModal(charData) {
            const name = charData.display_name || charData.name || "Unknown";
            document.getElementById('modalCharNameDisplay').innerText = name;
            document.getElementById('modalNameInput').value = name;
            document.getElementById('modalCharIdInput').value = charData.id;
            document.getElementById('modalDescription').value = charData.description || '';
            
            // Set Color
            const bubbleColor = charData.bubble_color || '#1e293b';
            selectColor(bubbleColor);

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
