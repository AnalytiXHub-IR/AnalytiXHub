"""
Database Models for OPENCHAIN IR v3.0
PostgreSQL-backed multi-chain forensic analysis
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/openchain_ir')

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== DATABASE MODELS ====================

class Case(Base):
    """Forensic investigation case"""
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, unique=True, index=True)
    case_name = Column(String)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String, default='active')  # active, closed, archived
    
    # Case metadata
    investigator = Column(String)
    jurisdiction = Column(String)
    case_type = Column(String)  # fraud, theft, money_laundering, etc.
    
    # Relationships
    addresses = relationship("Address", back_populates="case", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="case", cascade="all, delete-orphan")
    clusters = relationship("AddressCluster", back_populates="case", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="case", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'case_id': self.case_id,
            'case_name': self.case_name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'status': self.status,
        }


class Chain(Base):
    """Supported blockchain networks"""
    __tablename__ = "chains"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # ethereum, bitcoin, litecoin, dogecoin, xrp
    symbol = Column(String)  # ETH, BTC, LTC, DOGE, XRP
    full_name = Column(String)  # Ethereum Mainnet, Bitcoin Mainnet, etc.
    api_type = Column(String)  # etherscan, blockchain_com, xrpl, custom
    rpc_url = Column(String)
    explorer_url = Column(String)
    decimals = Column(Integer, default=18)
    is_active = Column(Boolean, default=True)
    
    addresses = relationship("Address", back_populates="chain")
    transactions = relationship("Transaction", back_populates="chain")


class Address(Base):
    """Blockchain addresses under investigation"""
    __tablename__ = "addresses"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    chain_id = Column(Integer, ForeignKey("chains.id"), index=True)
    
    address = Column(String, index=True)
    alias = Column(String)  # Human-readable name
    address_type = Column(String)  # suspect, victim, mixer, exchange, unknown
    label = Column(String)  # Known entity label (if identified)
    
    # Analysis data
    balance = Column(Float, default=0)
    total_in = Column(Float, default=0)
    total_out = Column(Float, default=0)
    tx_count = Column(Integer, default=0)
    first_tx_time = Column(DateTime)
    last_tx_time = Column(DateTime)
    
    # Risk assessment
    risk_score = Column(Float, default=0)
    risk_factors = Column(JSON, default={})
    is_suspicious = Column(Boolean, default=False)
    threat_intel_flag = Column(Boolean, default=False)
    threat_sources = Column(JSON, default=[])  # [chainalysis, ofac, scamalert, etc.]
    
    # Relationships
    case = relationship("Case", back_populates="addresses")
    chain = relationship("Chain", back_populates="addresses")
    transactions = relationship("Transaction", back_populates="address")
    cluster = relationship("AddressCluster", back_populates="addresses")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_analyzed = Column(DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'address': self.address,
            'alias': self.alias,
            'type': self.address_type,
            'label': self.label,
            'balance': self.balance,
            'risk_score': self.risk_score,
            'is_suspicious': self.is_suspicious,
            'threat_flagged': self.threat_intel_flag,
        }


class Transaction(Base):
    """Blockchain transactions"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    chain_id = Column(Integer, ForeignKey("chains.id"), index=True)
    
    tx_hash = Column(String, unique=True, index=True)
    from_address_id = Column(Integer, ForeignKey("addresses.id"))
    to_address_id = Column(Integer, ForeignKey("addresses.id"))
    
    from_address = Column(String, index=True)
    to_address = Column(String, index=True)
    
    amount = Column(Float)
    fee = Column(Float, default=0)
    timestamp = Column(DateTime, index=True)
    block_number = Column(Integer)
    
    # Token transfer data (for ERC-20, etc.)
    is_token_transfer = Column(Boolean, default=False)
    token_symbol = Column(String)
    token_name = Column(String)
    token_address = Column(String)
    
    # Analysis
    tx_type = Column(String)  # normal, internal, token_transfer, contract_interaction
    is_suspicious = Column(Boolean, default=False)
    anomaly_score = Column(Float, default=0)
    anomaly_reasons = Column(JSON, default=[])
    
    # Relationships
    case = relationship("Case", back_populates="transactions")
    chain = relationship("Chain", back_populates="transactions")
    address = relationship("Address", back_populates="transactions")
    
    def to_dict(self):
        return {
            'hash': self.tx_hash,
            'from': self.from_address,
            'to': self.to_address,
            'amount': self.amount,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'is_suspicious': self.is_suspicious,
            'anomaly_score': self.anomaly_score,
        }


class AddressCluster(Base):
    """Related addresses (cross-address clustering)"""
    __tablename__ = "address_clusters"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    
    cluster_id = Column(String, unique=True, index=True)
    cluster_type = Column(String)  # same_entity, mixer_output, exchange_dust, etc.
    confidence_score = Column(Float)  # 0-1 confidence this is related
    
    addresses = relationship("Address", back_populates="cluster")
    case = relationship("Case", back_populates="clusters")
    
    extra_metadata = Column(JSON, default={})  # Evidence of relationship
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    """Security alerts for monitored addresses"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    
    alert_type = Column(String)  # new_transaction, risk_threshold, new_counterparty, etc.
    severity = Column(String)  # critical, high, medium, low
    
    address = Column(String, index=True)
    description = Column(Text)
    
    is_acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Related data
    related_tx_hash = Column(String)
    related_address = Column(String)
    extra_metadata = Column(JSON, default={})
    
    case = relationship("Case", back_populates="alerts")


class ThreatIntel(Base):
    """Threat intelligence data (sanctions lists, scam databases, etc.)"""
    __tablename__ = "threat_intel"
    
    id = Column(Integer, primary_key=True, index=True)
    
    address = Column(String, unique=True, index=True)
    chain = Column(String)  # ethereum, bitcoin, etc.
    
    threat_type = Column(String)  # sanctioned, scammer, mixer, ransomware, etc.
    source = Column(String)  # chainalysis, ofac, scamalert, etherscan_phishing
    
    entity_name = Column(String)
    entity_type = Column(String)  # individual, organization, mixer, etc.
    
    description = Column(Text)
    confidence = Column(Float)  # 0-1
    
    first_seen = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    extra_metadata = Column(JSON, default={})


class AnomalyDetection(Base):
    """ML-based anomaly detection results"""
    __tablename__ = "anomaly_detection"
    
    id = Column(Integer, primary_key=True, index=True)
    
    address = Column(String, index=True)
    chain = Column(String)
    
    anomaly_type = Column(String)  # unusual_amount, frequency_spike, new_counterparty, behavioral_change
    anomaly_score = Column(Float)  # 0-1, 1 = highest anomaly
    
    baseline_metric = Column(String)  # What was the baseline?
    current_value = Column(Float)
    baseline_value = Column(Float)
    deviation_percent = Column(Float)  # % deviation from baseline
    
    confidence = Column(Float)  # Model confidence in detection
    
    detected_at = Column(DateTime, default=datetime.utcnow)
    extra_metadata = Column(JSON, default={})


# ==================== DATABASE INITIALIZATION ====================

def init_db():
    """Initialize database and create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")
    
    # Populate initial chains
    from sqlalchemy.orm import Session
    db = Session(bind=engine)
    
    chains = [
        Chain(name='ethereum', symbol='ETH', full_name='Ethereum Mainnet', 
              api_type='etherscan', explorer_url='https://etherscan.io', decimals=18),
        Chain(name='bitcoin', symbol='BTC', full_name='Bitcoin Mainnet', 
              api_type='blockchain_com', explorer_url='https://blockchain.com', decimals=8),
        Chain(name='litecoin', symbol='LTC', full_name='Litecoin Mainnet', 
              api_type='blockchain_com', explorer_url='https://blockchair.com/litecoin', decimals=8),
        Chain(name='dogecoin', symbol='DOGE', full_name='Dogecoin Mainnet', 
              api_type='blockchain_com', explorer_url='https://blockchair.com/dogecoin', decimals=8),
        Chain(name='xrp', symbol='XRP', full_name='XRP Ledger', 
              api_type='xrpl', explorer_url='https://xrpscan.com', decimals=6),
    ]
    
    for chain in chains:
        if not db.query(Chain).filter(Chain.name == chain.name).first():
            db.add(chain)
    
    db.commit()
    db.close()
    print("✅ Chains initialized")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SmartContract(Base):
    """Smart contract analysis and metadata"""
    __tablename__ = "smart_contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    chain_id = Column(Integer, ForeignKey("chains.id"), index=True)
    
    contract_address = Column(String, unique=True, index=True)
    name = Column(String)
    symbol = Column(String)
    decimals = Column(Integer)
    
    source_code = Column(Text)
    abi = Column(JSON)
    
    # Security analysis
    is_verified = Column(Boolean, default=False)
    is_honeypot = Column(Boolean, default=False)
    is_rug_pull = Column(Boolean, default=False)
    vulnerability_score = Column(Float, default=0)  # 0-1
    vulnerabilities = Column(JSON, default=[])  # List of found vulnerabilities
    
    # Metadata
    deployment_tx = Column(String)
    deployment_block = Column(Integer)
    deployed_at = Column(DateTime)
    
    creator_address = Column(String)
    
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    extra_metadata = Column(JSON, default={})
    
    case = relationship("Case", back_populates="contracts")
    chain = relationship("Chain", back_populates="contracts")


class DeFiActivity(Base):
    """DeFi and DEX activity tracking"""
    __tablename__ = "defi_activity"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    
    address = Column(String, index=True)
    chain = Column(String)
    
    activity_type = Column(String)  # swap, liquidity_add, liquidity_remove, yield_farming, borrowing, lending
    protocol = Column(String)  # uniswap, aave, curve, compound, etc.
    
    tx_hash = Column(String, unique=True, index=True)
    timestamp = Column(DateTime, index=True)
    
    # Activity details
    token_in = Column(String)
    amount_in = Column(Float)
    token_out = Column(String)
    amount_out = Column(Float)
    
    pool_address = Column(String)
    lp_position_id = Column(String)  # For Uniswap V3, etc.
    
    # Metrics
    slippage_percent = Column(Float)
    gas_paid = Column(Float)
    usd_value = Column(Float)
    
    extra_metadata = Column(JSON, default={})
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    case = relationship("Case", back_populates="defi_activities")


class TaintTrace(Base):
    """Fund flow and taint analysis tracking"""
    __tablename__ = "taint_traces"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    
    source_address = Column(String, index=True)
    destination_address = Column(String, index=True)
    
    # Path details
    tx_hashes = Column(JSON)  # Array of tx hashes in path
    addresses_in_path = Column(JSON)  # All addresses from source to dest
    
    amount_start = Column(Float)
    amount_end = Column(Float)
    amount_lost = Column(Float)  # Due to mixing, fees, swaps
    
    trace_depth = Column(Integer)  # Number of hops
    
    # Taint info
    taint_type = Column(String)  # direct, mixer, bridge, dex_swap, cex_deposit
    confidence = Column(Float)  # 0-1 confidence this is related
    
    # Timestamps
    trace_start_time = Column(DateTime)
    trace_end_time = Column(DateTime)
    duration_hours = Column(Float)
    
    analysis_metadata = Column(JSON, default={})
    traced_at = Column(DateTime, default=datetime.utcnow)
    
    case = relationship("Case", back_populates="taint_traces")


class MonitoringJob(Base):
    """Real-time monitoring jobs for addresses"""
    __tablename__ = "monitoring_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    
    address = Column(String, index=True)
    chain = Column(String)
    
    status = Column(String)  # active, paused, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime)
    
    # Configuration
    check_interval_minutes = Column(Integer, default=5)
    alert_on_new_tx = Column(Boolean, default=True)
    alert_on_anomaly = Column(Boolean, default=True)
    alert_on_counterparty_change = Column(Boolean, default=False)
    
    # Stats
    tx_count_last_check = Column(Integer, default=0)
    total_alerts_generated = Column(Integer, default=0)
    
    extra_metadata = Column(JSON, default={})
    case = relationship("Case", back_populates="monitoring_jobs")


class BatchJob(Base):
    """Batch processing jobs"""
    __tablename__ = "batch_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), index=True)
    
    job_id = Column(String, unique=True, index=True)  # Celery job ID
    status = Column(String)  # pending, processing, completed, failed
    
    address_count = Column(Integer)
    addresses = Column(JSON)  # List of addresses in batch
    
    progress_percent = Column(Float, default=0)
    completed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Results
    results_summary = Column(JSON, default={})
    error_log = Column(Text)
    
    extra_metadata = Column(JSON, default={})
    case = relationship("Case", back_populates="batch_jobs")


# Add relationships to Case model
Case.addresses = relationship("Address", back_populates="case", cascade="all, delete-orphan")
Case.transactions = relationship("Transaction", back_populates="case", cascade="all, delete-orphan")
Case.clusters = relationship("AddressCluster", back_populates="case", cascade="all, delete-orphan")
Case.alerts = relationship("Alert", back_populates="case", cascade="all, delete-orphan")
Case.contracts = relationship("SmartContract", back_populates="case", cascade="all, delete-orphan")
Case.defi_activities = relationship("DeFiActivity", back_populates="case", cascade="all, delete-orphan")
Case.taint_traces = relationship("TaintTrace", back_populates="case", cascade="all, delete-orphan")
Case.monitoring_jobs = relationship("MonitoringJob", back_populates="case", cascade="all, delete-orphan")
Case.batch_jobs = relationship("BatchJob", back_populates="case", cascade="all, delete-orphan")

Chain.contracts = relationship("SmartContract", back_populates="chain")
Chain.defi = relationship("DeFiActivity", foreign_keys='DeFiActivity.chain_id')


if __name__ == '__main__':
    init_db()
