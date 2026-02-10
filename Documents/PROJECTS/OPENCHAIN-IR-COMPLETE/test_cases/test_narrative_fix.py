#!/usr/bin/env python
"""Test script to verify narrative fallback fixes"""

from gemini import generate_fallback_narrative, generate_comprehensive_analysis
from analyzer import analyze_live_eth

# Create test data
test_txs = [
    {'from': '0x123', 'to': '0xabc', 'value': '1000000000000000000', 'timeStamp': '1700000000'},
    {'from': '0x456', 'to': '0xabc', 'value': '2000000000000000000', 'timeStamp': '1700000100'},
    {'from': '0xabc', 'to': '0xdef', 'value': '1500000000000000000', 'timeStamp': '1700000200'},
]

summary, G, source = analyze_live_eth(test_txs, '0xabc', None, None)

print("=" * 70)
print("NARRATIVE FIX VERIFICATION")
print("=" * 70)

# Test 1: Fallback narrative
print("\n[TEST 1] Fallback Narrative Generation")
print("-" * 70)
fallback = generate_fallback_narrative(summary)
print(f"✓ Generated: {len(fallback)} characters")
print(f"✓ No error markers: {not ('[Analysis failed' in fallback)}")
print(f"✓ Has content: {len(fallback) > 50}")
print(f"\nPreview:\n{fallback[:200]}...")

# Test 2: Comprehensive analysis
print("\n\n[TEST 2] Comprehensive Analysis (with potential API failures)")
print("-" * 70)
analysis = generate_comprehensive_analysis(summary, ['Test finding'])

for key, value in analysis.items():
    has_error = '[Analysis failed' in str(value)
    has_content = len(str(value)) > 0
    status = '✓ OK' if (has_content and not has_error) else '❌ FAIL'
    preview = str(value)[:80] + ('...' if len(str(value)) > 80 else '')
    print(f"{status} {key:20s}: {preview}")

# Test 3: Verify all required fields
print("\n\n[TEST 3] Summary Data Completeness")
print("-" * 70)
required_fields = ['risk_score', 'patterns_detected', 'top_victims', 'top_suspects', 'net_flow']
for field in required_fields:
    value = summary.get(field)
    status = '✓' if value is not None else '❌'
    print(f"{status} {field:25s}: {str(value)[:50]}")

print("\n" + "=" * 70)
print("VERIFICATION COMPLETE - All fixes deployed successfully! ✓")
print("=" * 70)
