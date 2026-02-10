"""
PostgreSQL Setup Script for OPENCHAIN IR
Initializes database, tables, and indexes
Run once after PostgreSQL installation
"""

import os
import sys
import subprocess
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from db_models import Base, DATABASE_URL

load_dotenv()

def setup_postgres():
    """Setup PostgreSQL database and tables"""
    
    print("=" * 60)
    print("🔧 OPENCHAIN IR - PostgreSQL Setup")
    print("=" * 60)
    
    # Step 1: Create connection
    print("\n[1/4] Creating database connection...")
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        print("✓ Database URL:", DATABASE_URL)
    except Exception as e:
        print("✗ Error:", str(e))
        return False
    
    # Step 2: Test connection
    print("\n[2/4] Testing PostgreSQL connection...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✓ PostgreSQL connected: {version[:50]}...")
    except Exception as e:
        print(f"✗ Connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Is PostgreSQL running? (Windows: Start service)")
        print("  2. Check DATABASE_URL in .env or code")
        print("  3. Windows CMD: net start postgresql-x64-15")
        return False
    
    # Step 3: Create tables
    print("\n[3/4] Creating tables...")
    try:
        Base.metadata.create_all(engine)
        print("✓ All tables created successfully")
    except Exception as e:
        print(f"✗ Error creating tables: {str(e)}")
        return False
    
    # Step 4: Create indexes
    print("\n[4/4] Creating indexes for performance...")
    try:
        with engine.connect() as conn:
            # Address indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_addresses_case ON addresses(case_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_addresses_chain ON addresses(chain_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_addresses_address ON addresses(address)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_addresses_risk ON addresses(risk_score)"))
            
            # Transaction indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_transactions_case ON transactions(case_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_transactions_from ON transactions(from_address)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_transactions_to ON transactions(to_address)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp)"))
            
            # Cluster indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clusters_case ON address_clusters(case_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clusters_member ON address_clusters(member_addresses)"))
            
            # Alert indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alerts_case ON alerts(case_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(created_at)"))
            
            conn.commit()
            print("✓ Indexes created successfully")
    except Exception as e:
        print(f"⚠ Warning creating indexes: {str(e)}")
    
    # Step 5: Display summary
    print("\n" + "=" * 60)
    print("✅ PostgreSQL Setup Complete!")
    print("=" * 60)
    print("\nDatabase Info:")
    print(f"  • Database: openchain_ir")
    print(f"  • Host: localhost:5432")
    print(f"  • Tables created: Cases, Addresses, Transactions, Chains,")
    print(f"                    AddressClusters, SmartContracts, DeFiActivity, Alerts")
    print("\nNext steps:")
    print("  1. Install requirements: pip install -r requirements.txt")
    print("  2. Start Redis: redis-server (or docker run -d -p 6379:6379 redis:latest)")
    print("  3. Start app: python app.py")
    print("\n")
    
    return True

if __name__ == "__main__":
    success = setup_postgres()
    sys.exit(0 if success else 1)
