#!/usr/bin/env python3
"""
Flask Web Server for the Social Media Forensic Analysis Tool (SMFAT)
Refactored to align with forensic workflow and case management.
"""

import os
import sys
import json
import base64
import argparse
import traceback
import hashlib
from datetime import datetime, timezone
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import re # Ensure re is imported
import time # Add import for time used in SimulatedCollector
import random # Add import for random used in SimulatedCollector

# --- Configuration and Path Setup ---
try:
    # First, try to import directly if this script is run from the same directory as config.py
    import config
except ImportError:
    try:
        # If run from a different directory, try the package import
        from brain_forensics import config
    except ImportError:
        # If run directly, try adding parent directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        try:
            from brain_forensics import config
        except ImportError:
            print("Error: Could not import config. Ensure brain_forensics package structure is correct.", file=sys.stderr)
            sys.exit(1)

# --- (Simulated) Module Imports ---
# These imports assume the new structure exists. We'll implement the logic later.
# For now, we will define placeholder functions within this file or use existing ones.

# Placeholder/Simulated Collection (replace with actual module later)
# from brain_forensics.collection.collector import SimulatedCollector
# search_api = SimulatedCollector() # Uses web search

# Placeholder/Simulated Preservation (replace with actual module later)
# from brain_forensics.preservation.preserver import DataPreserver
# data_preserver = DataPreserver()

# Analysis Modules (adapt existing ones later)
from analysis.sentiment import SentimentAnalyzer
from analysis.network import NetworkAnalyzer
sentiment_analyzer = SentimentAnalyzer()
network_analyzer = NetworkAnalyzer()

# Reporting Module (rewrite later)
from reports.report_generator import ForensicReportGenerator
report_generator = ForensicReportGenerator()

# --- Flask App Setup ---
app = Flask(__name__, static_folder='web')
CORS(app)  # Enable Cross-Origin Resource Sharing for UI interaction

# --- Helper Functions ---

def get_case_path(case_name):
    """Get the absolute path for a given case name."""
    # Basic sanitization to prevent directory traversal
    safe_case_name = os.path.basename(case_name)
    if not safe_case_name or safe_case_name == '.' or safe_case_name == '..':
        return None
    return os.path.join(config.CASES_DIR, safe_case_name)

def ensure_case_structure(case_path):
    """Create the necessary directory structure for a case."""
    if not case_path: return False
    try:
        os.makedirs(os.path.join(case_path, config.CASE_DATA_DIR_NAME), exist_ok=True)
        os.makedirs(os.path.join(case_path, config.CASE_METADATA_DIR_NAME), exist_ok=True)
        os.makedirs(os.path.join(case_path, config.CASE_ANALYSIS_DIR_NAME), exist_ok=True)
        os.makedirs(os.path.join(case_path, config.CASE_EXPORTS_DIR_NAME), exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating case structure for {case_path}: {e}", file=sys.stderr)
        return False

def calculate_hash(data):
    """Calculate SHA256 hash of JSON serializable data."""
    hasher = hashlib.sha256()
    # Ensure consistent serialization for hashing
    encoded = json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')
    hasher.update(encoded)
    return hasher.hexdigest()

def create_metadata(data_filename, data_hash, collection_details):
    """Create metadata dictionary for a collected data item."""
    return {
        "data_filename": data_filename,
        "collection_timestamp_utc": datetime.now(timezone.utc).strftime(config.TIMESTAMP_FORMAT),
        "hash_algorithm": config.HASH_ALGORITHM,
        "data_hash": data_hash,
        "collection_method": collection_details.get("method", "simulated_web_search"),
        "source_platform": collection_details.get("platform", "unknown"),
        "target_identifier": collection_details.get("target", "unknown"),
        "collection_parameters": collection_details.get("parameters", {})
    }

# --- Simulated Modules (Implement proper versions later) ---

# --- Web Search Function (Placeholder - Needs Integration with Tool) ---
def perform_web_search(query):
    """Placeholder function to simulate web search.
    In a real integration, this would call the available web search tool.
    Returns a list of simulated search result texts.
    """
    print(f"[Web Search Simulation] Querying: {query}")
    # Simulate results - replace with actual tool call
    time.sleep(0.5) # Simulate network delay
    results = [
        f"Result 1 for {query}: Found profile link on {query.split('site:')[1].split(' ')[0] if 'site:' in query else 'Platform'}. User posts about relevant topics.",
        f"Result 2 for {query}: User mentioned in an article related to the search target.",
        f"Result 3 for {query}: Another potential mention or related activity."
    ]
    return results[:config.MAX_SEARCH_RESULTS_PER_PLATFORM]

# --- Refined Simulated Collector ---
class SimulatedCollector:
    """Placeholder for data collection using web search tool simulation."""
    def collect_data(self, target, platforms):
        print(f"[Simulated Collection] Starting collection for target '{target}' on platforms: {platforms}")
        collected_items = []
        collection_timestamp = datetime.now(timezone.utc)

        for platform in platforms:
            if platform not in config.SUPPORTED_PLATFORMS:
                print(f"Warning: Skipping unsupported platform: {platform}")
                continue

            # Construct a search query (example)
            query = f'{target} site:{platform.lower()}.com'
            if platform == "X":
                query = f'{target} site:x.com OR site:twitter.com'
            
            print(f"[Simulated Collection] Searching {platform} with query: '{query}'")
            try:
                # --- Replace this with actual Web Search Tool Call --- 
                search_results = perform_web_search(query)
                # -----------------------------------------------------
                
                print(f"[Simulated Collection] Received {len(search_results)} results from {platform} search.")

                for i, result_text in enumerate(search_results):
                    # Simulate creating a structured data item from search result
                    item_id = f"{platform.lower()}_{target.replace(' ', '_')}_{collection_timestamp.strftime('%Y%m%d%H%M%S')}_{i}"
                    item_timestamp = time.time() - random.randint(0, 86400 * 7) # Random timestamp in last week
                    
                    # Simulate extracting URL (very basic)
                    url_match = re.search(r'https?://[\w\./-]+', result_text)
                    simulated_url = url_match.group(0) if url_match else f"https://{platform.lower()}.com/{target}/simulated_post_{i}"

                    item = {
                        "id": item_id,
                        "platform": platform,
                        "target": target, # The original search target
                        "collected_at_utc": collection_timestamp.strftime(config.TIMESTAMP_FORMAT),
                        "simulated_content": result_text, # Use search result as content
                        "simulated_timestamp_epoch": item_timestamp,
                        "simulated_timestamp_iso": datetime.fromtimestamp(item_timestamp, timezone.utc).strftime(config.TIMESTAMP_FORMAT),
                        "source_url": simulated_url, # Extracted or simulated URL
                        "collection_query": query # Store the query used
                    }
                    # Use 'simulated_content' for analysis later
                    item['content'] = item['simulated_content'] 
                    collected_items.append(item)
            except Exception as e:
                print(f"Error during simulated collection for {platform}: {e}", file=sys.stderr)
                traceback.print_exc()

        print(f"[Simulated Collection] Finished. Collected {len(collected_items)} items total.")
        return collected_items

# --- Refined Data Preserver ---
class DataPreserver:
    """Handles saving collected data, metadata, and logging for a case."""
    def preserve_data(self, case_name, collected_items, collection_details):
        case_path = get_case_path(case_name)
        if not case_path or not ensure_case_structure(case_path):
            raise ValueError(f"Invalid case name or failed to create structure: {case_name}")

        data_dir = os.path.join(case_path, config.CASE_DATA_DIR_NAME)
        meta_dir = os.path.join(case_path, config.CASE_METADATA_DIR_NAME)
        log_path = os.path.join(meta_dir, "forensic_log.jsonl") # Changed log name

        preserved_files_summary = []
        print(f"[Preservation] Starting preservation for {len(collected_items)} items in case '{case_name}'")

        # Log the start of the collection/preservation batch
        self._log_event(log_path, {
            "event_type": "BATCH_START",
            "case_name": case_name,
            "target": collection_details.get("target", "N/A"),
            "platforms": collection_details.get("platforms", []), 
            "item_count": len(collected_items)
        })

        for i, item in enumerate(collected_items):
            try:
                item_id = item.get("id", f"item_{i}_{int(time.time())}")
                data_filename = f"{item_id}.json"
                data_filepath = os.path.join(data_dir, data_filename)
                meta_filename = f"{item_id}_meta.json"
                meta_filepath = os.path.join(meta_dir, meta_filename)

                # 1. Save Data file
                with open(data_filepath, 'w', encoding='utf-8') as f:
                    json.dump(item, f, indent=4, ensure_ascii=False)
                print(f"  - Saved data: {data_filename}")

                # 2. Calculate Hash of the data file contents
                data_hash = calculate_hash(item) # Hash the structured data
                print(f"  - Calculated hash: {data_hash[:8]}...")

                # 3. Create Metadata file
                metadata = create_metadata(data_filename, data_hash, {
                    "platform": item.get("platform"),
                    "target": item.get("target"), # Original search target
                    "method": "simulated_web_search",
                    "collection_query": item.get("collection_query", "N/A"),
                    "source_url": item.get("source_url", "N/A"),
                    "parameters": collection_details.get("parameters", {}) # Overall parameters
                })

                # 4. Save Metadata file
                with open(meta_filepath, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=4, ensure_ascii=False)
                print(f"  - Saved metadata: {meta_filename}")

                # 5. Log Preservation Event per item
                self._log_event(log_path, {
                    "event_type": "ITEM_PRESERVATION",
                    "case_name": case_name,
                    "item_id": item_id,
                    "data_filename": data_filename,
                    "metadata_filename": meta_filename,
                    "data_hash": data_hash,
                    "source_url": item.get("source_url", "N/A")
                })

                preserved_files_summary.append({
                    "data_file": data_filename,
                    "metadata_file": meta_filename,
                    "hash": data_hash
                })
            except Exception as e:
                error_msg = f"Error preserving item {i} (ID: {item.get('id', 'N/A')}): {e}"
                print(error_msg, file=sys.stderr)
                traceback.print_exc()
                # Log error event
                self._log_event(log_path, {
                   "event_type": "ERROR",
                   "stage": "Preservation",
                   "item_index": i,
                   "item_id": item.get('id', 'N/A'),
                   "error_message": str(e)
                })
        
        # Log the end of the batch
        self._log_event(log_path, {
            "event_type": "BATCH_END",
            "case_name": case_name,
            "items_preserved_count": len(preserved_files_summary)
        })

        print(f"[Preservation] Finished. Preserved {len(preserved_files_summary)} items.")
        return preserved_files_summary

    def _log_event(self, log_path, event_data):
        """Append a structured event to the case log file."""
        try:
            base_event = {
                "log_timestamp_utc": datetime.now(timezone.utc).strftime(config.TIMESTAMP_FORMAT),
                "actor": config.REPORT_AUTHOR # Or a more specific system actor
            }
            full_event = {**base_event, **event_data}
            with open(log_path, 'a', encoding='utf-8') as log_file:
                log_file.write(json.dumps(full_event, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"Error writing to log file {log_path}: {e}", file=sys.stderr)

# Instantiate simulated components
collector = SimulatedCollector()
data_preserver = DataPreserver()


# --- API Endpoints ---

@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('web', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (CSS, JS)."""
    return send_from_directory('web', path)

@app.route('/api/cases', methods=['GET'])
def list_cases():
    """List existing forensic cases."""
    try:
        cases = [d for d in os.listdir(config.CASES_DIR)
                 if os.path.isdir(os.path.join(config.CASES_DIR, d))]
        return jsonify({"cases": cases})
    except Exception as e:
        print(f"Error listing cases: {e}", file=sys.stderr)
        return jsonify({"error": "Failed to list cases"}), 500

@app.route('/api/cases', methods=['POST'])
def create_case():
    """Create a new forensic case."""
    data = request.json
    case_name = data.get('case_name')

    if not case_name:
        return jsonify({"error": "'case_name' is required"}), 400

    case_path = get_case_path(case_name)
    if not case_path:
         return jsonify({"error": "Invalid 'case_name' provided"}), 400

    if os.path.exists(case_path):
        return jsonify({"error": f"Case '{case_name}' already exists"}), 409 # Conflict

    if ensure_case_structure(case_path):
        return jsonify({"message": f"Case '{case_name}' created successfully", "case_name": os.path.basename(case_path)}), 201
    else:
        return jsonify({"error": "Failed to create case structure"}), 500

@app.route('/api/cases/<case_name>/process', methods=['POST'])
def process_case(case_name):
    """Run the forensic process for a given case."""
    case_path = get_case_path(case_name)
    if not case_path or not os.path.isdir(case_path):
        return jsonify({"error": f"Case '{case_name}' not found"}), 404

    data = request.json
    target = data.get('target')
    platforms = data.get('platforms', []) # Expecting a list e.g., ["X", "Facebook"]

    if not target:
        return jsonify({"error": "'target' identifier is required"}), 400
    if not platforms or not isinstance(platforms, list):
        return jsonify({"error": "'platforms' must be a non-empty list"}), 400

    # Filter to only supported platforms
    valid_platforms = [p for p in platforms if p in config.SUPPORTED_PLATFORMS]
    if not valid_platforms:
        return jsonify({"error": f"None of the provided platforms are supported. Supported: {config.SUPPORTED_PLATFORMS}"}), 400

    collection_details = {
        "target": target,
        "platforms": valid_platforms,
        "parameters": data.get("collection_params", {}) # e.g., date range
    }

    try:
        # --- Step 1: Collection (Simulated) ---
        collected_data = collector.collect_data(target, valid_platforms)
        if not collected_data:
             return jsonify({"message": "No data collected for the target.", "status": "completed_no_data"}), 200

        # --- Step 2: Preservation ---
        preserved_files = data_preserver.preserve_data(case_name, collected_data, collection_details)
        if not preserved_files:
             return jsonify({"error": "Data collection succeeded but preservation failed."}), 500

        # --- Step 3: Analysis ---
        # TODO: Refactor analysis modules to read from case_path/data
        # For now, we pass the collected_data directly, which isn't ideal forensically
        print("[Analysis] Running sentiment analysis...")
        sentiment_results = sentiment_analyzer.analyze_user_posts({"posts": collected_data}) # Adapt input later
        analysis_dir = os.path.join(case_path, config.CASE_ANALYSIS_DIR_NAME)
        sentiment_path = os.path.join(analysis_dir, "sentiment_results.json")
        with open(sentiment_path, 'w', encoding='utf-8') as f:
             json.dump(sentiment_results, f, indent=4)

        print("[Analysis] Running network analysis...")
        # Network analysis needs adaptation to work with preserved data format
        # It currently expects a list of dicts structure from the old API search
        # Placeholder: Generate visualization based on collected data structure
        network_input_data = [{ # Reformat slightly for existing network analyzer
             'user': target,
             'platform': p,
             'profile': {}, # Add profile simulation later
             'posts': [item for item in collected_data if item['platform'] == p]
         } for p in valid_platforms]

        # Ensure network analyzer output goes to the case analysis dir
        original_output_dir = network_analyzer.output_dir
        network_analyzer.output_dir = analysis_dir
        network_vis_filename = f"network_graph_{int(time.time())}.png"
        network_vis_path_rel = os.path.join(config.CASE_ANALYSIS_DIR_NAME, network_vis_filename) # Relative path for response
        network_vis_path_abs = os.path.join(analysis_dir, network_vis_filename)

        # Note: visualize_network might need significant refactoring
        try:
            # Pass absolute path for saving
            _ = network_analyzer.visualize_network(network_input_data, output_filename=network_vis_path_abs)
            print(f"[Analysis] Network graph saved to {network_vis_path_abs}")
        except Exception as net_err:
             print(f"Error during network visualization: {net_err}", file=sys.stderr)
             traceback.print_exc()
             network_vis_path_rel = None # Indicate failure
        finally:
             network_analyzer.output_dir = original_output_dir # Restore original setting


        # TODO: Add other analysis steps (image, timeline etc.)

        # --- Step 4: Reporting ---
        print("[Reporting] Generating forensic report...")
        # TODO: Refactor report generator to read all data from case_path
        report_filename = f"forensic_report_{case_name}_{int(time.time())}.pdf" # Or HTML
        # Pass case_path to generator so it can find all necessary files
        report_generator.output_dir = config.REPORTS_DIR # Ensure reports go to the main reports dir
        try:
            # Pass case_path, and potentially analysis results directly if needed for refactor
            report_path_abs = report_generator.generate_report(
                case_name=case_name,
                case_path=case_path,
                target_info=collection_details,
                # Pass necessary data explicitly until generator is fully refactored
                sentiment_results=sentiment_results,
                network_vis_path=network_vis_path_abs if network_vis_path_rel else None
            )
            report_path_rel = os.path.basename(report_path_abs) if report_path_abs else None
            print(f"[Reporting] Report generated: {report_path_rel}")
        except Exception as rep_err:
            print(f"Error during report generation: {rep_err}", file=sys.stderr)
            traceback.print_exc()
            report_path_rel = None

        # --- Format Response ---
        response_summary = {
            "status": "completed",
            "case_name": case_name,
            "target": target,
            "platforms_processed": valid_platforms,
            "items_collected": len(collected_data),
            "items_preserved": len(preserved_files),
            "analysis_summary": {
                "sentiment_path": os.path.join(config.CASE_ANALYSIS_DIR_NAME, "sentiment_results.json"),
                "network_graph_path": network_vis_path_rel,
                # Add other analysis results paths here
            },
            "report_filename": report_path_rel
        }
        return jsonify(response_summary), 200

    except Exception as e:
        print(f"Error processing case '{case_name}': {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({"error": f"An unexpected error occurred while processing the case: {str(e)}"}), 500


@app.route('/api/cases/<case_name>/artifacts/<path:artifact_path>')
def get_case_artifact(case_name, artifact_path):
    """Serve analysis artifacts (images, JSON) from a case."""
    case_path = get_case_path(case_name)
    if not case_path or not os.path.isdir(case_path):
        return jsonify({"error": f"Case '{case_name}' not found"}), 404

    # Basic path safety check
    safe_artifact_path = os.path.normpath(artifact_path).lstrip('/\\')
    full_path = os.path.join(case_path, safe_artifact_path)

    # Prevent accessing files outside the case directory
    if not full_path.startswith(os.path.abspath(case_path)):
         return jsonify({"error": "Access denied"}), 403

    if not os.path.exists(full_path):
        return jsonify({"error": "Artifact not found"}), 404

    # Determine mimetype (simple version)
    mimetype = 'application/octet-stream'
    if full_path.endswith('.png'):
        mimetype = 'image/png'
    elif full_path.endswith('.json'):
        mimetype = 'application/json'
    elif full_path.endswith('.pdf'):
        mimetype = 'application/pdf'
    elif full_path.endswith('.html'):
        mimetype = 'text/html'

    return send_file(full_path, mimetype=mimetype)

@app.route('/api/reports/<path:filename>')
def get_report(filename):
    """Serve generated report files from the main reports directory."""
    # Basic path safety check
    safe_filename = os.path.basename(filename)
    if not safe_filename:
         return jsonify({"error": "Invalid report filename"}), 400

    report_path = os.path.join(config.REPORTS_DIR, safe_filename)

    if not os.path.exists(report_path):
        return jsonify({'error': 'Report not found'}), 404

    mimetype = 'application/pdf' if safe_filename.lower().endswith('.pdf') else 'text/html'
    return send_file(report_path, mimetype=mimetype, as_attachment=True, download_name=safe_filename)


# --- Main Execution ---
def main():
    """Run the Flask application with port selection logic."""
    parser = argparse.ArgumentParser(description=f"Start {config.APP_NAME} Web Server v{config.VERSION}")
    parser.add_argument('--port', type=int, help='Port to run the server on')
    args = parser.parse_args()

    if args.port:
        ports_to_try = [args.port]
    else:
        ports_to_try = [8080, 8000, 5000, 3000] # Common dev ports

    server_started = False
    for port in ports_to_try:
        try:
            print(f"\nAttempting to start {config.APP_NAME} server on port {port}...")
            # Use host='0.0.0.0' to be accessible on the network
            app.run(debug=True, host='0.0.0.0', port=port)
            server_started = True
            break # Exit loop if server starts successfully
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"Port {port} is already in use.")
                if port == 5000 and sys.platform == 'darwin': # macOS specific hint
                    print("Hint: On macOS, port 5000 might be used by AirPlay Receiver.")
                    print("-> System Settings > General > AirDrop & Handoff > Turn off 'AirPlay Receiver'")
                continue # Try the next port
            else:
                print(f"Error starting server on port {port}: {e}", file=sys.stderr)
                traceback.print_exc()
                break # Don't try other ports if it's not an 'address in use' error
        except Exception as e:
            print(f"An unexpected error occurred: {e}", file=sys.stderr)
            traceback.print_exc()
            break

    if not server_started:
        print("\nFailed to start the server on any attempted port.", file=sys.stderr)
        if not args.port:
             print("You can specify a port using: python app.py --port <port_number>", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    # Ensure necessary directories exist before starting
    os.makedirs(config.CASES_DIR, exist_ok=True)
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    main() 