import re
import os

def sync_dropdowns():
    master_file = os.path.join('templates', 'investigation.html')
    # Map target file to the exact <select> marker to find
    targets = {
        'investigator.html': 'id="targetChain"',
        'pathfinder.html': 'name="chain"',
        'tracing.html': 'id="chainSelect"',
        'monitoring.html': 'name="chain"'
    }

    with open(master_file, 'r', encoding='utf-8') as f:
        master_content = f.read()

    # Get everything INSIDE the <select ...>...</select> in investigation.html
    # We want to extract just the options/optgroups so we can paste them inside the styling of the other pages
    match = re.search(r'<select[^>]*name="chain"[^>]*>(.*?)</select>', master_content, re.DOTALL)
    if not match:
        print("Could not find master content!")
        return

    inner_options = match.group(1)

    for target_name, marker in targets.items():
        t_path = os.path.join('templates', target_name)
        if not os.path.exists(t_path):
            continue
            
        with open(t_path, 'r', encoding='utf-8') as f:
            t_content = f.read()
            
        # Find the select block containing the marker
        pattern = r'(<select[^>]*' + re.escape(marker) + r'[^>]*>)(.*?)(</select>)'
        
        t_match = re.search(pattern, t_content, re.DOTALL)
        if t_match:
            open_tag = t_match.group(1)
            close_tag = t_match.group(3)
            
            # Reconstruct the string with the new inner options
            new_content = t_content[:t_match.start()] + open_tag + inner_options + close_tag + t_content[t_match.end():]
            with open(t_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Synced {target_name}")
        else:
            print(f"❌ Could not match regex in {target_name}")

if __name__ == '__main__':
    sync_dropdowns()
