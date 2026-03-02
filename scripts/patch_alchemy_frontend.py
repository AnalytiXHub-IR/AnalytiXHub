import os
import glob
from modules.fetchers.multi_chain import AlchemyEVMFetcher

# We only want strings that we just added (the new extended ones)
# Let's dynamically create the <option> blocks from ALCHEMY_URLS
opts_html = '\n                    <optgroup label="🔋 Alchemy EVM (Expanded Networks)">\n'

new_keys = [
    'worldchain', 'worldchain_sepolia', 'shape', 'shape_sepolia', 'arbitrum_nova', 
    'astar', 'zetachain', 'zetachain_testnet', 'berachain', 'berachain_bepolia', 
    'zora', 'zora_sepolia', 'robinhood_testnet', 'ronin', 'ronin_saigon', 'plasma', 
    'plasma_testnet', 'mythos', 'settlus', 'settlus_sepolia', 'megaeth', 'megaeth_testnet', 
    'citrea', 'citrea_testnet', 'tea_sepolia', 'gensyn_testnet', 'arc_testnet', 'story', 
    'story_aeneid', 'clankermon', 'humanity', 'humanity_testnet', 'risa_testnet', 
    'tempo_testnet', 'tempo_moderato', 'hyperliquid', 'hyperliquid_testnet', 'lens', 
    'lens_sepolia', 'worldmobilechain', 'worldmobile_testnet', 'frax', 'frax_sepolia', 
    'ink', 'ink_sepolia', 'celestiabridge', 'celestiabridge_mocha', 'unichain', 
    'unichain_sepolia', 'syndicate', 'superseed', 'superseed_sepolia', 'rise_testnet', 
    'monad', 'monad_testnet', 'flow', 'flow_testnet', 'degen', 'polynomial', 
    'polynomial_sepolia', 'mode', 'mode_sepolia', 'apechain', 'apechain_curtis', 
    'anime', 'anime_sepolia', 'metis', 'sonic', 'sonic_testnet', 'sonic_blaze', 
    'xmtp_ropsten', 'adi', 'adi_testnet', 'abstract', 'abstract_testnet', 'crossfi', 
    'crossfi_testnet', 'soneium', 'soneium_minato', 'stable', 'stable_testnet'
]

for k in new_keys:
    if k in AlchemyEVMFetcher.ALCHEMY_URLS:
        readable_label = k.replace('_', ' ').title() + " (Alchemy)"
        opts_html += f'                        <option value="{k}" {{% if current_chain=="{k}" %}}selected{{% endif %}}>{readable_label}</option>\n'

opts_html += '                    </optgroup>\n'

template_files = glob.glob(os.path.join("templates", "*.html"))
for f in template_files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        
    if "Alchemy EVM (Expanded Networks)" not in content and 'name="chain"' in content:
        # Some files might have multiple </select>. We only target the FIRST one that is for 'chain'.
        # The easiest approach is to replace "</select>" with the expanded group.
        # However, some forms might have other selects.
        # We will split on "</select>", string-match the preceding block for 'name="chain"', 
        # and insert it.
        parts = content.split('</select>')
        for i in range(len(parts) - 1):
            if 'name="chain"' in parts[i]:
                parts[i] += opts_html
        
        new_content = '</select>'.join(parts)
        with open(f, 'w', encoding='utf-8') as out:
            out.write(new_content)
        print(f"Patched {f}")
print("Done patching.")
