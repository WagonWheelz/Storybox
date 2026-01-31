import re
import html
import os
import markdown

ACTION_STYLE = 'text-indigo-300 italic font-medium'

def render_star_rp(text):
    """Legacy format: *actions* are highlighted."""
    safe_text = html.escape(text)
    return re.sub(
        r'\*([^*]+)\*', 
        f'<span class="{ACTION_STYLE}">*\\1*</span>', 
        safe_text
    )

def render_markdown(text):
    """Standard Markdown rendering."""
    return markdown.markdown(text, extensions=['extra', 'nl2br'])

def render_novel(text):
    """Text is plain, but quotes are highlighted."""
    safe_text = html.escape(text)
    return re.sub(
        r'"([^"]+)"', 
        f'<span class="text-white font-serif">"\\1"</span>', 
        safe_text
    )

def extract_speaker(line):
    """
    Attempts to identify a speaker in a line.
    Handles formats:
    - User: Hello
    - [User]: Hello
    - [User -> Other]: Hello
    - [User → Other]: Hello
    """
    # Pattern explanation:
    # ^\[?          : Optional starting bracket
    # ([^:\]→>]+)   : Capture Group 1 (The Name). Captures anything NOT a colon, bracket, or arrow.
    # (?:.*?)       : Non-capturing group for " -> Target" (we ignore the target for now)
    # \]?           : Optional closing bracket
    # :\s* : The colon separator and whitespace
    # (.*)          : Capture Group 2 (The Message)
    
    match = re.match(r"^\[?([^:\]→>]+)(?:[→>].*?)?\]?:\s*(.*)", line)
    
    if match:
        name = match.group(1).strip()
        content = match.group(2)
        return name, content
    return None, None

def get_file_stats(filepath):
    stats = {}
    msg_count = 0
    try:
        mod_time = os.path.getmtime(filepath)
        from datetime import datetime
        date_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d')
        
        with open(filepath, "r", encoding="utf-8-sig", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                
                name, _ = extract_speaker(line)
                if name:
                    if name not in stats: stats[name] = 0
                    stats[name] += 1
                    msg_count += 1
                    
        top_chars = sorted(stats.keys(), key=lambda n: stats[n], reverse=True)[:3]
        return {"msg_count": msg_count, "top_characters": top_chars, "date": date_str}
    except:
        return {"msg_count": 0, "top_characters": [], "date": "Unknown"}

def parse_file(filepath, format_type="star_rp"):
    blocks = []
    stats = {}
    current_block = None

    try:
        with open(filepath, "r", encoding="utf-8-sig", errors="ignore") as f:
            for line in f:
                raw_line = line.strip()
                if not raw_line: continue

                # 1. Handle OOC (( ... ))
                if raw_line.startswith("((") and raw_line.endswith("))"):
                    if current_block:
                        blocks.append(current_block)
                        current_block = None
                    blocks.append({"type": "ooc", "text": html.escape(raw_line.strip("() "))})
                    continue

                # 2. Check for Speaker using new logic
                name, content = extract_speaker(raw_line)
                
                if name:
                    if current_block: blocks.append(current_block)

                    if name not in stats: stats[name] = 0
                    stats[name] += 1
                    
                    current_block = {"type": "dialogue", "speaker": name, "lines": []}
                    
                    # RENDER CONTENT BASED ON FORMAT
                    rendered_content = ""
                    is_action = False

                    if format_type == "markdown":
                        rendered_content = render_markdown(content)
                    elif format_type == "novel":
                        rendered_content = render_novel(content)
                    else:
                        is_action = content.startswith("*") and content.endswith("*")
                        rendered_content = render_star_rp(content)

                    current_block["lines"].append({
                        "is_action_line": is_action,
                        "content": rendered_content
                    })
                else:
                    # Append line to previous block
                    if current_block:
                        is_action = False
                        rendered_content = ""

                        if format_type == "markdown":
                            rendered_content = render_markdown(raw_line)
                        elif format_type == "novel":
                            rendered_content = render_novel(raw_line)
                        else:
                            is_action = raw_line.startswith("*") and raw_line.endswith("*")
                            rendered_content = render_star_rp(raw_line)

                        current_block["lines"].append({
                            "is_action_line": is_action,
                            "content": rendered_content
                        })
                    else:
                        # Narrative block
                        rendered_narrative = ""
                        if format_type == "markdown": rendered_narrative = render_markdown(raw_line)
                        else: rendered_narrative = render_star_rp(raw_line)
                        blocks.append({"type": "narrative", "text": rendered_narrative})

            if current_block: blocks.append(current_block)

    except Exception as e:
        print(f"Parser Error: {e}")
        return [], {}
        
    return blocks, stats
