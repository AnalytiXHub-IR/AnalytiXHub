# ✅ SQLAlchemy Reserved Word Fix

## Issue
Flask app failed to start with error:
```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
```

## Root Cause
The SQLAlchemy ORM reserves the name `metadata` for the table metadata registry. Having columns named `metadata` in model classes conflicts with this reserved word.

## Solution
Renamed all `metadata` column definitions to `extra_metadata` in db_models.py

### Fixed Classes (8 total)
1. ✅ `AddressCluster` (line 190)
2. ✅ `Alert` (line 213)
3. ✅ `ThreatIntel` (line 239)
4. ✅ `AnomalyDetection` (line 262)
5. ✅ `SmartContract` (line 374)
6. ✅ `DeFiActivity` (line 439)
7. ✅ `MonitoringJob` (line 467)
8. ✅ `BatchJob` (line 485)

## Changes Made
```python
# ❌ BEFORE
metadata = Column(JSON, default={})

# ✅ AFTER
extra_metadata = Column(JSON, default={})
```

## Verification
✅ db_models.py compiles without errors  
✅ app.py imports successfully  
✅ Flask app ready to start  

## Status
🟢 **FIXED** - App is ready to run!

Start with:
```bash
python app.py
```

Then visit: http://127.0.0.1:5000
