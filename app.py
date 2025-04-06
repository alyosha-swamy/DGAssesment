import os
import json
from flask import Flask, render_template, request, jsonify
from markupsafe import Markup
import time
# Ensure scraper_utils.py is in the same directory or Python path
try:
    # Updated import to the new main parallel function
    from scraper_utils import get_user_info_and_id, run_all_analyses_parallel, prepare_cookies, prepare_headers
except ImportError as e:
    print(f"Error: Could not import from scraper_utils.py: {e}")
    print("Ensure scraper_utils.py exists and contains the required functions.")
    # Optionally exit if the import fails, as the app won't work
    import sys
    sys.exit(1)


app = Flask(__name__)

# Function to safely extract graph data for vis.js
def prepare_graph_json(json_data):
    graph_data = json_data.get("network_connections_explicit")
    if not graph_data or not isinstance(graph_data.get("nodes"), list) or not isinstance(graph_data.get("edges"), list):
        print("No valid explicit graph data found in JSON response.")
        return 'null'
    try:
        # Ensure nodes have labels for vis.js
        # Add profile owner if missing (should be handled in utils, but belt-and-suspenders)
        nodes = graph_data.get('nodes', [])
        has_owner = any(node.get("id") == "profile_owner" for node in nodes)
        if not has_owner:
            username = json_data.get("profile_context", {}).get("username", "Unknown")
            nodes.insert(0, {"id": "profile_owner", "label": username, "type": "ProfileOwner"})

        for node in nodes:
            if 'label' not in node and 'id' in node:
                node['label'] = node['id'] # Use ID as label if missing
            if not node.get('id'): # Add default ID if missing somehow
                 node['id'] = f"missing_id_{time.time()}" # Avoid vis.js errors

        # Ensure edges reference valid nodes
        valid_node_ids = {node['id'] for node in nodes if node.get('id')}
        valid_edges = []
        for edge in graph_data.get('edges', []):
             if edge.get('from') in valid_node_ids and edge.get('to') in valid_node_ids:
                 # Add unique ID to edges if missing (vis.js might need it)
                 if 'id' not in edge:
                     edge['id'] = f"edge_{edge.get('from')}_{edge.get('to')}_{time.time()}"
                 valid_edges.append(edge)
             else:
                  print(f"Warning: Filtering out invalid edge: {edge}")

        # Reassign validated nodes and edges
        graph_data['nodes'] = nodes
        graph_data['edges'] = valid_edges

        graph_json = json.dumps(graph_data)
        print("Explicit graph data successfully prepared for JS.")
        return graph_json
    except Exception as json_e:
        print(f"Error converting graph data to JSON: {json_e}")
        return 'null'

@app.route('/')
def index():
    """Renders the homepage with the username input form."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Handles username submission, runs scraping and parallel analysis, renders results."""
    username = request.form.get('username')
    if not username:
        return render_template('index.html', error="Username cannot be empty.")

    # Prepare cookies and headers
    cookies = prepare_cookies()
    headers = prepare_headers(username, cookies)

    # Fetch profile info
    print(f"--- Starting analysis for: {username} ---")
    user_id, basic_info, profile_error = get_user_info_and_id(username, cookies, headers)

    # Initialize result variables
    llm_report = "Analysis not performed."
    llm_forensic_notes = "Analysis not performed."
    llm_json_data = None
    graph_data_json = 'null'
    llm_error = None # Consolidated error message

    if profile_error:
        print(f"Profile fetch failed: {profile_error}")
        # Pass profile_error to template, skip LLM calls
        return render_template('results.html', username=username, error=profile_error)

    # If profile fetch succeeded, run parallel LLM analyses
    if basic_info:
        biography = basic_info.get('biography') # Can be None or empty string
        if biography is None:
            biography = "" # Ensure it's a string for LLM calls

        print("Starting parallel LLM analyses...")
        # Call the parallel function from scraper_utils
        analysis_results = run_all_analyses_parallel(username, biography)

        # Extract results from the returned dictionary
        llm_report = analysis_results.get("report", "Report generation failed or task did not complete.")
        llm_forensic_notes = analysis_results.get("forensic_notes", "Forensic note generation failed or task did not complete.")
        llm_json_data = analysis_results.get("json_data")

        # Check for errors specifically in the JSON data generation
        if isinstance(llm_json_data, dict) and llm_json_data.get("error"):
            llm_error = f"LLM JSON Data Error: {llm_json_data.get('error')}"
            print(llm_error)
            # Optionally extract raw response if available
            raw_resp = llm_json_data.get('raw_response')
            if raw_resp:
                 llm_error += f" (Raw Response Snippet: {raw_resp[:100]}...)"
            # Attempt to prepare graph json even if other parts failed
            graph_data_json = prepare_graph_json(llm_json_data) # Use helper

        elif isinstance(llm_json_data, dict):
            # Success case for JSON data, prepare graph for vis.js
            graph_data_json = prepare_graph_json(llm_json_data) # Use helper
        else:
            # Handle unexpected type for llm_json_data
            llm_error = f"LLM JSON Data Error: Unexpected data type received ({type(llm_json_data)})."
            print(llm_error)
            llm_json_data = {"error": llm_error} # Ensure it's a dict for template

    else:
        # This case should now be caught by profile_error, but defensive coding
        profile_error = "Failed to retrieve basic profile information."
        print(profile_error)
        return render_template('results.html', username=username, error=profile_error)

    # Pass all results to the template
    return render_template(
        'results.html',
        username=username,
        profile_info=basic_info,
        user_id=user_id,
        llm_report=llm_report,
        llm_forensic_notes=llm_forensic_notes,
        llm_json_data=llm_json_data, # Pass the whole JSON dict
        graph_data_json=Markup(graph_data_json), # Specific JSON for vis.js graph
        llm_error=llm_error, # Consolidated error from JSON task
        error=None # No profile fetch error if we reached here
    )

if __name__ == '__main__':
    # API Key check is now handled within run_all_analyses_parallel
    print("Starting Flask app...")
    app.run(host='0.0.0.0', port=5001, debug=True)
