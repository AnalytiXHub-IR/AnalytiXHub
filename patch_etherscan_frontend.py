import os
import glob
import sys

# Ensure modules package is accessible
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from modules.fetchers.multi_chain import EtherscanMultiChainFetcher

# We only want to generate strings for the EXACT Etherscan chains current in memory
opts_html = '\n                    <optgroup label="✅ EVM Chains (Etherscan V2 API - Single Endpoint)">\n'

for k, v in EtherscanMultiChainFetcher.CHAIN_CONFIGS.items():
    readable_label = v.get('name', k.title())
    opts_html += f'                        <option value="{k}" {{% if current_chain=="{k}" %}}selected{{% endif %}}>{readable_label}</option>\n'

opts_html += '                    </optgroup>\n'

template_files = glob.glob(os.path.join("templates", "*.html"))

for f in template_files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # We need to find the <optgroup label="✅ EVM Chains (Etherscan V2 API - Single Endpoint)">
    # and replace everything inside it until the closing </optgroup>
    start_tag = '<optgroup label="✅ EVM Chains (Etherscan V2 API - Single Endpoint)">'
    
    # some files might just have ✅ EVM Chains
    # Let's search broadly.
    pos_start = content.find(start_tag)
    if pos_start == -1:
        start_tag = '<optgroup label="✅ EVM Chains'
        pos_start = content.find(start_tag)
        
    if pos_start != -1:
        # Find the next </optgroup>
        pos_end = content.find('</optgroup>', pos_start)
        if pos_end != -1:
            full_end = pos_end + len('</optgroup>')
            # Strip the old string out and replace
            new_content = content[:pos_start] + opts_html.strip() + content[full_end:]
            
            with open(f, 'w', encoding='utf-8') as out:
                out.write(new_content)
            print(f"Patched strictly Etherscan blocks inside {f}")

print("Done patching.")
