import re
import html
import os

ACTION_STYLE = 'text-indigo-300 italic font-medium'

def format_text_content(text):
    safe_text = html.escape(text)
    return re.sub(
        r'\*([^*]+)\*', 
        f'<span class="{ACTION_STYLE}">*\\1*</span>', 
        safe_text
    )

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
                match = re.match(r"^([A-Za-z0-9_ -]+):\s*(.*)", line)
                if match:
                    name = match.group(1)
                    if name not in stats: stats[name] = 0
                    stats[name] += 1
                    msg_count += 1
        top_chars = sorted(stats.keys(), key=lambda n: stats[n], reverse=True)[:3]
        return {"msg_count": msg_count, "top_characters": top_chars, "date": date_str}
    except:
        return {"msg_count": 0, "top_characters": [], "date": "Unknown"}

def parse_file(filepath):
    blocks = []
    stats = {}
    current_block = None

    try:
        with open(filepath, "r", encoding="utf-8-sig", errors="ignore") as f:
            for line in f:
                raw_line = line.strip()
                if not raw_line: continue

                if raw_line.startswith("((") and raw_line.endswith("))"):
                    if current_block:
                        blocks.append(current_block)
                        current_block = None
                    blocks.append({"type": "ooc", "text": html.escape(raw_line.strip("() "))})
                    continue

                speaker_match = re.match(r"^([A-Za-z0-9_ -]+):\s*(.*)", raw_line)
                if speaker_match:
                    if current_block: blocks.append(current_block)
                    name = speaker_match.group(1)
                    content = speaker_match.group(2)
                    if name not in stats: stats[name] = 0
                    stats[name] += 1
                    current_block = {"type": "dialogue", "speaker": name, "lines": []}
                    if content:
                        is_action = content.startswith("*") and content.endswith("*")
                        current_block["lines"].append({
                            "is_action_line": is_action,
                            "content": format_text_content(content)
                        })
                else:
                    if current_block:
                        is_action = raw_line.startswith("*") and raw_line.endswith("*")
                        current_block["lines"].append({
                            "is_action_line": is_action,
                            "content": format_text_content(raw_line)
                        })
                    else:
                        blocks.append({"type": "narrative", "text": format_text_content(raw_line)})

            if current_block: blocks.append(current_block)

    except Exception as e:
        print(f"Parser Error: {e}")
        return [], {}
        
    return blocks, stats
