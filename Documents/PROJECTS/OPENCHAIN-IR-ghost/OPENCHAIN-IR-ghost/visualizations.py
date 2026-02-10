"""
Advanced Visualizations for OPENCHAIN IR
Timeline, Sankey diagrams, and interactive charts
"""

import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
from datetime import datetime
import os

def create_timeline_visualization(txlist, root_address, output_file="exports/timeline.html"):
    """Create interactive timeline visualization of transactions"""
    os.makedirs("exports", exist_ok=True)
    
    events = []
    for tx in txlist:
        try:
            ts = int(tx.get("timeStamp", 0))
            frm = tx.get("from", "Unknown")
            to = tx.get("to", "Unknown")
            val = float(tx.get("value", 0)) / 1e18
            
            date = datetime.fromtimestamp(ts)
            
            # Determine event type
            if to.lower() == root_address.lower():
                event_type = "INBOUND"
                title = f"Received {val:.2f} ETH from {frm[:10]}..."
            elif frm.lower() == root_address.lower():
                event_type = "OUTBOUND"
                title = f"Sent {val:.2f} ETH to {to[:10]}..."
            else:
                continue
                
            events.append({
                "timestamp": date,
                "date_str": date.strftime("%Y-%m-%d %H:%M:%S"),
                "amount": val,
                "type": event_type,
                "from": frm,
                "to": to,
                "title": title
            })
        except:
            continue
    
    if not events:
        return None
    
    # Sort by timestamp
    events = sorted(events, key=lambda x: x["timestamp"])
    
    # Create plotly timeline
    fig = go.Figure()
    
    inbound = [e for e in events if e["type"] == "INBOUND"]
    outbound = [e for e in events if e["type"] == "OUTBOUND"]
    
    if inbound:
        fig.add_trace(go.Scatter(
            x=[e["timestamp"] for e in inbound],
            y=[e["amount"] for e in inbound],
            mode='markers+lines',
            name='Inbound',
            marker=dict(size=8, color='green', symbol='circle'),
            text=[e["title"] for e in inbound],
            hovertemplate='<b>%{text}</b><br>Amount: %{y:.4f} ETH<br>Time: %{x}<extra></extra>'
        ))
    
    if outbound:
        fig.add_trace(go.Scatter(
            x=[e["timestamp"] for e in outbound],
            y=[e["amount"] for e in outbound],
            mode='markers+lines',
            name='Outbound',
            marker=dict(size=8, color='red', symbol='diamond'),
            text=[e["title"] for e in outbound],
            hovertemplate='<b>%{text}</b><br>Amount: %{y:.4f} ETH<br>Time: %{x}<extra></extra>'
        ))
    
    fig.update_layout(
        title=f"Transaction Timeline for {root_address[:10]}...",
        xaxis_title="Date & Time",
        yaxis_title="Amount (ETH)",
        hovermode='x unified',
        height=500,
        template='plotly_white'
    )
    
    fig.write_html(output_file)
    return output_file

def create_sankey_diagram(summary, root_address, output_file="exports/sankey.html"):
    """Create Sankey diagram showing fund flow"""
    os.makedirs("exports", exist_ok=True)
    
    # Get top sources and destinations
    top_victims = summary.get("top_victims", [])[:5]
    top_suspects = summary.get("top_suspects", [])[:5]
    
    if not top_victims and not top_suspects:
        return None
    
    # Build nodes and links
    nodes = [root_address]
    node_colors = ["blue"]
    
    # Add victims (sources)
    for addr, amount in top_victims:
        nodes.append(addr)
        node_colors.append("green")
    
    # Add suspects (destinations)
    for addr, amount in top_suspects:
        nodes.append(addr)
        node_colors.append("red")
    
    # Build links
    source = []
    target = []
    value = []
    link_colors = []
    
    # Inbound
    for i, (addr, amount) in enumerate(top_victims):
        source.append(nodes.index(addr))
        target.append(0)  # root_address
        value.append(amount)
        link_colors.append("rgba(0,255,0,0.3)")
    
    # Outbound
    for i, (addr, amount) in enumerate(top_suspects):
        source.append(0)  # root_address
        target.append(nodes.index(addr))
        value.append(amount)
        link_colors.append("rgba(255,0,0,0.3)")
    
    # Create Sankey
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=[addr[:10] + "..." for addr in nodes],
            color=node_colors
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_colors
        )
    )])
    
    fig.update_layout(
        title=f"Fund Flow Sankey Diagram - {root_address[:10]}...",
        font=dict(size=10),
        height=600,
        template='plotly_white'
    )
    
    fig.write_html(output_file)
    return output_file

def create_heatmap_visualization(txlist, root_address, output_file="exports/heatmap.png"):
    """Create heatmap of transaction activity by day and hour"""
    os.makedirs("exports", exist_ok=True)
    
    import numpy as np
    from datetime import datetime
    
    # Create matrix [day_of_week][hour]
    activity_matrix = np.zeros((7, 24))
    
    for tx in txlist:
        try:
            ts = int(tx.get("timeStamp", 0))
            date = datetime.fromtimestamp(ts)
            day = date.weekday()  # 0-6
            hour = date.hour  # 0-23
            activity_matrix[day, hour] += 1
        except:
            continue
    
    if activity_matrix.sum() == 0:
        return None
    
    fig, ax = plt.subplots(figsize=(12, 6))
    im = ax.imshow(activity_matrix, cmap='YlOrRd', aspect='auto')
    
    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('Day of Week')
    ax.set_title(f'Transaction Activity Heatmap - {root_address[:10]}...')
    
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    ax.set_yticks(range(7))
    ax.set_yticklabels(days)
    ax.set_xticks(range(0, 24, 2))
    
    plt.colorbar(im, ax=ax, label='Number of Transactions')
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_file

def create_network_hops_visualization(summary, output_file="exports/network_hops.html"):
    """Visualize network hops and fund routing"""
    os.makedirs("exports", exist_ok=True)
    
    top_victims = summary.get("top_victims", [])
    top_suspects = summary.get("top_suspects", [])
    
    # Create network graph
    fig = go.Figure()
    
    x_pos = [0]  # Root in center
    y_pos = [0]
    labels = ["ROOT"]
    colors = ["blue"]
    
    # Arrange in circle
    import math
    total = len(top_victims) + len(top_suspects)
    angle_step = 2 * math.pi / max(total, 1)
    
    # Add victims
    for i, (addr, amount) in enumerate(top_victims):
        angle = i * angle_step
        x_pos.append(2 * math.cos(angle))
        y_pos.append(2 * math.sin(angle))
        labels.append(f"Victim {i+1}\n({amount:.2f} ETH)")
        colors.append("green")
    
    # Add suspects
    for i, (addr, amount) in enumerate(top_suspects):
        angle = (i + len(top_victims)) * angle_step
        x_pos.append(2 * math.cos(angle))
        y_pos.append(2 * math.sin(angle))
        labels.append(f"Suspect {i+1}\n({amount:.2f} ETH)")
        colors.append("red")
    
    fig.add_trace(go.Scatter(
        x=x_pos, y=y_pos,
        mode='markers+text',
        text=labels,
        textposition="top center",
        marker=dict(size=20, color=colors),
        hoverinfo='text'
    ))
    
    # Add edges
    for i, (addr, amount) in enumerate(top_victims):
        fig.add_trace(go.Scatter(
            x=[0, x_pos[i+1]], y=[0, y_pos[i+1]],
            mode='lines',
            line=dict(color='green', width=1),
            hoverinfo='skip',
            showlegend=False
        ))
    
    for i, (addr, amount) in enumerate(top_suspects):
        fig.add_trace(go.Scatter(
            x=[0, x_pos[len(top_victims)+i+1]], y=[0, y_pos[len(top_victims)+i+1]],
            mode='lines',
            line=dict(color='red', width=1),
            hoverinfo='skip',
            showlegend=False
        ))
    
    fig.update_layout(
        title="Network Hops Visualization",
        showlegend=False,
        hovermode='closest',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white'
    )
    
    fig.write_html(output_file)
    return output_file
