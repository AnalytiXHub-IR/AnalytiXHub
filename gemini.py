import os
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

def generate_comprehensive_analysis(summary, findings):
    """
    Generates comprehensive forensic analysis using Gemini API with retry logic.
    Analyzes patterns, risk, victims, and suspects.
    """
    if not API_KEY:
        return {
            "narrative": "Error: Missing GEMINI_API_KEY in .env file.",
            "pattern_analysis": "",
            "risk_assessment": "",
            "suspect_profile": ""
        }

    client = genai.Client(api_key=API_KEY)

    # Prepare comprehensive prompt
    patterns = summary.get("patterns", {})
    risk_factors = summary.get("risk_factors", [])
    top_suspects = summary.get("top_suspects", [])
    top_victims = summary.get("top_victims", [])

    prompt_narrative = f"""
    ROLE: Forensic Financial Analyst
    TASK: Analyze Ethereum transaction patterns for money laundering indicators and suspicious activity.
    
    TRANSACTION DATA:
    - Total Inflow: {summary.get('total_volume_in')} ETH
    - Total Outflow: {summary.get('total_volume_out')} ETH
    - Net Flow: {summary.get('net_flow')} ETH
    - Transactions: {summary.get('total_transactions')}
    - Unique Sources: {summary.get('unique_senders')}
    - Unique Destinations: {summary.get('unique_receivers')}
    - Avg Transaction: {summary.get('avg_transaction_value')} ETH
    - Max Transaction: {summary.get('max_transaction_value')} ETH
    
    DETECTED PATTERNS:
    - Rapid Succession: {patterns.get('rapid_succession', False)}
    - Round Amounts: {len(patterns.get('round_amounts', []))} detected
    - Dust Transactions: {len(patterns.get('dust_transactions', []))} detected
    - High Frequency Wallet: {patterns.get('high_frequency_wallet', False)}
    - Mixing Service Behavior: {patterns.get('mixing_service_suspicion', False)}
    - Consolidation Pattern: {patterns.get('consolidation_pattern', False)}
    - Layering Pattern: {patterns.get('layering_pattern', False)}
    
    RISK FACTORS: {', '.join(risk_factors) if risk_factors else 'None detected'}
    
    INSTRUCTIONS:
    - Provide a factual forensic narrative (100-150 words)
    - Identify if patterns suggest money laundering techniques (mixing, structuring, layering)
    - Assess the risk level and activity type
    - Do NOT identify specific individuals
    - Use professional AML/CFT terminology
    - Keep analysis objective and evidence-based
    """

    prompt_pattern = f"""
    ROLE: Blockchain Forensics Expert
    TASK: Analyze transaction patterns for AML concerns.
    
    Detected Patterns:
    {patterns}
    
    Risk Score: {summary.get('risk_score', 0)}/100
    Risk Factors: {', '.join(risk_factors) if risk_factors else 'None'}
    
    Provide a structured analysis:
    1. Pattern Type (if any): Describe the type of suspicious activity (mixing, structuring, layering, etc.)
    2. AML Concern Level: LOW/MEDIUM/HIGH/CRITICAL
    3. Justification: 2-3 sentences explaining why
    4. Recommended Action: What investigation step is next
    
    Keep it concise and professional.
    """

    prompt_suspects = f"""
    ROLE: Financial Investigator
    TASK: Profile top destination addresses based on transaction patterns.
    
    Top Suspect Destinations (by volume):
    {[f"{addr[:20]}...: {val:.4f} ETH" for addr, val in top_suspects[:5]]}
    
    Transaction Pattern: {summary.get('total_transactions')} transactions
    Flow Type: {'Sending funds' if summary.get('net_flow', 0) < 0 else 'Receiving funds'}
    
    Provide brief analysis of each top destination address:
    - Is it likely an exchange, mixing service, or individual wallet?
    - Any red flags?
    - Recommended tagging or monitoring
    
    Be brief (2-3 sentences per address).
    """

    results = {
        "narrative": "",
        "pattern_analysis": "",
        "risk_assessment": "",
        "suspect_profile": ""
    }

    # Generate each analysis with retry logic
    prompts = [
        ("narrative", prompt_narrative),
        ("pattern_analysis", prompt_pattern),
        ("risk_assessment", prompt_suspects)
    ]

    for key, prompt in prompts:
        result = generate_with_retry(client, prompt)
        if not result:
            # Use fallback templates when API fails
            if key == "narrative":
                result = generate_fallback_narrative(summary)
            else:
                result = f"[Analysis temporarily unavailable. Please check API configuration.]"
        results[key] = result

    return results


def generate_with_retry(client, prompt_text, max_retries=2):
    """
    Generates content with retry logic for rate limiting.
    Falls back to template if API is unavailable.
    """
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt_text,
            )
            return response.text if response.text else None
            
        except Exception as e:
            error_str = str(e)
            is_rate_limited = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str
            
            if is_rate_limited and attempt < max_retries - 1:
                print(f"[AI] Rate limited. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            
            print(f"[AI ERROR] {error_str[:100]}")
            return None


def generate_narrative(summary, findings):
    """
    Legacy function for backward compatibility.
    Generates fallback narrative if new analysis fails.
    """
    results = generate_comprehensive_analysis(summary, findings)
    
    if results["narrative"]:
        return results["narrative"]
    
    # Fallback to template
    return generate_fallback_narrative(summary)


def generate_fallback_narrative(summary):
    """
    Generates template-based narrative when API is unavailable.
    """
    inflow = summary.get('total_volume_in', 0)
    outflow = summary.get('total_volume_out', 0)
    net = summary.get('net_flow', 0)
    senders = summary.get('unique_senders', 0)
    receivers = summary.get('unique_receivers', 0)
    period = f"{summary.get('start_date', 'N/A')} to {summary.get('end_date', 'N/A')}"
    risk_score = summary.get('risk_score', 0)
    risk_factors = summary.get('risk_factors', [])
    
    flow_type = "accumulation" if net > 0 else "liquidation" if net < 0 else "neutral"
    volume_velocity = "high" if (inflow + outflow) > 10000 else "moderate" if (inflow + outflow) > 1000 else "low"
    risk_level = "CRITICAL" if risk_score >= 70 else "HIGH" if risk_score >= 50 else "MEDIUM" if risk_score >= 30 else "LOW"
    
    narrative = f"""During the analysis period ({period}), the target address exhibited {volume_velocity} transaction velocity with {senders} inbound and {receivers} outbound counterparties. Total inflow of {inflow:.2f} ETH against outflow of {outflow:.2f} ETH resulted in a net {flow_type} of {abs(net):.2f} ETH. Risk Assessment: {risk_level} ({risk_score}/100). {', '.join(risk_factors) if risk_factors else 'No major risk factors detected'}. Transaction patterns suggest deliberate capital movement."""
    
    return narrative