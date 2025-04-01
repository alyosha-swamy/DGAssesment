import networkx as nx
import os
import sys
import json
import random
import math
import matplotlib
matplotlib.use('Agg')  # Use Agg backend for non-GUI environments
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import traceback
from glob import glob
from datetime import datetime

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    import config
except ImportError:
    print("Error: Could not import config from network.py", file=sys.stderr)
    # Define fallback config paths if necessary
    class MockConfig:
        CASES_DIR = "cases"
        CASE_DATA_DIR_NAME = "data"
        CASE_ANALYSIS_DIR_NAME = "analysis"
    config = MockConfig()

class NetworkAnalyzer:
    """
    Analyze network connections based on data within a case folder.
    Generates a visualization of the network.
    """
    def __init__(self):
        # Output directory is now determined per-case during analysis
        pass

    def _get_case_dirs(self, case_name):
        """Get paths for data and analysis directories for a case."""
        safe_case_name = os.path.basename(case_name)
        if not safe_case_name or safe_case_name == '.' or safe_case_name == '..':
            return None, None
        case_path = os.path.join(config.CASES_DIR, safe_case_name)
        if not os.path.isdir(case_path):
            return None, None
        data_path = os.path.join(case_path, config.CASE_DATA_DIR_NAME)
        analysis_path = os.path.join(case_path, config.CASE_ANALYSIS_DIR_NAME)
        # Ensure analysis dir exists
        os.makedirs(analysis_path, exist_ok=True)
        return data_path, analysis_path

    def _build_graph_from_case_data(self, case_data_path, target_user):
        """
        Build a NetworkX graph from preserved JSON data files in a case.
        Simulates connections for demonstration purposes.
        Args:
            case_data_path (str): Path to the case's data directory.
            target_user (str): The primary target user of the investigation.
        Returns:
            nx.Graph: A NetworkX graph object, potentially empty if no data.
        """
        graph = nx.Graph()
        data_files = glob(os.path.join(case_data_path, "*.json"))

        if not data_files:
            return graph # Return empty graph

        all_users = set([target_user]) # Start with the main target
        processed_data = []

        # --- Pass 1: Identify all unique users/entities --- 
        # In a real scenario, this would parse interactions (mentions, replies)
        # Here, we simulate finding related users based on content.
        for filepath in data_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                processed_data.append(data)
                # Simulate finding mentioned users (e.g., @ mentions)
                content = data.get('content', '')
                mentions = re.findall(r'@(\w+)', content)
                for mention in mentions:
                    all_users.add(mention)
                # Add the post author/target if available
                if data.get('target') and data['target'] != target_user:
                    all_users.add(data['target'])

            except Exception as e:
                print(f"Warning: Error reading/parsing {filepath}: {e}", file=sys.stderr)
                continue

        # Limit number of simulated users for visualization clarity
        simulated_users_to_add = min(15, len(all_users))
        display_users = random.sample(list(all_users), simulated_users_to_add)
        if target_user not in display_users and target_user in all_users:
             display_users.append(target_user)

        # --- Pass 2: Add nodes for identified users --- 
        node_attributes = {}
        for user in display_users:
            # Simulate node attributes
            platform = random.choice(config.SUPPORTED_PLATFORMS)
            node_id = f"{user}_{platform}"
            attributes = {
                "username": user,
                "platform": platform,
                "followers": random.randint(10, 5000) if user != target_user else random.randint(1000, 10000),
                "post_count": random.randint(1, 50),
                "is_suspicious": random.random() < 0.15, # 15% chance of being suspicious
                "label": user # Simple label for visualization
            }
            graph.add_node(node_id, **attributes)
            node_attributes[node_id] = attributes # Store for edge creation

        # --- Pass 3: Add simulated edges --- 
        if graph.number_of_nodes() > 1:
             nodes = list(graph.nodes())
             target_node_id = next((nid for nid in nodes if graph.nodes[nid]['username'] == target_user), None)

             for i, node1_id in enumerate(nodes):
                 # Connect target user to a few others
                 if target_node_id and node1_id != target_node_id and random.random() < 0.3:
                      weight = round(random.uniform(0.2, 1.0), 2)
                      graph.add_edge(target_node_id, node1_id, weight=weight, type='simulated_interaction')

                 # Add random connections between other nodes
                 for node2_id in nodes[i+1:]:
                     if node1_id != target_node_id and node2_id != target_node_id:
                         # Connect nodes with lower probability
                         if random.random() < 0.15:
                             weight = round(random.uniform(0.1, 0.7), 2)
                             graph.add_edge(node1_id, node2_id, weight=weight, type='simulated_connection')
        return graph

    def visualize_network(self, case_name, target_user, output_filename="network_graph.png"):
        """
        Generate and save a visualization of the network graph for a case.

        Args:
            case_name (str): The name of the case.
            target_user (str): The primary target user for context.
            output_filename (str): The desired filename for the output image (e.g., 'network.png').

        Returns:
            str: The absolute path to the generated visualization file, or None if failed.
        """
        case_data_path, case_analysis_path = self._get_case_dirs(case_name)
        if not case_data_path or not case_analysis_path:
            print(f"Error: Invalid case or paths for '{case_name}'", file=sys.stderr)
            return None

        # Build graph
        print(f"Building network graph for case '{case_name}'...")
        graph = self._build_graph_from_case_data(case_data_path, target_user)

        if graph.number_of_nodes() == 0:
            print(f"No nodes found for network analysis in case '{case_name}'. Skipping visualization.")
            return None

        print(f"Visualizing network with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges...")

        # Prepare for visualization
        plt.figure(figsize=(16, 12))
        pos = nx.spring_layout(graph, k=0.6, iterations=50) # Layout algorithm

        # Node colors (e.g., based on suspicion or platform)
        node_colors = ['#ff7f0e' if graph.nodes[node].get('is_suspicious') else '#1f77b4' for node in graph.nodes()]
        # Node sizes (e.g., based on followers or post count)
        node_sizes = [max(200, min(3000, graph.nodes[node].get('followers', 100))) for node in graph.nodes()]

        # Edge widths (based on weight)
        edge_widths = [graph[u][v].get('weight', 0.5) * 3 for u, v in graph.edges()]

        try:
            nx.draw_networkx_edges(graph, pos, alpha=0.4, width=edge_widths, edge_color='gray')
            nx.draw_networkx_nodes(graph, pos, node_color=node_colors, node_size=node_sizes, alpha=0.9)
            nx.draw_networkx_labels(graph, pos, labels={n: d.get('label', '') for n, d in graph.nodes(data=True)}, font_size=9, font_weight='bold')

            plt.title(f"Simulated Network Graph for Case: {case_name} (Target: {target_user})", size=16)
            plt.axis('off')
            plt.tight_layout()

            # Save the visualization
            output_path = os.path.join(case_analysis_path, os.path.basename(output_filename))
            plt.savefig(output_path, format='png', dpi=100)
            plt.close() # Close the figure to free memory
            print(f"Network visualization saved to: {output_path}")
            return output_path

        except Exception as e:
            print(f"Error during network visualization generation: {e}", file=sys.stderr)
            traceback.print_exc()
            plt.close() # Ensure figure is closed even on error
            return None

# Example Usage (if run directly)
if __name__ == "__main__":
    if len(sys.argv) > 2:
        case_name_to_analyze = sys.argv[1]
        target = sys.argv[2]
        print(f"Running network analysis for case: {case_name_to_analyze}, Target: {target}")
        analyzer = NetworkAnalyzer()
        output_file = analyzer.visualize_network(case_name_to_analyze, target)
        if output_file:
            print(f"\nNetwork graph saved to: {output_file}")
        else:
            print(f"Network analysis failed for case '{case_name_to_analyze}'.")
    else:
        print("Usage: python network.py <case_name> <target_user>")
        # Example of creating a dummy case for testing
        print("\nCreating dummy case 'test_case_network' for example.")
        dummy_case = "test_case_network"
        dummy_data_path = os.path.join(config.CASES_DIR, dummy_case, config.CASE_DATA_DIR_NAME)
        dummy_analysis_path = os.path.join(config.CASES_DIR, dummy_case, config.CASE_ANALYSIS_DIR_NAME)
        os.makedirs(dummy_data_path, exist_ok=True)
        os.makedirs(dummy_analysis_path, exist_ok=True)
        dummy_data = [
            {"id": "post1", "content": "Talking to @userA and @userB about #topic1", "target": "main_target"},
            {"id": "post2", "content": "Great discussion with @userC", "target": "main_target", "platform": "X"},
            {"id": "post3", "content": "@main_target check this out!", "target": "userA", "platform": "Facebook"},
            {"id": "post4", "content": "Just posting random thoughts #topic2", "target": "userB"}
        ]
        for i, post in enumerate(dummy_data):
             with open(os.path.join(dummy_data_path, f"item_{i}.json"), 'w') as f:
                 json.dump(post, f)
        print(f"Dummy data created in {dummy_data_path}")
        print("Now run: python network.py test_case_network main_target") 