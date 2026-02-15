
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import re

class DogechainInfoScraper:
    """
    Scrapes transaction history from Dogechain.info (Public Explorer).
    Uses HTML parsing to get around API limits.
    """
    
    BASE_URL = "https://dogechain.info/address"
    
    @staticmethod
    def fetch_transactions(address: str) -> tuple[list[dict], dict]:
        transactions = []
        counts = {'normal': 0}
        
        try:
            print(f"[+] Scraping Dogechain.info for {address[:8]}...")
            
            # 1. First request to get total pages/txs
            url = f"{DogechainInfoScraper.BASE_URL}/{address}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Scrape ALL pages
            # But let's start with page 1
            # We can detect number of pages from pagination links
            
            # Limit to 10 pages (~500 txs) initially for speed, or loop until done
            MAX_PAGES = 20 
            
            for page in range(1, MAX_PAGES + 1):
                page_url = f"{url}?page={page}" if page > 1 else url
                print(f"    Scanning page {page}...")
                
                try:
                    resp = requests.get(page_url, headers=headers, timeout=15)
                    if resp.status_code != 200:
                        break
                        
                    soup = BeautifulSoup(resp.content, 'html.parser')
                    
                    # Find transaction table
                    # Usually it's a table with class 'table' or similar
                    # Look for 'Transactions' header
                    
                    # Dogechain.info structure (based on general knowledge of explorer):
                    # Table rows <tr> containing txid, block, time, amount...
                    
                    tx_table = soup.find('table', {'id': 'transactions'}) # Hypothetical ID, need to verify
                    if not tx_table:
                        # Fallback to finding any table
                        tables = soup.find_all('table')
                        for t in tables:
                            if 'Hash' in t.text and 'Amount' in t.text:
                                tx_table = t
                                break
                    
                    if not tx_table:
                        print("    No transaction table found.")
                        break
                        
                    rows = tx_table.find_all('tr')[1:] # Skip header
                    if not rows:
                        break
                        
                    found_new = False
                    
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) < 4: continue
                        
                        # Parse columns (Heuristic)
                        # Hash is usually a link
                        hash_link = row.find('a', href=re.compile(r'/tx/'))
                        if not hash_link: continue
                        
                        tx_hash = hash_link.text.strip()
                        
                        # Amount (usually right aligned or green/red)
                        # Check for input/output
                        # Dogechain.info shows In/Out in separate columns or colored amount
                        
                        # Let's try to parse text content
                        row_text = row.text.strip()
                        
                        # Time?
                        # Usually "2024-05-20 12:00:00"
                        time_str = "Unknown"
                        try:
                            # Try finding time pattern
                            match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', row_text)
                            if match:
                                time_str = match.group(0)
                        except:
                            pass
                            
                        # Value?
                        val = 0.0
                        try:
                            # Look for numeric with + or -
                            # Or just parse the amount column
                            # Let's assume last column is balance, second to last is amount
                            amt_text = cols[-2].text.strip().replace(' DOGE', '').replace(',', '')
                            val = float(amt_text)
                        except:
                            val = 0.0
                        
                        # Flow
                        flow = 'in' if val > 0 else 'out' # This might be wrong if scraper parses abs value
                        # Check color? class='text-success' vs 'text-danger'
                        if 'text-danger' in str(row):
                            flow = 'out'
                        elif 'text-success' in str(row):
                            flow = 'in'
                            
                        # Sender/Receiver
                        # This is hard to get from summary table efficiently
                        # Use generic "Incoming"/"Outgoing" or address
                        
                        transactions.append({
                            'hash': tx_hash,
                            'timestamp': time_str,
                            'value': abs(val),
                            'from': address if flow == 'out' else 'Incoming',
                            'to': 'Outgoing' if flow == 'out' else address,
                            'chain': 'dogecoin',
                            'type': 'doge'
                        })
                        found_new = True
                        
                    counts['normal'] = len(transactions)
                    
                    if not found_new:
                        break
                        
                    # Check for "Next" button disabled?
                    # or active page check
                    
                    time.sleep(0.5) # Be nice
                    
                except Exception as e:
                    print(f"    Error scraping page {page}: {e}")
                    break
                    
            print(f"✅ Dogechain.info (Scraper): {len(transactions)} transactions")
            return transactions, counts
            
        except Exception as e:
            print(f"❌ Dogechain scraper error: {e}")
            return [], counts
