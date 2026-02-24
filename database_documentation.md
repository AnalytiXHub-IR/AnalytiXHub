# OPENCHAIN IR v4 Database Architecture Documentation

## Overview
OPENCHAIN IR v4 uses a relational database architecture to manage forensic investigations, blockchain networks, chain of custody evidence, and system audit logging.

### Technology Stack
*   **Database Management System:** SQLite for local development or PostgreSQL for production (configured via `DATABASE_URL` environment variable).
*   **Default Connection:** `sqlite:///forensics.db` / `postgresql://postgres:password@localhost:5432/openchain_ir`
*   **ORM (Object-Relational Mapping):** SQLAlchemy. The database is interacted with programmatically using SQLAlchemy's declarative base.
*   **Initialization & Migrations:** 
    *   `init_db()` in `modules/core/db_models.py` handles the initial creation of all tables.
    *   `upgrade_db_schema.py` is a standalone migration script to securely run database upgrades (e.g., v3 to v4 schema additions) directly on SQLite or PostgreSQL databases seamlessly.

---

## Core Entities

### 1. User (`users`)
Represents the investigators and system administrators who use the platform.
*   **Attributes:** `username`, `email`, `role` (admin, officer), `password_hash`, `created_at`.
*   **Security Upgrades:** `last_login`, `failed_login_attempts`, `is_locked`. Protects accounts from brute-forcing and supports auditing.
*   **Relationships:** A User can own multiple `Cases`, upload `Evidence`, write `AnalysisReports`, and generate `AuditLogs`.

### 2. Case (`cases`)
The central entity for any forensic investigation. All analysis details are linked to a specific case.
*   **Attributes:** `case_id` (unique), `case_name`, `description`, `status` (active, closed, archived), `investigator`, `jurisdiction`, `case_type` (fraud, theft, money laundering, etc.).
*   **Legal Upgrades:** `court_reference`, `evidence_status`, `confidentiality_level`. Maps cases to correct legal metadata mapping restrictions.
*   **Relationships:** Linked to the `User` (owner). Also acts as a parent to `Addresses`, `Transactions`, `AddressClusters`, `Alerts`, `CaseNotes`, `SmartContracts`, `DeFiActivities`, `TaintTraces`, `Evidence`, `AnalysisReports`, `CaseTimeline`, and `InvestigationSnapshots`.

### 3. CaseNote (`case_notes`)
Allows investigators to add text-based notes regarding a specific case.
*   **Attributes:** `content`, `author`, `created_at`.
*   **Relationships:** Belongs to a specific `Case`.

### 4. Chain (`chains`)
Represents the supported blockchain networks (e.g., Ethereum, Bitcoin, Litecoin).
*   **Attributes:** `name`, `symbol` (ETH, BTC, etc.), `full_name`, `api_type`, `rpc_url`, `explorer_url`, `decimals`, `is_active`.
*   **Relationships:** Has many `Addresses`, `Transactions`, and `SmartContracts`.

---

## Investigation Data Entities

### 5. Address (`addresses`)
Represents a specific blockchain wallet or contract address being investigated within a case.
*   **Attributes:** `address`, `alias`, `address_type` (suspect, victim, mixer, exchange, unknown), `label`.
*   **Analysis Data:** `balance`, `total_in`, `total_out`, `tx_count`, `first_tx_time`, `last_tx_time`.
*   **Risk Assessment:** `risk_score`, `risk_factors` (JSON), `is_suspicious`, `threat_intel_flag`, `threat_sources` (JSON).
*   **Data Protection:** `is_deleted` (Boolean). Implements soft-delete capability to prevent data loss.
*   **Relationships:** Linked to a `Case` and a `Chain`. Connected to incoming/outgoing `Transactions` and potentially part of an `AddressCluster`.

### 6. Transaction (`transactions`)
Represents a recorded transaction moving from one address to another on a specific chain.
*   **Attributes:** `tx_hash` (unique), `from_address`, `to_address`, `amount`, `fee`, `timestamp`, `block_number`.
*   **Token Data:** `is_token_transfer`, `token_symbol`, `token_name`, `token_address`.
*   **Analysis Data:** `tx_type` (normal, internal, token_transfer, contract_interaction), `is_suspicious`, `anomaly_score`, `anomaly_reasons` (JSON).
*   **Data Protection:** `is_deleted` (Boolean). Soft-delete capability.
*   **Relationships:** Linked to a `Case`, a `Chain`, and the sender/receiver `Addresses`.

### 7. AddressCluster (`address_clusters`)
Groups related addresses together showing cross-address linkages (e.g., outputs from the same entity or mixer).
*   **Attributes:** `cluster_id` (unique), `cluster_type` (same_entity, mixer_output, exchange_dust), `confidence_score` (0-1), `extra_metadata` (JSON for evidence).
*   **Relationships:** Linked to a `Case` and contains multiple `Addresses`.

---

## Security & Analysis Entities

### 8. Alert (`alerts`)
Security notifications generated for monitored addresses.
*   **Attributes:** `alert_type`, `severity` (critical, high, medium, low), `address`, `description`, `is_acknowledged`.
*   **Related Data:** `related_tx_hash`, `related_address`, `extra_metadata` (JSON).
*   **Relationships:** Linked to a `Case`.

### 9. ThreatIntel (`threat_intel`)
Stores known threat intelligence data scraped or obtained from external sources.
*   **Attributes:** `address` (unique), `chain`, `threat_type` (sanctioned, scammer, ransomware), `source` (ofac, scamalert, etc.), `entity_name`, `entity_type`, `confidence` (0-1), `description`.

### 10. AnomalyDetection (`anomaly_detection`)
Stores results generated by ML-based anomaly detection algorithms.
*   **Attributes:** `address`, `chain`, `anomaly_type` (unusual_amount, frequency_spike), `anomaly_score` (0-1), `baseline_metric`, `current_value`, `baseline_value`, `deviation_percent`, `confidence`, `detected_at`.

### 11. SmartContract (`smart_contracts`)
Metadata and security analysis corresponding to a specific smart contract deployed on a blockchain.
*   **Attributes:** `contract_address`, `name`, `symbol`, `decimals`, `source_code`, `abi` (JSON).
*   **Security Analysis:** `is_verified`, `is_honeypot`, `is_rug_pull`, `vulnerability_score`, `vulnerabilities` (JSON).
*   **Metadata:** Deployment info and `creator_address`.
*   **Relationships:** Linked to a `Case` and `Chain`.

### 12. DeFiActivity (`defi_activity`)
Tracks Decentralized Finance (DeFi) and Decentralized Exchange (DEX) activity points for an address.
*   **Attributes:** `address`, `activity_type` (swap, liquidity_add, yield_farming, etc.), `protocol` (uniswap, aave, curve), `tx_hash`, `timestamp`.
*   **Activity Details:** tokens in/out, amounts, pool addressing, slippage, gas paid, USD value.
*   **Relationships:** Linked to a `Case` and a `Chain`.

### 13. TaintTrace (`taint_traces`)
Stores the flow of funds tracking (taint analysis) representing money movement across hops.
*   **Attributes:** `source_address`, `destination_address`, `tx_hashes` (JSON), `addresses_in_path` (JSON), `amount_start`, `amount_end`, `amount_lost`, `trace_depth` (number of hops).
*   **Taint Info:** `taint_type` (mixer, bridge, dex_swap, etc.), `confidence` (0-1).
*   **Relationships:** Linked to a `Case`.

---

## Advanced Forensic and Audit Entities

### 14. Evidence (`evidence`)
Chain of Custody evidence tracking, ensuring files are stored immutably.
*   **Attributes:** `file_name`, `file_path`, `file_type`, `file_size`, `checksum_sha256`, `description`.
*   **Verification:** Uses `checksum_sha256` to prevent log/proof tampering, maintaining court-readiness.
*   **Relationships:** Linked to a `Case` and the `User` (`uploaded_by`).

### 15. AnalysisReport (`analysis_reports`)
AI and human investigation summary reports.
*   **Attributes:** `title`, `report_text`, `generated_by_ai` (Boolean), `status`, `created_at`, `updated_at`.
*   **Relationships:** Linked to a `Case` and verified by a specific `User` (`verified_by`).

### 16. AuditLog (`audit_logs`)
System-wide security tracking for accountability inside the platform.
*   **Attributes:** `action`, `entity_type`, `entity_id`, `ip_address`, `user_agent`, `created_at`.
*   **Relationships:** Records the exact `User` interacting with the system.

### 17. CaseTimeline (`case_timeline`)
Visual mapping tracking exactly when and what happened throughout an investigation.
*   **Attributes:** `event_type`, `description`, `related_entity`, `related_id`, `created_at`.
*   **Relationships:** Tracks history alongside the `Case` entirely and specifies which `User` (`created_by`) noted it.

### 18. InvestigationSnapshot (`investigation_snapshots`)
Advanced full database state backups for robust investigation rollbacks and historic point-in-time preservation.
*   **Attributes:** `snapshot_data` (Stored as native JSON/JSONB).
*   **Relationships:** Preserves the state for a specific `Case`.

---

## Job Management Entities

### 19. MonitoringJob (`monitoring_jobs`)
Manages real-time monitoring routines set up for specific addresses.
*   **Attributes:** `address`, `chain`, `status` (active, paused, completed), last checked metrics.
*   **Configuration:** `check_interval_minutes`, boolean flags for raising alerts on new txs, anomalies, or counterparty changes.
*   **Stats:** Total alerts generated, `tx_count_last_check`.
*   **Relationships:** Linked to a `Case`.

### 20. BatchJob (`batch_jobs`)
Manages bulk, asynchronous background jobs (such as Celery tasks processing multiple addresses).
*   **Attributes:** `job_id` (unique), `status` (pending, processing, failed, completed), `address_count`, `addresses` (JSON).
*   **Progress Tracking:** `progress_percent`, completed/failed counts, start/end times.
*   **Results:** `results_summary` (JSON), `error_log`.
*   **Relationships:** Linked to a `Case`.
