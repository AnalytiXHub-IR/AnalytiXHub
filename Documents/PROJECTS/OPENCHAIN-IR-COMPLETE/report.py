from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import textwrap
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import os

def create_transaction_chart(summary):
    """Creates a visualization of transaction flow."""
    try:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        
        # Pie chart - Inflow vs Outflow
        flows = [summary.get('total_volume_in', 0), summary.get('total_volume_out', 0)]
        labels = [f"Inflow\n{flows[0]:.2f} ETH", f"Outflow\n{flows[1]:.2f} ETH"]
        colors_pie = ['#2ecc71', '#e74c3c']
        ax1.pie(flows, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Transaction Flow Distribution', fontweight='bold')
        
        # Risk score gauge
        risk_score = summary.get('risk_score', 0)
        ax2.barh(['Risk Score'], [risk_score], color='#e74c3c' if risk_score > 50 else '#f39c12' if risk_score > 30 else '#2ecc71')
        ax2.set_xlim(0, 100)
        ax2.set_xlabel('Risk Level (/100)')
        ax2.text(risk_score/2, 0, f'{risk_score}/100', ha='center', va='center', color='white', fontweight='bold')
        
        fig.tight_layout()
        chart_path = "exports/transaction_chart.png"
        fig.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return chart_path
    except Exception as e:
        print(f"[CHART ERROR] {e}")
        return None

def create_address_distribution_chart(summary):
    """Creates visualization of top senders and receivers."""
    try:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # Top victims (inbound)
        top_victims = summary.get('top_victims', [])
        if top_victims:
            addrs = [addr[:12] + "..." for addr, _ in top_victims[:5]]
            values = [val for _, val in top_victims[:5]]
            ax1.barh(addrs, values, color='#3498db')
            ax1.set_xlabel('ETH Received')
            ax1.set_title('Top 5 Inbound Addresses', fontweight='bold')
        
        # Top suspects (outbound)
        top_suspects = summary.get('top_suspects', [])
        if top_suspects:
            addrs = [addr[:12] + "..." for addr, _ in top_suspects[:5]]
            values = [val for _, val in top_suspects[:5]]
            ax2.barh(addrs, values, color='#e74c3c')
            ax2.set_xlabel('ETH Sent')
            ax2.set_title('Top 5 Outbound Addresses', fontweight='bold')
        
        fig.tight_layout()
        chart_path = "exports/address_distribution.png"
        fig.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return chart_path
    except Exception as e:
        print(f"[CHART ERROR] {e}")
        return None

def create_pdf(summary, findings, narrative, source):
    """Creates comprehensive forensic audit report PDF."""
    os.makedirs("exports", exist_ok=True)
    
    # Generate charts
    chart1 = create_transaction_chart(summary)
    chart2 = create_address_distribution_chart(summary)
    
    # Create PDF
    pdf_path = "exports/forensic_report.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        borderColor=colors.HexColor('#3498db'),
        borderWidth=2,
        borderPadding=5
    )
    
    # Title
    story.append(Paragraph("OPENCHAIN IR - FORENSIC AUDIT REPORT", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # === EXECUTIVE SUMMARY ===
    story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
    
    summary_data = [
        ["Metric", "Value"],
        ["Total Transactions", str(summary.get('total_transactions', 0))],
        ["Total Inflow", f"{summary.get('total_volume_in', 0):.4f} ETH"],
        ["Total Outflow", f"{summary.get('total_volume_out', 0):.4f} ETH"],
        ["Net Flow", f"{summary.get('net_flow', 0):.4f} ETH"],
        ["Unique Senders", str(summary.get('unique_senders', 0))],
        ["Unique Receivers", str(summary.get('unique_receivers', 0))],
        ["Avg Transaction", f"{summary.get('avg_transaction_value', 0):.4f} ETH"],
        ["Risk Score", f"{summary.get('risk_score', 0)}/100"],
        ["Analysis Period", f"{summary.get('start_date', 'N/A')} to {summary.get('end_date', 'N/A')}"],
    ]
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.2*inch))
    
    # === VISUAL ANALYSIS ===
    if chart1:
        story.append(Paragraph("TRANSACTION FLOW ANALYSIS", heading_style))
        img1 = Image(chart1, width=6*inch, height=2.4*inch)
        story.append(img1)
        story.append(Spacer(1, 0.2*inch))
    
    if chart2:
        story.append(Paragraph("ADDRESS DISTRIBUTION", heading_style))
        img2 = Image(chart2, width=6*inch, height=2.4*inch)
        story.append(img2)
        story.append(Spacer(1, 0.2*inch))
    
    # === PATTERN DETECTION ===
    story.append(PageBreak())
    story.append(Paragraph("PATTERN ANALYSIS", heading_style))
    
    patterns = summary.get('patterns', {})
    pattern_text = "<b>Detected Patterns:</b><br/>"
    
    pattern_descriptions = {
        'rapid_succession': 'Rapid succession of transactions (within 1 minute)',
        'high_frequency_wallet': 'High frequency transaction wallet (>50 transactions)',
        'mixing_service_suspicion': 'Possible mixing service behavior (many inputs, few outputs)',
        'consolidation_pattern': 'Consolidation pattern detected (many small inputs, large outputs)',
        'layering_pattern': 'Layering pattern detected (potential AML obfuscation)',
    }
    
    patterns_detected = False
    for pattern_key, pattern_desc in pattern_descriptions.items():
        if patterns.get(pattern_key, False):
            pattern_text += f"• {pattern_desc}<br/>"
            patterns_detected = True
    
    if not patterns_detected:
        pattern_text += "• No major patterns detected<br/>"
    
    if patterns.get('dust_transactions', []):
        pattern_text += f"• {len(patterns['dust_transactions'])} dust transactions (very small amounts)<br/>"
    
    if patterns.get('round_amounts', []):
        pattern_text += f"• {len(patterns['round_amounts'])} round-amount transactions detected<br/>"
    
    story.append(Paragraph(pattern_text, styles['Normal']))
    story.append(Spacer(1, 0.15*inch))
    
    # === RISK ASSESSMENT ===
    story.append(Paragraph("RISK ASSESSMENT", heading_style))
    
    risk_score = summary.get('risk_score', 0)
    if risk_score >= 70:
        risk_level = "🔴 CRITICAL"
    elif risk_score >= 50:
        risk_level = "🟠 HIGH"
    elif risk_score >= 30:
        risk_level = "🟡 MEDIUM"
    else:
        risk_level = "🟢 LOW"
    
    risk_text = f"<b>Overall Risk Level:</b> {risk_level} ({risk_score}/100)<br/><br/>"
    risk_text += "<b>Risk Factors:</b><br/>"
    
    for factor in summary.get('risk_factors', []):
        risk_text += f"• {factor}<br/>"
    
    story.append(Paragraph(risk_text, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # === VICTIMS LIST ===
    story.append(PageBreak())
    story.append(Paragraph("INBOUND ANALYSIS (VICTIMS)", heading_style))
    
    top_victims = summary.get('top_victims', [])
    if top_victims:
        victim_data = [["Address (First 16 Chars)", "Amount (ETH)", "Status"]]
        for addr, val in top_victims[:10]:
            status = "🚨 Large Transfer" if val > summary.get('avg_transaction_value', 0) * 5 else "Normal"
            victim_data.append([addr[:16] + "...", f"{val:.4f}", status])
        
        victim_table = Table(victim_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        victim_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
        ]))
        story.append(victim_table)
    else:
        story.append(Paragraph("No inbound transactions detected.", styles['Normal']))
    
    story.append(Spacer(1, 0.2*inch))
    
    # === SUSPECTS LIST ===
    story.append(Paragraph("OUTBOUND ANALYSIS (SUSPECTS)", heading_style))
    
    top_suspects = summary.get('top_suspects', [])
    if top_suspects:
        suspect_data = [["Address (First 16 Chars)", "Amount (ETH)", "Status"]]
        for addr, val in top_suspects[:10]:
            status = "⚠️ Large Transfer" if val > summary.get('avg_transaction_value', 0) * 5 else "Normal"
            suspect_data.append([addr[:16] + "...", f"{val:.4f}", status])
        
        suspect_table = Table(suspect_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        suspect_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fadbd8')]),
        ]))
        story.append(suspect_table)
    else:
        story.append(Paragraph("No outbound transactions detected.", styles['Normal']))
    
    story.append(Spacer(1, 0.2*inch))
    
    # === CASH OUT ALERTS ===
    if summary.get('cash_out_points'):
        story.append(Paragraph("⚠️ CASH-OUT ALERTS", heading_style))
        alert_text = ""
        for attempt in summary['cash_out_points']:
            alert_text += f"• {attempt}<br/>"
        story.append(Paragraph(alert_text, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # === AI ANALYSIS ===
    story.append(PageBreak())
    story.append(Paragraph("AI INVESTIGATIVE NARRATIVE", heading_style))
    
    # narrative could be a string or dict depending on gemini function
    if isinstance(narrative, dict):
        narrative_text = narrative.get('narrative', '')
        # Check for error markers and use fallback if found
        if not narrative_text or "[Analysis failed" in narrative_text:
            from gemini import generate_fallback_narrative
            narrative_text = generate_fallback_narrative(summary)
        
        if narrative_text:
            story.append(Paragraph(narrative_text, styles['Normal']))
        if narrative.get('pattern_analysis') and "[Analysis" not in narrative.get('pattern_analysis', ''):
            story.append(Spacer(1, 0.15*inch))
            story.append(Paragraph("<b>Pattern Analysis:</b>", styles['Heading3']))
            story.append(Paragraph(narrative['pattern_analysis'], styles['Normal']))
        if narrative.get('risk_assessment') and "[Analysis" not in narrative.get('risk_assessment', ''):
            story.append(Spacer(1, 0.15*inch))
            story.append(Paragraph("<b>Risk Assessment:</b>", styles['Heading3']))
            story.append(Paragraph(narrative['risk_assessment'], styles['Normal']))
    else:
        # Handle string format or error cases
        if not narrative or "[Analysis failed" in str(narrative):
            from gemini import generate_fallback_narrative
            narrative = generate_fallback_narrative(summary)
        clean_text = str(narrative).replace("**", "").replace("#", "")
        story.append(Paragraph(clean_text, styles['Normal']))
    
    story.append(Spacer(1, 0.3*inch))
    
    # === FOOTER ===
    story.append(Paragraph("___" * 30, styles['Normal']))
    story.append(Paragraph(f"<i>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Source: {source}</i>", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    print(f"[✓] Report generated: {pdf_path}")

