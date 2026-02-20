
import sqlite3
import os

DB_FILE = "forensics.db"

def fix_schema():
    if not os.path.exists(DB_FILE):
        print(f"[ERROR] Database file {DB_FILE} not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. Add cluster_id to addresses
    try:
        print("[INFO] Attempting to add column 'cluster_id' to 'addresses' table...")
        cursor.execute("ALTER TABLE addresses ADD COLUMN cluster_id INTEGER")
        print("[SUCCESS] Added 'cluster_id' to 'addresses'.")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("[INFO] Column 'cluster_id' already exists in 'addresses'.")
        else:
            print(f"[ERROR] Failed to add 'cluster_id': {e}")

    # 2. Add chain_id to defi_activity (just in case, based on previous errors)
    try:
        print("[INFO] Attempting to add column 'chain_id' to 'defi_activity' table...")
        cursor.execute("ALTER TABLE defi_activity ADD COLUMN chain_id INTEGER")
        print("[SUCCESS] Added 'chain_id' to 'defi_activity'.")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("[INFO] Column 'chain_id' already exists in 'defi_activity'.")
        elif "no such table" in str(e):
             print("[WARN] Table 'defi_activity' not found (might not be initialized yet).")
        else:
            print(f"[ERROR] Failed to add 'chain_id': {e}")

    # 3. Create case_notes table if not exists (since we just added the model)
    # We can rely on SQLAlchemy init_db for this usually, but let's be safe or just let app.py do it. 
    # Actually, app.py calls init_db() which uses create_all(), which ONLY creates tables if they don't exist.
    # It does NOT update existing tables. 
    # So we MUST rely on this script or a drop-recreate (data loss) approach.
    # We'll skip creating tables here and urge a restart, but we MUST fix the columns on existing tables.
    
    conn.commit()
    conn.close()
    print("[DONE] Schema fix complete.")

if __name__ == "__main__":
    fix_schema()
