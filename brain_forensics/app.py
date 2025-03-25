#!/usr/bin/env python3
"""
Flask web server for the Social Media Forensics tool
"""

import os
import sys
import json
import base64
import argparse
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from brain_forensics.api.web_search import WebSearchAPI
from brain_forensics.analysis.sentiment import SentimentAnalyzer
from brain_forensics.analysis.network import NetworkAnalyzer
from brain_forensics.reports.report_generator import ForensicReportGenerator
from brain_forensics import config

app = Flask(__name__, static_folder='web')
CORS(app)  # Enable Cross-Origin Resource Sharing

# Initialize components
search_api = WebSearchAPI()
sentiment_analyzer = SentimentAnalyzer()
network_analyzer = NetworkAnalyzer()
report_generator = ForensicReportGenerator()

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('web', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('web', path)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """API endpoint to analyze a user's social media presence"""
    data = request.json
    
    if not data or 'username' not in data:
        return jsonify({'error': 'Username is required'}), 400
    
    username = data['username']
    platform = data.get('platform')
    
    try:
        # Step 1: Collect social media data
        search_results = search_api.search(username, platform=platform)
        result_data = search_results.get('results', [])
        
        if not result_data:
            return jsonify({'error': f'No social media data found for user: {username}'}), 404
        
        # Step 2: Analyze sentiment and detect anomalies
        analysis_results = []
        
        for platform_data in result_data:
            # Analyze sentiment for each platform
            platform_analysis = sentiment_analyzer.analyze_user_posts(platform_data)
            
            # Detect anomalies
            anomalies = sentiment_analyzer.detect_anomalies(platform_data)
            platform_analysis['anomalies'] = anomalies
            
            analysis_results.append(platform_analysis)
        
        # Step 3: Perform network analysis
        # For prototype, we'll simulate additional users
        simulated_users = []
        
        # Generate 3 random users for each platform to create a network
        for platform_data in result_data:
            platform = platform_data.get('platform', '')
            for i in range(3):
                simulated_username = f"user{i}_{platform}"
                simulated_result = search_api.search(simulated_username, platform=platform)
                if 'results' in simulated_result and simulated_result['results']:
                    simulated_users.extend(simulated_result['results'])
        
        # Combine real and simulated users for network analysis
        all_users = result_data + simulated_users
        
        # Visualize network
        network_vis_path = network_analyzer.visualize_network(all_users)
        
        # Detect communities
        communities = network_analyzer.detect_communities()
        
        # Detect influential nodes
        influential_nodes = network_analyzer.detect_influential_nodes()
        
        # Detect suspicious connections
        suspicious_connections = network_analyzer.detect_suspicious_connections()
        
        # Read image file for network visualization to include in response
        network_image = None
        if network_vis_path and os.path.exists(network_vis_path):
            with open(network_vis_path, 'rb') as f:
                image_data = f.read()
                network_image = base64.b64encode(image_data).decode('utf-8')
        
        # Step 4: Generate comprehensive report
        # Use the first platform's data for the main report
        main_platform_data = result_data[0]
        main_analysis = analysis_results[0]
        
        network_results = {
            'visualization_path': network_vis_path,
            'communities': communities,
            'influential_nodes': influential_nodes,
            'suspicious_connections': suspicious_connections
        }
        
        report_path = report_generator.generate_report(
            main_platform_data,
            main_analysis,
            network_results
        )
        
        # Format response data
        response = {
            'username': username,
            'platform': main_platform_data.get('platform', ''),
            'profile': main_platform_data.get('profile', {}),
            'sentiment_analysis': {
                'average_sentiment': main_analysis.get('average_sentiment', 0),
                'sentiment_distribution': main_analysis.get('sentiment_distribution', {}),
                'top_keywords': main_analysis.get('top_keywords', [])
            },
            'anomalies': main_analysis.get('anomalies', []),
            'network_analysis': {
                'image': network_image,
                'influential_nodes': influential_nodes[:5] if influential_nodes else [],
                'suspicious_connections': suspicious_connections[:5] if suspicious_connections else []
            },
            'report_path': report_path
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/<path:filename>')
def get_report(filename):
    """Serve generated report files"""
    reports_dir = config.REPORTS_DIR
    return send_file(os.path.join(reports_dir, filename))

def main():
    """Run the Flask application"""
    parser = argparse.ArgumentParser(description='Start the Social Media Forensics web server')
    parser.add_argument('--port', type=int, help='Port to run the server on (default: try 8080, 8000, etc.)')
    args = parser.parse_args()

    os.makedirs('web', exist_ok=True)
    
    if args.port:
        try:
            print(f"\nStarting server on specified port {args.port}...")
            app.run(debug=True, host='0.0.0.0', port=args.port)
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"Error: Port {args.port} is already in use.")
                if args.port == 5000:
                    print("Note: On macOS, port 5000 is often used by AirPlay Receiver.")
                    print("To fix: Go to System Settings -> General -> AirDrop & Handoff -> Turn off 'AirPlay Receiver'")
            else:
                print(f"Error starting server: {e}")
            sys.exit(1)
        return

    # Try different ports, starting with higher ports first to avoid system ports
    ports = [8080, 8000, 3000, 5000]
    
    for port in ports:
        try:
            print(f"\nAttempting to start server on port {port}...")
            app.run(debug=True, host='0.0.0.0', port=port)
            break
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"Port {port} is already in use.")
                if port == 5000:
                    print("Note: On macOS, port 5000 is often used by AirPlay Receiver.")
                    print("To fix: Go to System Settings -> General -> AirDrop & Handoff -> Turn off 'AirPlay Receiver'")
                continue
            else:
                print(f"Error starting server on port {port}: {e}")
                continue
    else:
        print("\nFailed to find an available port. Please try:")
        print("1. Using a specific port with: python app.py --port <port_number>")
        print("2. Checking and stopping other running services")
        print("3. Disabling AirPlay Receiver if you're on macOS")
        sys.exit(1)

if __name__ == '__main__':
    main() 