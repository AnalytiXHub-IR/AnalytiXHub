from db_models import SessionLocal, ThreatIntel, Chain, init_db

KNOWN_ENTITIES = {
    # Individuals
    "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045": {"name": "Vitalik Buterin", "type": "Individual", "risk": "LOW"},
    
    # Exchanges
    "0x28C6c06298d514Db089934071355E5743bf21d60": {"name": "Binance Hot Wallet", "type": "Exchange", "risk": "LOW"},
    "0x77696bb39917C91A0c3908D577d5e322095425cA": {"name": "Coinbase Hot Wallet", "type": "Exchange", "risk": "LOW"},
    "0x1111111111111111111111111111111111111111": {"name": "Kraken Exchange", "type": "Exchange", "risk": "LOW"},
    
    # Ransomware - WannaCry
    "0x8626f6940e2eb28930df1c8e74e7b6aaf002e33e": {"name": "WannaCry Ransomware Payments", "type": "Ransomware", "risk": "CRITICAL"},
    "0x394cff924caf8598b022503b023d87b96f5bd8e5": {"name": "WannaCry Bitcoin Tumbler", "type": "Ransomware", "risk": "CRITICAL"},
    "0xa4EDE3b20d41db0f0f01c5aE2cBc7f54Dc22e94f": {"name": "WannaCry Victims' Refund Address", "type": "Ransomware", "risk": "CRITICAL"},
    
    # Mixing/Tumbling Services
    "0x12D66f87A04A9E220743712cE6d9bB1B5616B8Fc": {"name": "Tornado Cash Router", "type": "Mixer", "risk": "CRITICAL"},
    "0xd4b88df4d29f5cdf15910dcb5bef341d57227f59": {"name": "Coin Join Service", "type": "Mixer", "risk": "HIGH"},
    
    # Bridges
    "0x098B716B8Aaf21512996dC57EB0615e2383E2f96": {"name": "Ronin Bridge", "type": "Bridge", "risk": "MEDIUM"},
    
    # DeFi Protocols
    "0x1f98431c8ad98523631ae4a59f267346ea31f984": {"name": "Uniswap V3", "type": "DEX", "risk": "LOW"},
    "0x68b3465833fb72B5A828cCEd3294e3B6b3214313": {"name": "Uniswap Router", "type": "DEX", "risk": "LOW"},
    
    # Known Scam Wallets
    "0x0000000000000000000000000000000000000000": {"name": "Null Address", "type": "System", "risk": "MEDIUM"},
}

def seed():
    db = SessionLocal()
    count = 0
    try:
        print("Seeding Threat Intelligence Data...")
        for address, data in KNOWN_ENTITIES.items():
            exists = db.query(ThreatIntel).filter_by(address=address).first()
            if not exists:
                ti = ThreatIntel(
                    address=address,
                    chain='ethereum',
                    entity_name=data['name'],
                    entity_type=data['type'],
                    threat_type=data['type'] if data['risk'] in ['CRITICAL', 'HIGH'] else 'known_entity',
                    source='internal_db',
                    confidence=1.0 if data['risk'] in ['CRITICAL', 'HIGH'] else 0.8,
                    description=f"{data['name']} ({data['type']})"
                )
                db.add(ti)
                count += 1
        
        db.commit()
        print(f"✅ Added {count} new entities to ThreatIntel.")
    except Exception as e:
        print(f"❌ Error seeding DB: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    seed()
