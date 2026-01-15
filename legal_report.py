"""
Legal Report Template Generator for Law Enforcement
FIR (First Information Report) ready format
Generates blockchain evidence reports admissible in court
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from datetime import datetime
import os

class LegalReportGenerator:
    """Generate FIR-ready legal reports for law enforcement"""
    
    def __init__(self, case_id, investigator_name, department):
        self.case_id = case_id
        self.investigator_name = investigator_name
        self.department = department
        self.timestamp = datetime.now()
        
    def create_fir_report(self, summary, analysis, root_address, output_file="exports/FIR_Report.pdf"):
        """Create FIR (First Information Report) document"""
        os.makedirs("exports", exist_ok=True)
        
        doc = SimpleDocTemplate(output_file, pagesize=A4, rightMargin=0.5*inch, leftMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#000000'),
            spaceAfter=12,
            alignment=1  # CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=8,
            spaceBefore=8,
            borderBottom=1,
            borderColor=colors.HexColor('#cccccc')
        )
        
        # Header
        story.append(Paragraph("FIRST INFORMATION REPORT (FIR)", title_style))
        story.append(Paragraph("Digital Forensics - Cryptocurrency Analysis", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Case Information
        case_data = [
            ["FIR Number:", f"CYBER/{self.case_id}"],
            ["Date of Report:", self.timestamp.strftime("%d-%m-%Y")],
            ["Time of Report:", self.timestamp.strftime("%H:%M:%S")],
            ["Investigating Officer:", self.investigator_name],
            ["Department:", self.department],
            ["Digital Evidence Type:", "Ethereum Blockchain Transaction Analysis"],
            ["Investigation Date:", self.timestamp.strftime("%d-%m-%Y")],
            ["Target Address:", root_address[:20] + "..."],
        ]
        
        case_table = Table(case_data, colWidths=[2*inch, 4*inch])
        case_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e6f2ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(case_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Key Findings
        story.append(Paragraph("KEY FINDINGS AND ANALYSIS", heading_style))
        
        findings_data = [
            ["Metric", "Value"],
            ["Total Transactions", str(summary.get("total_transactions", 0))],
            ["Total ETH Received", f"{summary.get('total_received', 0):.4f}"],
            ["Total ETH Sent", f"{summary.get('total_sent', 0):.4f}"],
            ["Net Flow", f"{summary.get('net_flow', 0)} ETH"],
            ["Risk Score", f"{summary.get('risk_score', 0)}/100"],
            ["Confidence Level", f"{summary.get('confidence_score', 0)}%"],
            ["Entity Type", summary.get('entity_type', 'Unknown')],
            ["Patterns Detected", str(len(summary.get('patterns_detected', [])))],
        ]
        
        findings_table = Table(findings_data, colWidths=[2.5*inch, 3.5*inch])
        findings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        
        story.append(findings_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Detailed Analysis
        story.append(Paragraph("DETAILED FORENSIC ANALYSIS", heading_style))
        
        # Handle analysis safely - with fallback for failed analyses
        if isinstance(analysis, dict):
            narrative = analysis.get('narrative', 'Professional analysis of blockchain transaction patterns')
        elif isinstance(analysis, str):
            narrative = analysis
        else:
            narrative = "Professional analysis of blockchain transaction patterns and fund flows"
        
        # If narrative still contains error markers, use fallback
        if not narrative or "[Analysis failed" in narrative:
            from gemini import generate_fallback_narrative
            narrative = generate_fallback_narrative(summary)
            
        story.append(Paragraph("GENERATED NARRATIVE ANALYSIS:", styles['Heading3']))
        story.append(Paragraph(narrative[:800] + "..." if len(narrative) > 800 else narrative, styles['Normal']))
        story.append(Spacer(1, 0.15*inch))
        
        # Patterns Detected
        story.append(Paragraph("Detected Suspicious Patterns:", heading_style))
        patterns = summary.get('patterns_detected', [])
        if patterns:
            pattern_text = "<br/>".join([f"• {p.upper()}" for p in patterns])
            story.append(Paragraph(pattern_text, styles['Normal']))
        else:
            story.append(Paragraph("No suspicious patterns detected.", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Risk Assessment
        story.append(Paragraph("RISK ASSESSMENT", heading_style))
        risk_level = summary.get('risk_score', 0)
        if risk_level < 30:
            risk_category = "LOW RISK"
            color = colors.green
        elif risk_level < 70:
            risk_category = "MEDIUM RISK"
            color = colors.orange
        else:
            risk_category = "HIGH RISK"
            color = colors.red
        
        risk_assessment = f"""
        Based on the forensic analysis of the provided Ethereum address and its transaction patterns,
        this entity has been classified as <b>{risk_category}</b> (Score: {risk_level}/100).
        This assessment is based on:
        <br/>
        <br/>
        • Pattern Detection: {len(summary.get('patterns_detected', []))} suspicious patterns identified
        <br/>
        • Total Transactions: {summary.get('total_transactions', 0)} transactions analyzed
        <br/>
        • Entity Classification: {summary.get('entity_type', 'Unknown')} type entity
        <br/>
        • Network Analysis: {len(summary.get('top_victims', []))} source addresses, {len(summary.get('top_suspects', []))} destination addresses
        <br/>
        • Confidence Level: {summary.get('confidence_score', 0)}% analysis reliability
        """
        
        story.append(Paragraph(risk_assessment.strip(), styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Top Victims (Sources)
        story.append(Paragraph("SOURCE ADDRESSES (VICTIMS)", heading_style))
        victims = summary.get('top_victims', [])[:10]
        if victims:
            victim_data = [["Address", "Amount (ETH)", "Transaction Count"]]
            for addr, amount in victims:
                victim_data.append([addr[:16] + "...", f"{amount:.4f}", ""])
            victim_table = Table(victim_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
            victim_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#90EE90')),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]))
            story.append(victim_table)
        else:
            story.append(Paragraph("No incoming transactions detected.", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Top Suspects (Destinations)
        story.append(Paragraph("DESTINATION ADDRESSES (SUSPECTS)", heading_style))
        suspects = summary.get('top_suspects', [])[:10]
        if suspects:
            suspect_data = [["Address", "Amount (ETH)", "Transaction Count"]]
            for addr, amount in suspects:
                suspect_data.append([addr[:16] + "...", f"{amount:.4f}", ""])
            suspect_table = Table(suspect_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
            suspect_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFB6C6')),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]))
            story.append(suspect_table)
        else:
            story.append(Paragraph("No outgoing transactions detected.", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Page break for second page
        story.append(PageBreak())
        
        # Evidence Chain of Custody
        story.append(Paragraph("EVIDENCE CHAIN OF CUSTODY", heading_style))
        
        custody_data = [
            ["Item", "Description", "Collected By", "Date"],
            ["Primary Evidence", f"Ethereum Address {root_address[:10]}...", 
            self.investigator_name, self.timestamp.strftime("%d-%m-%Y")],
            ["Data Source", "Etherscan API (Public Blockchain Data)", 
            self.investigator_name, self.timestamp.strftime("%d-%m-%Y")],
            ["Analysis Date", "Blockchain Forensic Analysis", 
            self.investigator_name, self.timestamp.strftime("%d-%m-%Y")],
        ]
        
        custody_table = Table(custody_data, colWidths=[1.2*inch, 2.0*inch, 1.5*inch, 1.3*inch])
        custody_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        
        story.append(custody_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Blockchain Verification
        story.append(Paragraph("BLOCKCHAIN VERIFICATION DETAILS", heading_style))
        
        verification_text = f"""
        <b>Network:</b> Ethereum Mainnet
        <br/>
        <b>Data Source:</b> Etherscan API (public blockchain data)
        <br/>
        <b>Verification Method:</b> Public blockchain explorer API
        <br/>
        <b>Data Timestamp:</b> {self.timestamp.isoformat()}
        <br/>
        <b>Analysis Tool:</b> OPENCHAIN IR (Forensic Analysis Platform)
        <br/>
        <br/>
        The evidence presented in this report has been extracted directly from the immutable 
        Ethereum blockchain using publicly available API endpoints. All transactions are permanently 
        recorded and cannot be altered without consensus from the entire Ethereum network.
        """
        
        story.append(Paragraph(verification_text.strip(), styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Investigator Certification
        story.append(Paragraph("INVESTIGATOR CERTIFICATION", heading_style))
        
        cert_text = f"""
        I hereby certify that I have conducted a thorough forensic analysis of the above-mentioned 
        Ethereum address and that the findings presented in this report are accurate and complete 
        to the best of my knowledge and belief.
        <br/>
        <br/>
        <br/>
        Signature: ___________________________
        <br/>
        Date: {self.timestamp.strftime("%d-%m-%Y")}
        <br/>
        Investigator: {self.investigator_name}
        <br/>
        Department: {self.department}
        """
        
        story.append(Paragraph(cert_text.strip(), styles['Normal']))
        
        # Build PDF
        doc.build(story)
        return output_file
    
    def create_evidence_report(self, summary, patterns, output_file="exports/Evidence_Report.pdf"):
        """Create detailed evidence report with pattern analysis"""
        os.makedirs("exports", exist_ok=True)
        
        doc = SimpleDocTemplate(output_file, pagesize=A4, rightMargin=0.5*inch, leftMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=1
        )
        
        story.append(Paragraph("DIGITAL EVIDENCE REPORT", title_style))
        story.append(Paragraph(f"Case ID: {self.case_id} | Date: {self.timestamp.strftime('%Y-%m-%d')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Pattern Evidence
        story.append(Paragraph("DETECTED PATTERNS AND INDICATORS", styles['Heading2']))
        
        pattern_list = summary.get('patterns_detected', [])
        if pattern_list:
            for i, pattern in enumerate(pattern_list, 1):
                pattern_text = f"<b>{i}. {pattern.upper()}</b>"
                story.append(Paragraph(pattern_text, styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
        else:
            story.append(Paragraph("No significant patterns detected.", styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Transaction Summary
        story.append(Paragraph("TRANSACTION SUMMARY", styles['Heading2']))
        
        tx_data = [
            ["Category", "Count", "Total ETH", "Average"],
            ["Inbound Transactions", str(summary.get('inbound_count', 0)), 
            f"{summary.get('total_received', 0):.4f}", 
            f"{summary.get('total_received', 0) / max(summary.get('inbound_count', 1), 1):.4f}"],
            ["Outbound Transactions", str(summary.get('outbound_count', 0)), 
            f"{summary.get('total_sent', 0):.4f}", 
            f"{summary.get('total_sent', 0) / max(summary.get('outbound_count', 1), 1):.4f}"],
        ]
        
        tx_table = Table(tx_data, colWidths=[2*inch, 1.3*inch, 1.5*inch, 1.2*inch])
        tx_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        
        story.append(tx_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Recommendations
        story.append(Paragraph("INVESTIGATIVE RECOMMENDATIONS", styles['Heading2']))
        
        recommendations = []
        if summary.get('risk_score', 0) > 70:
            recommendations.append("• PRIORITY: High-risk entity - Recommend immediate further investigation")
        if 'consolidation' in summary.get('patterns_detected', []):
            recommendations.append("• Investigate fund consolidation patterns - may indicate mixing or layering")
        if 'rapid_succession' in summary.get('patterns_detected', []):
            recommendations.append("• Monitor rapid transaction succession - typical of automated laundering")
        if 'high_frequency' in summary.get('patterns_detected', []):
            recommendations.append("• High-frequency trading pattern detected - may require enhanced monitoring")
        
        if not recommendations:
            recommendations.append("• Continue routine monitoring")
            recommendations.append("• Re-assess if new patterns emerge")
        
        for rec in recommendations:
            story.append(Paragraph(rec, styles['Normal']))
        
        doc.build(story)
        return output_file
