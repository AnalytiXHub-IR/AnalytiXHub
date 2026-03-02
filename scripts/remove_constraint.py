import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///forensics.db')
engine = create_engine(DATABASE_URL)

def remove_unique_constraint():
    print("Dropping UNIQUE constraint on transactions.tx_hash...")
    try:
        with engine.begin() as conn:
            # For SQLite, the standard way is to recreate the table.
            # 1. Create temporary table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS transactions_new (
                    id INTEGER NOT NULL PRIMARY KEY,
                    case_id INTEGER,
                    chain_id INTEGER,
                    tx_hash VARCHAR,
                    from_address_id INTEGER,
                    to_address_id INTEGER,
                    from_address VARCHAR,
                    to_address VARCHAR,
                    amount FLOAT,
                    fee FLOAT,
                    timestamp DATETIME,
                    block_number INTEGER,
                    is_token_transfer BOOLEAN,
                    token_symbol VARCHAR,
                    token_name VARCHAR,
                    token_address VARCHAR,
                    tx_type VARCHAR,
                    is_suspicious BOOLEAN,
                    anomaly_score FLOAT,
                    anomaly_reasons JSON,
                    is_deleted BOOLEAN DEFAULT 0,
                    FOREIGN KEY(case_id) REFERENCES cases (id),
                    FOREIGN KEY(chain_id) REFERENCES chains (id),
                    FOREIGN KEY(from_address_id) REFERENCES addresses (id),
                    FOREIGN KEY(to_address_id) REFERENCES addresses (id)
                )
            """))
            
            # 2. Copy data
            conn.execute(text("""
                INSERT INTO transactions_new (
                    id, case_id, chain_id, tx_hash, from_address_id, to_address_id,
                    from_address, to_address, amount, fee, timestamp, block_number,
                    is_token_transfer, token_symbol, token_name, token_address,
                    tx_type, is_suspicious, anomaly_score, anomaly_reasons, is_deleted
                )
                SELECT 
                    id, case_id, chain_id, tx_hash, from_address_id, to_address_id,
                    from_address, to_address, amount, fee, timestamp, block_number,
                    is_token_transfer, token_symbol, token_name, token_address,
                    tx_type, is_suspicious, anomaly_score, anomaly_reasons, is_deleted
                FROM transactions
            """))
            
            # 3. Drop old table
            conn.execute(text("DROP TABLE transactions"))
            
            # 4. Rename new table
            conn.execute(text("ALTER TABLE transactions_new RENAME TO transactions"))
            
            # 5. Recreate indexes
            conn.execute(text("CREATE INDEX ix_transactions_case_id ON transactions (case_id)"))
            conn.execute(text("CREATE INDEX ix_transactions_chain_id ON transactions (chain_id)"))
            conn.execute(text("CREATE INDEX ix_transactions_tx_hash ON transactions (tx_hash)"))
            conn.execute(text("CREATE INDEX ix_transactions_from_address ON transactions (from_address)"))
            conn.execute(text("CREATE INDEX ix_transactions_to_address ON transactions (to_address)"))
            conn.execute(text("CREATE INDEX ix_transactions_timestamp ON transactions (timestamp)"))
            
            print("Successfully migrated transactions table!")
    except Exception as e:
        print(f"Error dropping constraint: {e}")

if __name__ == "__main__":
    remove_unique_constraint()
