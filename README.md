# AnalytiXHub - Advanced Blockchain Forensic Intelligence

**Professional Multi-Chain Cryptocurrency Forensics & AML Investigation Platform**

![Version](https://img.shields.io/badge/version-5.0-blue)
![Status](https://img.shields.io/badge/status-Production%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-Proprietary-red)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Supported Blockchains](#supported-blockchains)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [Forensic Engine](#forensic-engine)
- [Project Structure](#project-structure)
- [Credits](#credits)

---

## 🎯 Overview

**AnalytiXHub** is a state-of-the-art blockchain forensic intelligence platform designed for law enforcement, compliance officers, and security researchers. It provides a unified, "Cyber-themed" interface to track, analyze, and visualize fund flows across multiple blockchain ecosystems.

By leveraging advanced machine learning, real-time threat intelligence, and cross-address clustering, AnalytiXHub transforms raw transaction data into actionable investigative insights.

---

## 🚀 What's New in V5.0

### 1. High-Volume Transaction Optimization
- **Backend Scaling**: Integrated `bulk_insert_mappings` to process massive address histories (e.g., 60,000+ transactions) near-instantaneously.
- **Frontend Rendering**: Optimized UI logic to dynamically render the top 500 transactions for a snappy user experience while comprehensively analyzing the full dataset via the backend threat engine.

### 2. Enhanced Solana Forensics
- **Accurate Flow Attribution**: Revamped the Solscan V2 parsing logic to precisely attribute sender and receiver transaction directions based on underlying balance changes.
- **Complete Visibility**: Addressed dropping of incoming/outgoing records to ensure 100% accurate representation of complex Solana movements.

### 3. Data Integrity & UI Refinements
- **Case-Sensitive Forensics**: Guaranteed original address and hash casing is preserved throughout the pipeline (from Fetch to Database to UI) to prevent mismatch errors.
- **Streamlined API Configuration**: Removed redundant network entries (e.g., duplicates of Worldchain, abstract networks) to provide a cleaner Multi-Chain dropdown array.
- **Threat Intel Upgrades**: Enhanced investigations with highly accurate rendering of indicators.

---

## ✨ Key Features

### 1. **Unified Multi-Chain Dashboard**
- **15+ EVM Chains**: One API key for Ethereum, Polygon, BSC, Arbitrum, Base, and more through Etherscan V2.
- **Non-EVM Support**: Native integration for **Bitcoin**, **Solana**, **Tron**, and **Dogecoin**.
- **Cyber Aesthetic**: High-performance, interactive dashboard with Vanta.js backgrounds and real-time data streaming.

### 2. **Threat Intelligence V2**
- **Aggregated Feeds**: Live checks against **OFAC** sanctions, **Etherscan Phishing** filters, and **SlowMist** malicious address lists.
- **Automated Risk Scoring**: 0-100 risk assessment based on behavioral patterns and entity matching.
- **Severity Classification**: Real-time critical/high/medium risk tagging for all investigated addresses.

### 3. **AI-Driven Anomaly Detection**
- **ML Engine**: Utilizes **Isolation Forest** (Scikit-Learn) to identify statistical outliers in transaction volume, gas prices, and timing.
- **Behavioral Patterns**: Heuristic detection for **Peeling Chains**, **Round Tripping**, and **Structuring** attempts.
- **Explanatory Narratives**: Human-readable descriptions of *why* a transaction was flagged as anomalous.

### 4. **Forensic Network Visualization**
- **Interactive Tracer**: Visual breadcrumbs mapping fund hops through the ecosystem.
- **Dynamic Clustering**: Identify related wallets (mixer outputs, dust attacks, circular patterns) via graph-based analysis.
- **Evidence Management**: Detailed "Top Suspects" and "Top Victims" breakdowns for complex investigations.

### 5. **Case Management & Persistence**
- **Persistent Storage**: Save investigation history and analysis results to a local database.
- **API Optimization**: Intelligent caching reduces external API consumption and improves load times.
- **PDF Reporting**: Generate professional forensic reports with executive summaries and technical annexes.

---

## 🌐 Supported Blockchains

| Ecosystem | Chain | Integration | Provider |
|-----------|-------|-------------|----------|
| **EVM** | Ethereum, BSC, Polygon, Arbitrum, Optimism, Avalanche, Fantom, Base, Cronos, Moonbeam, Gnosis, Celo, Blast, Linea | ✅ Etherscan V2 | Unified API |
| **Bitcoin** | BTC Mainnet | ✅ Mempool.space | Public API |
| **Solana** | SOL Mainnet | ✅ Solscan V2 | Pro/Public API |
| **Tron** | TRON Mainnet | ✅ TronScan | Official API |
| **Dogecoin** | DOGE Mainnet | ✅ BlockCypher | Tokenized API |
| **XRP** | XRPL | ✅ Public Nodes | RPC |

---

## 🏗️ Architecture

### Technology Stack
- **Frontend**: Flask + Jinja2, Chart.js, Cytoscape.js, Bootstrap 5.3 (Cyber Theme).
- **Backend**: Python 3.10+, SQLAlchemy ORM.
- **Intelligence**: Scikit-Learn (ML), Google Gemini AI (Narrative generation).
- **APIs**: Etherscan Unified V2, TronGrid, Solscan, Mempool.space.

### Data Flow
1. **Ingress**: Investigator inputs Address & Chain.
2. **Fetch**: `MultiChainFetcher` selects optimal API provider and retrieves raw transaction history.
3. **Analyze**: `MLEngine` and `ThreatIntelligenceAPI` process data in parallel.
4. **Persist**: Results are stored in the Case Database.
5. **Render**: Dashboard visualizes risk, anomalies, and network graphs.

---

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- PostgreSQL (Optional, defaults to SQLite)
- API Keys: Etherscan, Solscan, TronGrid, Gemini AI.

### Steps
1. **Clone & Enter**:
   ```bash
   git clone <repo-url>
   cd AnalytiXHub
   ```

2. **Setup Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Settings**:
   Create a `.env` file based on the provided template:
   ```env
   ETHERSCAN_API_KEY=your_key
   SOLANA_API_KEY=your_key
   TRON_API_KEY=your_key
   GEMINI_API_KEY=your_key
   SECRET_KEY=generate_a_random_string
   ```

4. **Initialize & Run**:
   ```bash
   python app.py
   ```
   *Access dashboard at http://127.0.0.1:5000*

---

## 🚀 Usage Guide

### 1. Starting an Investigation
1. Navigate to the **Dashboard**.
2. Create a **New Case** (e.g., "Ransomware Tracking").
3. Input the target address and select the blockchain.
4. Click **Analyze**.

### 2. Exploring Findings
- **Overview**: Check the global Risk Score and detected AML patterns.
- **Threat Intel**: See if the address is listed on any international sanctions or phishing lists.
- **Visual Tracer**: Use the interactive graph to follow the money visually.
- **ML Anomalies**: Review transactions flagged for unusual behavior.

### 3. Generating Reports
- Go to the **Report** tab.
- Click **Generate Forensic Report**.
- Download the PDF containing all findings and AI-generated analysis.

---

## 🔍 Forensic Engine

### AML Pattern Detection
AnalytiXHub identifies 7 core suspicious behaviors:
- **Rapid Succession**: High-speed transfers indicating bot/structuring.
- **Mixing Suspicion**: Disproportional inputs vs outputs.
- **Consolidation**: "Many-to-One" pooling of funds.
- **Layering**: High-hop counts between source and destination.
- **Dust Spam**: Intentional blockchain bloating.

### ML Anomaly Scoring
The system calculates an **Anomaly Score (0.0 - 1.0)** for every transaction. Values above **0.7** are automatically flagged as "Suspicious" and highlighted in the dashboard.

---

## 📁 Project Structure

- `app.py`: Flask core and routing logic.
- `modules/fetchers/`: Multi-chain data retrieval logic.
- `modules/analyzers/`: Threat intelligence, ML engine, and clustering.
- `modules/core/`: Database models and case management.
- `templates/`: Cyber-themed HTML5 dashboards.
- `static/`: CSS/JS assets (Chart.js, Cytoscape).

---

## ⚖️ Credits & Disclaimer
AnalytiXHub is provided for forensic and educational purposes. Always verify findings with secondary sources before taking legal action.

Developed by **AnalytiXHub-IR Team**.
