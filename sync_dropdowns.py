import re
import os

def sync_dropdowns():
    master_file = os.path.join('templates', 'investigation.html')
    targets = [
        'investigator.html',
        'pathfinder.html',
        'tracing.html',
        'monitoring.html'
    ]

    # Read master HTML
    with open(master_file, 'r', encoding='utf-8') as f:
        master_content = f.read()

    # Extract the full <select ... id="chainSelector"> ... </select> block
    # We use a regex that handles newlines
    match = re.search(r'(<select[^>]*id="chainSelector"[^>]*>.*?<\/select>)', master_content, re.DOTALL)
    if not match:
        print("Could not find chainSelector block in investigation.html!")
        return

    master_select_block = match.group(1)
    
    # We want to make sure the target <select> blocks don't explicitly require different IDs, 
    # but based on Bootstrap/Jinja setup they are functionally identical cross-page for "chain".
    for target in targets:
        t_path = os.path.join('templates', target)
        if not os.path.exists(t_path):
            continue
            
        with open(t_path, 'r', encoding='utf-8') as f:
            t_content = f.read()
            
        # Replace the target's block
        t_match = re.search(r'(<select[^>]*id="chainSelector"[^>]*>.*?<\/select>)', t_content, re.DOTALL)
        if t_match:
            new_content = t_content[:t_match.start()] + master_select_block + t_content[t_match.end():]
            with open(t_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Synced drop-down in {target}")
        else:
            print(f"❌ Could not find target chainSelector in {target}")

if __name__ == '__main__':
    sync_dropdowns()
