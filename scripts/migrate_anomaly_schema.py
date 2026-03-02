import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///forensics.db')
engine = create_engine(DATABASE_URL)

def add_case_id_to_anomaly():
    print("Adding case_id to anomaly_detection...")
    try:
        with engine.begin() as conn:
            # Check if column exists
            try:
                # Try simple ALTER TABLE (works for adding columns in most dialects including SQLite)
                conn.execute(text("ALTER TABLE anomaly_detection ADD COLUMN case_id INTEGER REFERENCES cases(id)"))
                print("Successfully added case_id to anomaly_detection table!")
            except Exception as e:
                if 'duplicate column name' in str(e).lower() or 'already exists' in str(e).lower():
                    print("case_id column already exists in anomaly_detection.")
                else:
                    print(f"Error adding column directly, may need table recreation: {e}")
                    
                    # SQLite fallback: Recreate table if ALTER ADD COLUMN fails due to FK
                    print("Attempting SQLite table recreation...")
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS anomaly_detection_new (
                            id INTEGER NOT NULL PRIMARY KEY,
                            case_id INTEGER,
                            address VARCHAR,
                            chain VARCHAR,
                            anomaly_type VARCHAR,
                            anomaly_score FLOAT,
                            reasons JSON,
                            timestamp DATETIME,
                            is_suspicious BOOLEAN,
                            FOREIGN KEY(case_id) REFERENCES cases (id)
                        )
                    """))
                    
                    conn.execute(text("""
                        INSERT INTO anomaly_detection_new (
                            id, address, chain, anomaly_type, anomaly_score, reasons, timestamp, is_suspicious
                        )
                        SELECT 
                            id, address, chain, anomaly_type, anomaly_score, reasons, timestamp, is_suspicious
                        FROM anomaly_detection
                    """))
                    
                    conn.execute(text("DROP TABLE anomaly_detection"))
                    conn.execute(text("ALTER TABLE anomaly_detection_new RENAME TO anomaly_detection"))
                    
                    conn.execute(text("CREATE INDEX ix_anomaly_detection_case_id ON anomaly_detection (case_id)"))
                    conn.execute(text("CREATE INDEX ix_anomaly_detection_id ON anomaly_detection (id)"))
                    conn.execute(text("CREATE INDEX ix_anomaly_detection_address ON anomaly_detection (address)"))
                    print("Successfully recreated anomaly_detection table with case_id!")
                    
    except Exception as e:
        print(f"Critical error: {e}")

if __name__ == "__main__":
    add_case_id_to_anomaly()
