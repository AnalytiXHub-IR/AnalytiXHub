"""
Batch Analysis Module
Analyze multiple addresses simultaneously and generate comparison reports
"""

import csv
import json
import os
from datetime import datetime
from analyzer import analyze_live_eth
import pandas as pd

class BatchAnalyzer:
    """Batch analysis of multiple cryptocurrency addresses"""
    
    def __init__(self, output_dir="exports/batch_analysis"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.results = []
        self.timestamp = datetime.now()
        
    def analyze_from_csv(self, csv_file):
        """Analyze addresses from CSV file"""
        addresses = []
        
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    addr = row.get('address') or row.get('Address') or row.get('addr')
                    if addr:
                        addresses.append({
                            'address': addr.strip(),
                            'tag': row.get('tag', row.get('Tag', '')),
                            'notes': row.get('notes', row.get('Notes', ''))
                        })
        except Exception as e:
            raise Exception(f"Error reading CSV: {str(e)}")
        
        return self.analyze_addresses(addresses)
    
    def analyze_from_list(self, address_list):
        """Analyze from list of addresses"""
        addresses = [{'address': addr.strip(), 'tag': '', 'notes': ''} for addr in address_list]
        return self.analyze_addresses(addresses)
    
    def analyze_addresses(self, addresses):
        """Analyze multiple addresses and return results"""
        results = []
        
        for i, item in enumerate(addresses):
            try:
                address = item['address']
                print(f"Analyzing {i+1}/{len(addresses)}: {address}")
                
                summary = analyze_live_eth(address)
                
                result = {
                    'address': address,
                    'tag': item.get('tag', ''),
                    'notes': item.get('notes', ''),
                    'total_transactions': summary.get('total_transactions', 0),
                    'risk_score': summary.get('risk_score', 0),
                    'confidence_score': summary.get('confidence_score', 0),
                    'entity_type': summary.get('entity_type', 'Unknown'),
                    'total_received': summary.get('total_received', 0),
                    'total_sent': summary.get('total_sent', 0),
                    'patterns_detected': summary.get('patterns_detected', []),
                    'top_pattern': summary.get('top_pattern', 'None'),
                    'victim_count': len(summary.get('top_victims', [])),
                    'suspect_count': len(summary.get('top_suspects', []))
                }
                
                results.append(result)
                self.results.append(result)
                
            except Exception as e:
                result = {
                    'address': item['address'],
                    'tag': item.get('tag', ''),
                    'error': str(e),
                    'status': 'FAILED'
                }
                results.append(result)
                self.results.append(result)
        
        return results
    
    def generate_csv_report(self, results=None, filename="batch_analysis_results.csv"):
        """Generate CSV report of batch analysis"""
        if results is None:
            results = self.results
        
        if not results:
            return None
        
        output_path = os.path.join(self.output_dir, filename)
        
        # Prepare data for CSV
        csv_rows = []
        for result in results:
            row = {
                'Address': result.get('address', ''),
                'Tag': result.get('tag', ''),
                'Risk Score': result.get('risk_score', 'ERROR'),
                'Confidence': f"{result.get('confidence_score', 0)}%",
                'Entity Type': result.get('entity_type', 'Unknown'),
                'Total TX': result.get('total_transactions', 0),
                'ETH Received': f"{result.get('total_received', 0):.4f}",
                'ETH Sent': f"{result.get('total_sent', 0):.4f}",
                'Patterns': len(result.get('patterns_detected', [])),
                'Top Pattern': result.get('top_pattern', 'None'),
                'Status': 'ANALYZED' if 'risk_score' in result else 'FAILED'
            }
            csv_rows.append(row)
        
        # Write CSV
        with open(output_path, 'w', newline='') as f:
            fieldnames = ['Address', 'Tag', 'Risk Score', 'Confidence', 'Entity Type', 
                         'Total TX', 'ETH Received', 'ETH Sent', 'Patterns', 'Top Pattern', 'Status']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)
        
        return output_path
    
    def generate_json_report(self, results=None, filename="batch_analysis_results.json"):
        """Generate JSON report of batch analysis"""
        if results is None:
            results = self.results
        
        output_path = os.path.join(self.output_dir, filename)
        
        report = {
            'timestamp': self.timestamp.isoformat(),
            'total_addresses': len(results),
            'successful_analyses': len([r for r in results if 'risk_score' in r]),
            'failed_analyses': len([r for r in results if 'error' in r]),
            'results': results
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return output_path
    
    def generate_comparison_report(self, results=None, filename="batch_comparison.txt"):
        """Generate human-readable comparison report"""
        if results is None:
            results = self.results
        
        output_path = os.path.join(self.output_dir, filename)
        
        # Sort by risk score
        valid_results = [r for r in results if 'risk_score' in r]
        valid_results.sort(key=lambda x: x.get('risk_score', 0), reverse=True)
        
        report_lines = [
            "=" * 80,
            "BATCH ANALYSIS COMPARISON REPORT",
            f"Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            "",
            f"Total Addresses Analyzed: {len(valid_results)}",
            f"High Risk (>70): {len([r for r in valid_results if r.get('risk_score', 0) > 70])}",
            f"Medium Risk (30-70): {len([r for r in valid_results if 30 <= r.get('risk_score', 0) <= 70])}",
            f"Low Risk (<30): {len([r for r in valid_results if r.get('risk_score', 0) < 30])}",
            "",
            "=" * 80,
            "DETAILED RESULTS (Sorted by Risk Score)",
            "=" * 80,
            ""
        ]
        
        for i, result in enumerate(valid_results, 1):
            report_lines.extend([
                f"{i}. Address: {result['address']}",
                f"   Tag: {result.get('tag', 'N/A')}",
                f"   Risk Score: {result.get('risk_score', 0)}/100",
                f"   Confidence: {result.get('confidence_score', 0)}%",
                f"   Entity Type: {result.get('entity_type', 'Unknown')}",
                f"   Total Transactions: {result.get('total_transactions', 0)}",
                f"   Total ETH Received: {result.get('total_received', 0):.4f}",
                f"   Total ETH Sent: {result.get('total_sent', 0):.4f}",
                f"   Patterns Detected: {len(result.get('patterns_detected', []))}",
                f"   Top Pattern: {result.get('top_pattern', 'None')}",
                ""
            ])
        
        with open(output_path, 'w') as f:
            f.write("\n".join(report_lines))
        
        return output_path
    
    def get_summary_statistics(self):
        """Get summary statistics of batch analysis"""
        if not self.results:
            return {}
        
        valid_results = [r for r in self.results if 'risk_score' in r]
        
        if not valid_results:
            return {'error': 'No successful analyses'}
        
        risk_scores = [r.get('risk_score', 0) for r in valid_results]
        confidences = [r.get('confidence_score', 0) for r in valid_results]
        eth_received = [r.get('total_received', 0) for r in valid_results]
        eth_sent = [r.get('total_sent', 0) for r in valid_results]
        
        return {
            'total_addresses': len(valid_results),
            'avg_risk_score': sum(risk_scores) / len(risk_scores),
            'max_risk_score': max(risk_scores),
            'min_risk_score': min(risk_scores),
            'avg_confidence': sum(confidences) / len(confidences),
            'total_eth_received': sum(eth_received),
            'total_eth_sent': sum(eth_sent),
            'unique_patterns': set(
                pattern 
                for r in valid_results 
                for pattern in r.get('patterns_detected', [])
            )
        }
    
    def export_summary(self):
        """Export analysis summary as text"""
        stats = self.get_summary_statistics()
        
        summary_text = f"""
BATCH ANALYSIS SUMMARY
Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Total Addresses Analyzed: {stats.get('total_addresses', 0)}
Average Risk Score: {stats.get('avg_risk_score', 0):.2f}/100
Max Risk Score: {stats.get('max_risk_score', 0)}/100
Min Risk Score: {stats.get('min_risk_score', 0)}/100

Average Confidence: {stats.get('avg_confidence', 0):.2f}%
Total ETH Received: {stats.get('total_eth_received', 0):.4f}
Total ETH Sent: {stats.get('total_eth_sent', 0):.4f}

Unique Patterns Detected: {len(stats.get('unique_patterns', set()))}
"""
        
        return summary_text.strip()
