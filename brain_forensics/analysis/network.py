import networkx as nx
import os
import sys
import json
import random
import matplotlib
matplotlib.use('Agg')  # Use Agg backend which doesn't require a GUI
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import time
from datetime import datetime

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class NetworkAnalyzer:
    """
    Analyze network connections between users
    """
    def __init__(self):
        self.output_dir = os.path.join(config.DATA_DIR, "network_analysis")
        os.makedirs(self.output_dir, exist_ok=True)
        self.graph = nx.Graph()
        
        # Define colors for sentiment visualization
        self.cmap = LinearSegmentedColormap.from_list(
            'sentiment', 
            ['#d9534f', '#f0ad4e', '#5bc0de', '#5cb85c']
        )
        
    def _build_graph_from_user_data(self, user_data_list):
        """
        Build a graph from user data
        
        Args:
            user_data_list (list): List of user data dictionaries
        """
        self.graph.clear()
        
        # Add nodes (users) to graph
        for user_data in user_data_list:
            username = user_data.get('user', '')
            platform = user_data.get('platform', '')
            
            # Skip if no username
            if not username:
                continue
                
            # Add node with metadata
            node_id = f"{username}_{platform}"
            profile = user_data.get('profile', {})
            posts = user_data.get('posts', [])
            
            # Calculate average sentiment if available
            avg_sentiment = 0
            if hasattr(user_data, 'average_sentiment'):
                avg_sentiment = user_data.average_sentiment
            
            self.graph.add_node(
                node_id,
                username=username,
                platform=platform,
                followers=profile.get('followers', 0),
                following=profile.get('following', 0),
                post_count=len(posts),
                verified=profile.get('verified', False),
                sentiment=avg_sentiment,
                is_suspicious=profile.get('is_suspicious', False)
            )
            
            # For prototype, simulate connections between users
            # In a real implementation, we would extract mentions, replies, etc.
            self._simulate_connections(user_data_list, username, platform)
    
    def _simulate_connections(self, user_data_list, username, platform):
        """
        Simulate connections between users for prototype
        
        Args:
            user_data_list (list): List of user data dictionaries
            username (str): Current username
            platform (str): Current platform
        """
        current_node = f"{username}_{platform}"
        
        # Randomly connect to other users on the same platform
        for other_user in user_data_list:
            other_username = other_user.get('user', '')
            other_platform = other_user.get('platform', '')
            
            # Skip self or users on other platforms
            if (other_username == username and other_platform == platform) or other_platform != platform:
                continue
                
            other_node = f"{other_username}_{other_platform}"
            
            # Add edge with 40% probability
            if random.random() < 0.4:
                # Simulate connection weight (interaction strength)
                weight = random.uniform(0.1, 1.0)
                
                # Simulate interaction type
                interaction_types = ['mention', 'reply', 'retweet', 'like']
                interaction_type = random.choice(interaction_types)
                
                # Add edge with metadata
                self.graph.add_edge(
                    current_node,
                    other_node,
                    weight=weight,
                    type=interaction_type
                )
    
    def detect_communities(self):
        """
        Detect communities in the graph
        
        Returns:
            dict: Community detection results
        """
        if not self.graph or self.graph.number_of_nodes() < 2:
            return {'communities': [], 'modularity': 0}
            
        # Use Louvain algorithm for community detection
        communities = nx.community.louvain_communities(self.graph)
        
        # Calculate modularity
        modularity = nx.community.modularity(self.graph, communities)
        
        # Format results
        community_data = []
        for i, community in enumerate(communities):
            members = []
            for node in community:
                node_data = self.graph.nodes[node]
                members.append({
                    'id': node,
                    'username': node_data.get('username', ''),
                    'platform': node_data.get('platform', ''),
                    'is_suspicious': node_data.get('is_suspicious', False)
                })
            
            community_data.append({
                'id': i,
                'size': len(community),
                'members': members
            })
        
        return {
            'communities': community_data,
            'modularity': modularity
        }
    
    def detect_influential_nodes(self):
        """
        Detect influential nodes in the network
        
        Returns:
            list: Influential nodes
        """
        if not self.graph or self.graph.number_of_nodes() < 2:
            return []
            
        # Calculate centrality measures
        betweenness = nx.betweenness_centrality(self.graph)
        eigenvector = nx.eigenvector_centrality_numpy(self.graph)
        pagerank = nx.pagerank(self.graph)
        
        # Identify influential nodes
        influential_nodes = []
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            
            # Consider a node influential if it ranks high in any centrality measure
            if (betweenness[node] > 0.1 or eigenvector[node] > 0.1 or pagerank[node] > 0.1):
                influential_nodes.append({
                    'id': node,
                    'username': node_data.get('username', ''),
                    'platform': node_data.get('platform', ''),
                    'betweenness': betweenness[node],
                    'eigenvector': eigenvector[node],
                    'pagerank': pagerank[node],
                    'followers': node_data.get('followers', 0),
                    'is_suspicious': node_data.get('is_suspicious', False)
                })
        
        # Sort by sum of centrality measures
        influential_nodes.sort(key=lambda x: x['betweenness'] + x['eigenvector'] + x['pagerank'], reverse=True)
        
        return influential_nodes
    
    def detect_suspicious_connections(self):
        """
        Detect suspicious connection patterns
        
        Returns:
            list: Suspicious connections
        """
        if not self.graph or self.graph.number_of_nodes() < 3:
            return []
            
        suspicious_connections = []
        
        # Detect cliques (fully connected subgraphs)
        cliques = list(nx.find_cliques(self.graph))
        large_cliques = [c for c in cliques if len(c) >= 3]
        
        for clique in large_cliques:
            # Check if majority of nodes in clique are suspicious
            suspicious_count = sum(1 for node in clique if self.graph.nodes[node].get('is_suspicious', False))
            
            if suspicious_count >= len(clique) / 2:
                suspicious_connections.append({
                    'type': 'suspicious_clique',
                    'nodes': clique,
                    'size': len(clique),
                    'description': f'Clique of {len(clique)} accounts with {suspicious_count} suspicious accounts'
                })
        
        # Detect account farms (accounts with very similar behavior)
        # For prototype, we'll simulate this
        for node in self.graph.nodes():
            neighbors = list(self.graph.neighbors(node))
            
            if len(neighbors) >= 3:
                # Check if node is connecting multiple suspicious accounts
                suspicious_neighbors = [n for n in neighbors if self.graph.nodes[n].get('is_suspicious', False)]
                
                if len(suspicious_neighbors) >= 2:
                    suspicious_connections.append({
                        'type': 'account_farm',
                        'central_node': node,
                        'connected_nodes': suspicious_neighbors,
                        'description': f'Account connected to {len(suspicious_neighbors)} suspicious accounts'
                    })
        
        return suspicious_connections
    
    def visualize_network(self, user_data_list, filename=None):
        """
        Visualize the network
        
        Args:
            user_data_list (list): List of user data dictionaries
            filename (str): Output filename (optional)
            
        Returns:
            str: Path to saved visualization file
        """
        # Build graph from user data
        self._build_graph_from_user_data(user_data_list)
        
        if not self.graph or self.graph.number_of_nodes() < 1:
            return None
            
        # Create figure
        plt.figure(figsize=(12, 8))
        
        # Calculate node sizes based on followers count
        node_sizes = []
        node_colors = []
        for node in self.graph.nodes():
            # Get followers count, default to 100 if None or invalid
            followers = self.graph.nodes[node].get('followers', 100)
            try:
                followers = float(followers)
                if followers != followers:  # Check for NaN
                    followers = 100
            except (TypeError, ValueError):
                followers = 100
            
            is_suspicious = self.graph.nodes[node].get('is_suspicious', False)
            
            # Size based on log of followers (minimum 100, maximum 2000)
            size = max(100, min(2000, 100 * (1 + followers / 1000)))
            node_sizes.append(size)
            
            # Color based on suspiciousness
            node_colors.append('red' if is_suspicious else 'green')
        
        # Calculate edge weights
        edge_widths = []
        for u, v in self.graph.edges():
            weight = self.graph[u][v].get('weight', 0.5)
            try:
                weight = float(weight)
                if weight != weight:  # Check for NaN
                    weight = 0.5
            except (TypeError, ValueError):
                weight = 0.5
            edge_widths.append(weight * 3)
        
        # Spring layout for graph
        try:
            pos = nx.spring_layout(self.graph, k=0.3, iterations=50)
        except:
            # Fallback to simpler layout if spring layout fails
            pos = nx.circular_layout(self.graph)
        
        # Draw nodes
        nx.draw_networkx_nodes(
            self.graph, 
            pos, 
            node_size=node_sizes,
            node_color=node_colors,
            alpha=0.8
        )
        
        # Draw edges
        nx.draw_networkx_edges(
            self.graph, 
            pos, 
            width=edge_widths,
            alpha=0.5,
            edge_color='gray'
        )
        
        # Draw labels
        nx.draw_networkx_labels(
            self.graph, 
            pos, 
            font_size=8,
            font_family='sans-serif'
        )
        
        # Title and layout
        plt.title('Social Media Network Analysis', fontsize=16)
        plt.axis('off')
        
        # Save figure if filename provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"network_visualization_{timestamp}.png"
            
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path 