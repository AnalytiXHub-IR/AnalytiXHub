import os
from sqlalchemy import create_engine, inspect, text
from modules.core.db_models import Base, engine

def upgrade_database():
    print("Starting OPENCHAIN IR v4 Database Upgrades...")
    
    # 1. Create all new tables using SQLAlchemy metadata
    print("\n--- Creating missing tables ---")
    Base.metadata.create_all(engine)
    print("✅ Verified: Evidence, AnalysisReport, AuditLog, CaseTimeline, InvestigationSnapshot")
    
    # 2. Add columns to existing tables safely
    print("\n--- Upgrading existing tables ---")
    inspector = inspect(engine)
    
    with engine.begin() as conn:
        is_sqlite = engine.dialect.name == 'sqlite'
        
        def add_column(table, column, definition):
            columns = [col['name'] for col in inspector.get_columns(table)]
            if column not in columns:
                print(f"Adding column '{column}' to '{table}'...")
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
            else:
                print(f"Column '{column}' already exists in '{table}'.")

        # Upgrade Users Table
        add_column("users", "last_login", "DATETIME" if is_sqlite else "TIMESTAMP")
        add_column("users", "failed_login_attempts", "INTEGER DEFAULT 0")
        add_column("users", "is_locked", "BOOLEAN DEFAULT 0" if is_sqlite else "BOOLEAN DEFAULT FALSE")

        # Upgrade Cases Table
        add_column("cases", "court_reference", "VARCHAR(100)")
        add_column("cases", "evidence_status", "VARCHAR(30)")
        add_column("cases", "confidentiality_level", "VARCHAR(30)")

        # Upgrade Addresses Table
        add_column("addresses", "is_deleted", "BOOLEAN DEFAULT 0" if is_sqlite else "BOOLEAN DEFAULT FALSE")
        
        # Upgrade Transactions Table
        add_column("transactions", "is_deleted", "BOOLEAN DEFAULT 0" if is_sqlite else "BOOLEAN DEFAULT FALSE")

        print("\n✅ Database upgraded successfully!")

if __name__ == "__main__":
    upgrade_database()
