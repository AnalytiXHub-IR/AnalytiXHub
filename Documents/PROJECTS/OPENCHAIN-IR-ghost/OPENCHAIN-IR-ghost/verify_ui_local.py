from playwright.sync_api import sync_playwright
import time
import os

BASE_URL = "http://127.0.0.1:5000"
SCREENSHOT_DIR = "test_artifacts"

if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

def verify_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"[*] Navigating to {BASE_URL}...")
        try:
            page.goto(BASE_URL)
            page.screenshot(path=f"{SCREENSHOT_DIR}/01_homepage.png")
            print("    [PASS] Homepage loaded & screenshot saved.")
        except Exception as e:
            print(f"    [FAIL] Could not load homepage: {e}")
            return

        # Create Case
        print("[*] Creating Test Case...")
        try:
            page.click("text=Create New Case")
            page.fill("input[name='case_id']", "UI_TEST_CASE") # Assuming ID is auto-generated or field name matches
            # Let's check the form structure from previous knowledge or just try generic selectors
            # Actually, standard "Create New Case" modal usually has inputs.
            # I'll try to be robust.
            
            # Wait for modal?
            time.sleep(1)
            
            # If standard form:
            if page.is_visible("input[name='case_name']"):
                page.fill("input[name='case_name']", "Browser UI Test")
                page.fill("textarea[name='description']", "Automated UI verification")
                page.fill("input[name='investigator']", "Playwright Bot")
                page.click("button[type='submit']") 
                # Or "Create Case" button
                
                time.sleep(2)
                page.screenshot(path=f"{SCREENSHOT_DIR}/02_dashboard.png")
                print("    [PASS] Case created & screenshot saved.")
            else:
                print("    [WARN] specific inputs not found, taking screenshot of modal.")
                page.screenshot(path=f"{SCREENSHOT_DIR}/02_modal.png")
                
        except Exception as e:
            print(f"    [FAIL] Case creation failed: {e}")

        # Analyze Address
        print("[*] Analyzing Address...")
        try:
            # Go to dashboard of the case we just created? Or just use the main page if it redirects?
            # Assuming redirection to case dashboard or list.
            # Let's go to specific case dashboard if possible, or index.
            # The Index page has "Create Case".
            # Can we analyze from Index? "Analyze Address" form.
            
            page.goto(BASE_URL) # Back to home/dashboard
            
            # Look for Analyze form
            if page.is_visible("input[name='address']"):
                page.fill("input[name='address']", "0x8626f6940e2eb28930df1c8e74e7b6aaf002e33e")
                # Select chain if dropdown exists
                # page.select_option("select[name='chain']", "ethereum") 
                
                page.click("button:has-text('Analyze')")
                
                print("    [INFO] Waiting for analysis (30s timeout)...")
                try:
                    page.wait_for_selector("text=Analysis Complete", timeout=30000) 
                    # Or check for results elements
                except:
                    print("    [INFO] Timeout waiting for explicit 'Complete' text, checking for results...")
                
                time.sleep(5)
                page.screenshot(path=f"{SCREENSHOT_DIR}/03_analysis_results.png")
                print("    [PASS] Analysis attempted & screenshot saved.")
                
        except Exception as e:
            print(f"    [FAIL] Analysis failed: {e}")

        browser.close()

if __name__ == "__main__":
    verify_ui()
