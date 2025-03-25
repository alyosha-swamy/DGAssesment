#!/usr/bin/env python3
"""
Social Media Forensics Dashboard

A web dashboard to visualize forensic analysis results
"""

import os
import sys
import json
import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import networkx as nx
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from api import WebSearchAPI
from analysis import SentimentAnalyzer, NetworkAnalyzer

# Initialize the dashboard
app = dash.Dash(__name__, 
                title="Social Media Forensics Dashboard",
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)

# Define the layout
app.layout = html.Div([
    # Header
    html.H1("Social Media Forensics Dashboard"),
    html.P("Investigate digital footprints across social media platforms"),
    
    # Search Controls
    html.Div([
        html.H2("User Search"),
        dcc.Input(
            id="username-input",
            type="text",
            placeholder="Enter username to analyze",
            style={"width": "300px", "marginRight": "10px"}
        ),
        dcc.Dropdown(
            id="platform-dropdown",
            options=[
                {"label": platform.capitalize(), "value": platform}
                for platform in config.PLATFORMS
            ],
            placeholder="Select platform (optional)",
            style={"width": "200px", "display": "inline-block", "marginRight": "10px"}
        ),
        html.Button("Analyze", id="submit-button", style={"marginRight": "10px"}),
        html.Div(id="loading-output", style={"display": "inline-block"})
    ], style={"marginBottom": "20px", "padding": "20px", "backgroundColor": "#f9f9f9"}),
    
    # Results Container (initially hidden)
    html.Div(id="results-container", style={"display": "none"}, children=[
        # User Profile Section
        html.Div([
            html.H2("User Profile"),
            html.Div(id="profile-info")
        ], style={"marginBottom": "20px", "padding": "20px", "backgroundColor": "#f9f9f9"}),
        
        # Sentiment Analysis Section
        html.Div([
            html.H2("Sentiment Analysis"),
            html.Div([
                html.Div([
                    dcc.Graph(id="sentiment-pie")
                ], style={"width": "33%", "display": "inline-block"}),
                html.Div([
                    dcc.Graph(id="sentiment-timeline")
                ], style={"width": "66%", "display": "inline-block"})
            ])
        ], style={"marginBottom": "20px", "padding": "20px", "backgroundColor": "#f9f9f9"}),
        
        # Network Analysis Section
        html.Div([
            html.H2("Network Analysis"),
            dcc.Graph(id="network-graph")
        ], style={"marginBottom": "20px", "padding": "20px", "backgroundColor": "#f9f9f9"}),
        
        # Anomalies Section
        html.Div([
            html.H2("Detected Anomalies"),
            html.Div(id="anomalies-container")
        ], style={"marginBottom": "20px", "padding": "20px", "backgroundColor": "#f9f9f9"}),
        
        # Keywords Section
        html.Div([
            html.H2("Top Keywords"),
            dcc.Graph(id="keyword-graph")
        ], style={"marginBottom": "20px", "padding": "20px", "backgroundColor": "#f9f9f9"})
    ])
])

# Define callback to handle analysis
@app.callback(
    [Output("results-container", "style"),
     Output("profile-info", "children"),
     Output("sentiment-pie", "figure"),
     Output("sentiment-timeline", "figure"),
     Output("network-graph", "figure"),
     Output("anomalies-container", "children"),
     Output("keyword-graph", "figure"),
     Output("loading-output", "children")],
    [Input("submit-button", "n_clicks")],
    [State("username-input", "value"),
     State("platform-dropdown", "value")]
)
def perform_analysis(n_clicks, username, platform):
    if not n_clicks or not username:
        # Default empty figures
        empty_pie = px.pie(names=["No Data"], values=[1], title="No Data")
        empty_line = px.line(title="No Data")
        empty_network = go.Figure()
        empty_network.update_layout(title="No Network Data")
        empty_bar = px.bar(title="No Keyword Data")
        
        return ({"display": "none"}, [], empty_pie, empty_line, empty_network, [], empty_bar, "")
    
    # Show loading
    loading_output = "Analyzing social media data..."
    
    try:
        # Initialize components
        search_api = WebSearchAPI()
        sentiment_analyzer = SentimentAnalyzer()
        network_analyzer = NetworkAnalyzer()
        
        # Step 1: Collect social media data
        search_results = search_api.search(username, platform=platform)
        result_data = search_results.get('results', [])
        
        if not result_data:
            return ({"display": "none"}, [], go.Figure(), go.Figure(), go.Figure(), 
                    html.Div("No data found for this user"), go.Figure(), 
                    "No data found for this user")
        
        # For simplicity, use first platform's data
        user_data = result_data[0]
        platform = user_data.get('platform', '')
        
        # Step 2: Analyze sentiment
        analysis_results = sentiment_analyzer.analyze_user_posts(user_data)
        anomalies = sentiment_analyzer.detect_anomalies(user_data)
        analysis_results['anomalies'] = anomalies
        
        # Create profile info
        profile = user_data.get('profile', {})
        profile_info = [
            html.Div([
                html.Strong("Username: "),
                html.Span(user_data.get('user', ''))
            ], style={"marginBottom": "5px"}),
            html.Div([
                html.Strong("Platform: "),
                html.Span(platform.capitalize())
            ], style={"marginBottom": "5px"}),
            html.Div([
                html.Strong("Followers: "),
                html.Span(str(profile.get('followers', 'Unknown')))
            ], style={"marginBottom": "5px"}),
            html.Div([
                html.Strong("Following: "),
                html.Span(str(profile.get('following', 'Unknown')))
            ], style={"marginBottom": "5px"}),
            html.Div([
                html.Strong("Account Created: "),
                html.Span(profile.get('created_date', 'Unknown'))
            ], style={"marginBottom": "5px"}),
            html.Div([
                html.Strong("Verified: "),
                html.Span("Yes" if profile.get('verified', False) else "No")
            ], style={"marginBottom": "5px"})
        ]
        
        if profile.get('is_suspicious', False):
            profile_info.append(
                html.Div("⚠️ Potentially Suspicious Account", 
                         style={"color": "red", "fontWeight": "bold", "marginTop": "10px"})
            )
        
        # Create sentiment pie chart
        sentiment_dist = analysis_results.get('sentiment_distribution', {})
        sentiment_df = pd.DataFrame({
            'sentiment': list(sentiment_dist.keys()),
            'count': list(sentiment_dist.values())
        })
        sentiment_pie = px.pie(
            sentiment_df, 
            names='sentiment', 
            values='count',
            color='sentiment',
            color_discrete_map={
                'positive': '#2ecc71',
                'neutral': '#3498db',
                'negative': '#e74c3c'
            },
            title="Sentiment Distribution"
        )
        
        # Create sentiment timeline
        posts = user_data.get('posts', [])
        timeline_data = []
        
        for post in posts:
            sentiment_score = post.get('sentiment_analysis', {}).get('sentiment_score', 0)
            timestamp = post.get('timestamp', 0)
            date = datetime.fromtimestamp(timestamp)
            
            timeline_data.append({
                'date': date,
                'sentiment': sentiment_score,
                'content': post.get('content', '')[:50] + '...' if len(post.get('content', '')) > 50 else post.get('content', '')
            })
        
        timeline_df = pd.DataFrame(timeline_data)
        if not timeline_df.empty:
            timeline_df = timeline_df.sort_values('date')
            
            sentiment_timeline = px.line(
                timeline_df,
                x='date',
                y='sentiment',
                title="Sentiment Over Time",
                hover_data=['content']
            )
            
            # Add a horizontal line at 0
            sentiment_timeline.add_shape(
                type="line",
                x0=timeline_df['date'].min(),
                y0=0,
                x1=timeline_df['date'].max(),
                y1=0,
                line=dict(color="gray", width=1, dash="dash")
            )
        else:
            sentiment_timeline = px.line(title="No Timeline Data")
        
        # Create network graph
        # For prototype, we'll simulate additional users
        simulated_users = []
        
        # Generate 3 random users for the same platform
        for i in range(3):
            simulated_username = f"user{i}_{platform}"
            simulated_result = search_api.search(simulated_username, platform=platform)
            if 'results' in simulated_result and simulated_result['results']:
                simulated_users.extend(simulated_result['results'])
        
        # Combine real and simulated users for network analysis
        all_users = [user_data] + simulated_users
        
        # Build graph
        network_analyzer._build_graph_from_user_data(all_users)
        graph = network_analyzer.graph
        
        # Convert NetworkX graph to Plotly graph
        pos = nx.spring_layout(graph, seed=42)
        
        edge_trace = go.Scatter(
            x=[],
            y=[],
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')
        
        for edge in graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace['x'] += (x0, x1, None)
            edge_trace['y'] += (y0, y1, None)
        
        node_trace = go.Scatter(
            x=[],
            y=[],
            text=[],
            mode='markers',
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='YlGnBu',
                size=[],
                color=[],
                colorbar=dict(
                    thickness=15,
                    title='Node Type',
                    xanchor='left',
                    titleside='right'
                )
            )
        )
        
        for node in graph.nodes():
            x, y = pos[node]
            node_trace['x'] += (x,)
            node_trace['y'] += (y,)
            
            # Size based on followers
            followers = graph.nodes[node].get('followers', 100)
            size = max(10, min(50, 10 * (1 + followers / 10000)))
            node_trace['marker']['size'] += (size,)
            
            # Color based on suspiciousness
            is_suspicious = graph.nodes[node].get('is_suspicious', False)
            color = 1 if is_suspicious else 0
            node_trace['marker']['color'] += (color,)
            
            # Hover text
            node_trace['text'] += (
                f"User: {graph.nodes[node].get('username', '')}<br>"
                f"Platform: {graph.nodes[node].get('platform', '')}<br>"
                f"Followers: {followers}<br>"
                f"Suspicious: {'Yes' if is_suspicious else 'No'}"
            ,)
        
        network_fig = go.Figure(data=[edge_trace, node_trace],
                         layout=go.Layout(
                            title='User Connection Network',
                            titlefont=dict(size=16),
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=20,l=5,r=5,t=40),
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                        ))
        
        # Create anomalies list
        anomalies_list = []
        
        if anomalies:
            for i, anomaly in enumerate(anomalies):
                severity_color = {
                    'high': 'red',
                    'medium': 'orange',
                    'low': 'blue'
                }.get(anomaly.get('severity', 'medium'), 'gray')
                
                anomalies_list.append(
                    html.Div([
                        html.H4(f"Anomaly {i+1}: {anomaly.get('type', 'Unknown')}"),
                        html.P(anomaly.get('description', '')),
                        html.P([
                            html.Strong("Severity: "),
                            html.Span(anomaly.get('severity', 'medium').upper(), 
                                     style={"color": severity_color, "fontWeight": "bold"})
                        ]),
                    ], style={"border": "1px solid #ddd", "borderRadius": "5px", 
                              "padding": "10px", "marginBottom": "10px"})
                )
        else:
            anomalies_list.append(html.Div("No anomalies detected", style={"fontStyle": "italic"}))
        
        # Create keywords graph
        keywords = analysis_results.get('top_keywords', [])
        keyword_freq = {k: 10 for k in keywords}  # Dummy frequencies for prototype
        
        keyword_df = pd.DataFrame({
            'keyword': list(keyword_freq.keys()),
            'frequency': list(keyword_freq.values())
        }).sort_values('frequency', ascending=False)
        
        if not keyword_df.empty:
            keyword_graph = px.bar(
                keyword_df,
                x='keyword',
                y='frequency',
                title="Top Keywords",
                color='frequency',
                color_continuous_scale='Viridis'
            )
        else:
            keyword_graph = px.bar(title="No Keyword Data")
        
        return ({"display": "block"}, profile_info, sentiment_pie, sentiment_timeline, 
                network_fig, anomalies_list, keyword_graph, "")
    
    except Exception as e:
        return ({"display": "none"}, [], go.Figure(), go.Figure(), go.Figure(), 
                html.Div(f"Error: {str(e)}"), go.Figure(), f"Error: {str(e)}")

def main():
    """Run the dashboard"""
    app.run_server(debug=True, host='0.0.0.0', port=8050)

if __name__ == '__main__':
    main() 