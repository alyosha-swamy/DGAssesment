#!/usr/bin/env python3
"""
Social Media Forensics Application

This script runs the complete forensic analysis pipeline:
1. Search for user data on social media
2. Analyze sentiment and detect anomalies
3. Perform network analysis
4. Generate a comprehensive forensic report
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime

from api import WebSearchAPI
from analysis import SentimentAnalyzer, NetworkAnalyzer
from reports import ForensicReportGenerator
import config

def analyze_user(username, platforms=None, output_dir=None):
    """
    Run a complete forensic analysis on a user's social media presence
    
    Args:
        username (str): Username to analyze
        platforms (list): Specific platforms to analyze (None for all)
        output_dir (str): Output directory for reports
        
    Returns:
        str: Path to generated report
    """
    print(f"Starting forensic analysis for user: {username}")
    
    start_time = time.time()
    
    # Initialize components
    search_api = WebSearchAPI()
    sentiment_analyzer = SentimentAnalyzer()
    network_analyzer = NetworkAnalyzer()
    report_generator = ForensicReportGenerator()
    
    # Step 1: Collect social media data
    print("Collecting social media data...")
    search_results = search_api.search(username, platform=platforms[0] if platforms else None)
    
    # Extract results data
    result_data = search_results.get('results', [])
    
    if not result_data:
        print(f"No social media data found for user: {username}")
        return None
        
    # Step 2: Analyze sentiment and detect anomalies
    print("Analyzing sentiment and detecting anomalies...")
    analysis_results = []
    
    for platform_data in result_data:
        # Analyze sentiment for each platform
        platform_analysis = sentiment_analyzer.analyze_user_posts(platform_data)
        
        # Detect anomalies
        anomalies = sentiment_analyzer.detect_anomalies(platform_data)
        platform_analysis['anomalies'] = anomalies
        
        analysis_results.append(platform_analysis)
    
    # Step 3: Perform network analysis if we have multiple users/platforms
    print("Performing network analysis...")
    # For prototype, we'll simulate additional users
    simulated_users = []
    
    # Generate 3-5 random users for each platform to create a network
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
    
    network_results = {
        'visualization_path': network_vis_path,
        'communities': communities,
        'influential_nodes': influential_nodes,
        'suspicious_connections': suspicious_connections
    }
    
    # Step 4: Generate comprehensive report
    print("Generating forensic report...")
    
    # Use the first platform's data for the main report
    main_platform_data = result_data[0]
    main_analysis = analysis_results[0]
    
    report_path = report_generator.generate_report(
        main_platform_data,
        main_analysis,
        network_results
    )
    
    # Print completion info
    elapsed_time = time.time() - start_time
    print(f"Analysis completed in {elapsed_time:.2f} seconds")
    print(f"Report saved to: {report_path}")
    
    return report_path

def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description="Social Media Forensics Tool")
    parser.add_argument("username", help="Username to analyze")
    parser.add_argument("--platform", choices=config.PLATFORMS, help="Specific platform to analyze")
    parser.add_argument("--output", help="Output directory for reports")
    
    args = parser.parse_args()
    
    # Run analysis
    platforms = [args.platform] if args.platform else None
    report_path = analyze_user(args.username, platforms=platforms, output_dir=args.output)
    
    if report_path:
        print(f"Analysis complete. Report saved to: {report_path}")
    else:
        print("Analysis failed. No report generated.")
        sys.exit(1)

if __name__ == "__main__":
    main() 