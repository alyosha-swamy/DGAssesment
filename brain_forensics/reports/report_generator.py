import os
import sys
import json
import time
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
import pandas as pd
from wordcloud import WordCloud
import base64
from io import BytesIO

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class ForensicReportGenerator:
    """
    Generate PDF forensic reports based on analysis results
    """
    def __init__(self):
        self.output_dir = config.REPORTS_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Configure default styles
        self.colors = {
            'primary': '#3498db',
            'secondary': '#2c3e50',
            'success': '#2ecc71',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'info': '#9b59b6'
        }
        
    def _create_sentiment_chart(self, user_data):
        """Create sentiment distribution chart"""
        sentiment_dist = user_data.get('sentiment_distribution', {})
        
        # Create data for chart
        labels = list(sentiment_dist.keys())
        values = list(sentiment_dist.values())
        
        # Create pie chart
        plt.figure(figsize=(6, 4))
        colors = ['#2ecc71', '#3498db', '#e74c3c']
        plt.pie(
            values, 
            labels=labels, 
            colors=colors,
            autopct='%1.1f%%', 
            startangle=90,
            wedgeprops={'edgecolor': 'white', 'linewidth': 1}
        )
        plt.axis('equal')
        plt.title('Sentiment Distribution')
        
        # Save to BytesIO
        img_bytes = BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight')
        plt.close()
        img_bytes.seek(0)
        
        return img_bytes
    
    def _create_posting_timeline(self, user_data):
        """Create timeline of posts"""
        posts = user_data.get('posts', [])
        
        if not posts:
            return None
            
        # Extract timestamps and sentiment scores
        timestamps = [post.get('timestamp') for post in posts]
        dates = [datetime.fromtimestamp(ts) for ts in timestamps]
        
        # Create a dataframe for easy plotting
        df = pd.DataFrame({
            'date': dates,
            'sentiment': [post.get('sentiment_analysis', {}).get('sentiment_score', 0) for post in posts]
        })
        
        # Sort by date
        df = df.sort_values('date')
        
        # Plot
        plt.figure(figsize=(8, 4))
        plt.plot(df['date'], df['sentiment'], marker='o', linestyle='-', color=self.colors['primary'])
        
        # Add a horizontal line at 0
        plt.axhline(y=0, color='gray', linestyle='--', alpha=0.7)
        
        # Format
        plt.title('Sentiment Over Time')
        plt.xlabel('Date')
        plt.ylabel('Sentiment Score')
        plt.grid(True, alpha=0.3)
        
        # Color the markers based on sentiment
        for i, sentiment in enumerate(df['sentiment']):
            if sentiment > 0:
                plt.plot(df['date'].iloc[i], sentiment, 'o', color='green', markersize=8)
            elif sentiment < 0:
                plt.plot(df['date'].iloc[i], sentiment, 'o', color='red', markersize=8)
            else:
                plt.plot(df['date'].iloc[i], sentiment, 'o', color='blue', markersize=8)
        
        # Save to BytesIO
        img_bytes = BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight')
        plt.close()
        img_bytes.seek(0)
        
        return img_bytes
    
    def _create_wordcloud(self, user_data):
        """Create wordcloud from post keywords"""
        posts = user_data.get('posts', [])
        keywords = user_data.get('top_keywords', [])
        
        if not posts and not keywords:
            return None
            
        # Collect all text from posts
        all_text = " ".join([post.get('content', '') for post in posts])
        
        if not all_text and not keywords:
            return None
            
        # If we have keywords with frequency, use those
        if keywords:
            # Convert to dictionary with frequencies (for prototype, use equal frequencies)
            word_freq = {word: 10 for word in keywords}
        else:
            # Use the full text
            word_freq = None
            
        # Generate wordcloud
        wordcloud = WordCloud(
            width=400, 
            height=200, 
            background_color='white',
            colormap='viridis',
            max_words=50
        ).generate_from_frequencies(word_freq) if word_freq else WordCloud(
            width=400,
            height=200,
            background_color='white',
            colormap='viridis',
            max_words=50
        ).generate(all_text)
        
        # Create plot
        plt.figure(figsize=(6, 3))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('Common Keywords')
        
        # Save to BytesIO
        img_bytes = BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight')
        plt.close()
        img_bytes.seek(0)
        
        return img_bytes
    
    def generate_report(self, user_data, analysis_results, network_results=None, filename=None):
        """
        Generate a PDF forensic report
        
        Args:
            user_data (dict): User data from the search API
            analysis_results (dict): Results from sentiment analysis
            network_results (dict): Results from network analysis (optional)
            filename (str): Output filename (optional)
            
        Returns:
            str: Path to the saved report
        """
        if not filename:
            timestamp = int(time.time())
            username = user_data.get('user', 'unknown')
            platform = user_data.get('platform', 'unknown')
            filename = f"forensic_report_{username}_{platform}_{timestamp}.pdf"
            
        output_path = os.path.join(self.output_dir, filename)
        
        # Create PDF document
        pdf = FPDF()
        pdf.add_page()
        
        # Set up fonts
        pdf.set_font('Arial', 'B', 16)
        
        # Title
        pdf.cell(190, 10, 'Social Media Forensic Analysis Report', 0, 1, 'C')
        
        # Add timestamp
        pdf.set_font('Arial', 'I', 10)
        report_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        pdf.cell(190, 6, f'Generated on: {report_date}', 0, 1, 'C')
        
        # User Information Section
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 14)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(190, 10, 'User Information', 0, 1, 'L', 1)
        
        # User details
        pdf.set_font('Arial', '', 11)
        
        username = user_data.get('user', 'Unknown')
        platform = user_data.get('platform', 'Unknown')
        profile = user_data.get('profile', {})
        
        pdf.ln(2)
        pdf.cell(60, 6, 'Username:', 0, 0, 'L')
        pdf.cell(130, 6, username, 0, 1, 'L')
        
        pdf.cell(60, 6, 'Platform:', 0, 0, 'L')
        pdf.cell(130, 6, platform, 0, 1, 'L')
        
        pdf.cell(60, 6, 'Account Created:', 0, 0, 'L')
        pdf.cell(130, 6, profile.get('created_date', 'Unknown'), 0, 1, 'L')
        
        pdf.cell(60, 6, 'Followers:', 0, 0, 'L')
        pdf.cell(130, 6, str(profile.get('followers', 'Unknown')), 0, 1, 'L')
        
        pdf.cell(60, 6, 'Following:', 0, 0, 'L')
        pdf.cell(130, 6, str(profile.get('following', 'Unknown')), 0, 1, 'L')
        
        pdf.cell(60, 6, 'Verified Account:', 0, 0, 'L')
        pdf.cell(130, 6, 'Yes' if profile.get('verified', False) else 'No', 0, 1, 'L')
        
        pdf.cell(60, 6, 'Bio:', 0, 0, 'L')
        pdf.cell(130, 6, profile.get('bio', 'None'), 0, 1, 'L')
        
        # Suspicious account flag
        if profile.get('is_suspicious', False):
            pdf.ln(2)
            pdf.set_text_color(255, 0, 0)
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(190, 6, 'WARNING: Potentially suspicious account detected', 0, 1, 'L')
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arial', '', 11)
        
        # Activity Summary Section
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 14)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(190, 10, 'Activity Summary', 0, 1, 'L', 1)
        
        # Activity details
        pdf.set_font('Arial', '', 11)
        posts = user_data.get('posts', [])
        
        pdf.ln(2)
        pdf.cell(60, 6, 'Total Posts Analyzed:', 0, 0, 'L')
        pdf.cell(130, 6, str(len(posts)), 0, 1, 'L')
        
        pdf.cell(60, 6, 'Average Sentiment Score:', 0, 0, 'L')
        avg_sentiment = analysis_results.get('average_sentiment', 0)
        pdf.cell(130, 6, f"{avg_sentiment:.2f}", 0, 1, 'L')
        
        # Sentiment distribution chart
        sentiment_chart = self._create_sentiment_chart(analysis_results)
        if sentiment_chart:
            pdf.ln(5)
            pdf.cell(190, 6, 'Sentiment Distribution:', 0, 1, 'L')
            
            # Get the binary data and encode it for the PDF
            img_str = base64.b64encode(sentiment_chart.getvalue()).decode('ascii')
            pdf.image(sentiment_chart, x=50, y=None, w=100)
            
        # Timeline chart
        pdf.ln(5)
        pdf.cell(190, 6, 'Posting Timeline:', 0, 1, 'L')
        timeline_chart = self._create_posting_timeline(user_data)
        if timeline_chart:
            pdf.image(timeline_chart, x=25, y=None, w=160)
            
        # Wordcloud
        pdf.ln(5)
        pdf.cell(190, 6, 'Common Keywords:', 0, 1, 'L')
        wordcloud_chart = self._create_wordcloud(analysis_results)
        if wordcloud_chart:
            pdf.image(wordcloud_chart, x=50, y=None, w=100)
        
        # Anomalies Section
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 14)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(190, 10, 'Detected Anomalies', 0, 1, 'L', 1)
        
        # Anomalies details
        anomalies = analysis_results.get('anomalies', [])
        if anomalies:
            pdf.set_font('Arial', '', 11)
            for i, anomaly in enumerate(anomalies):
                pdf.ln(2)
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(190, 6, f"Anomaly {i+1}: {anomaly.get('type', 'Unknown')}", 0, 1, 'L')
                
                pdf.set_font('Arial', '', 11)
                pdf.cell(60, 6, 'Description:', 0, 0, 'L')
                pdf.cell(130, 6, anomaly.get('description', ''), 0, 1, 'L')
                
                pdf.cell(60, 6, 'Severity:', 0, 0, 'L')
                pdf.cell(130, 6, anomaly.get('severity', 'medium'), 0, 1, 'L')
                
                # Add timestamp if available
                if 'timestamp' in anomaly:
                    pdf.cell(60, 6, 'Timestamp:', 0, 0, 'L')
                    pdf.cell(130, 6, anomaly.get('timestamp', ''), 0, 1, 'L')
        else:
            pdf.set_font('Arial', 'I', 11)
            pdf.ln(2)
            pdf.cell(190, 6, 'No anomalies detected', 0, 1, 'L')
        
        # Suspicious Content Section
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 14)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(190, 10, 'Suspicious Content', 0, 1, 'L', 1)
        
        # Suspicious content details
        suspicious_content = analysis_results.get('suspicious_content', [])
        if suspicious_content:
            pdf.set_font('Arial', '', 11)
            for i, content in enumerate(suspicious_content):
                pdf.ln(2)
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(190, 6, f"Suspicious Post {i+1}:", 0, 1, 'L')
                
                pdf.set_font('Arial', '', 10)
                pdf.multi_cell(190, 6, f"Content: {content.get('content', '')}")
                
                pdf.set_font('Arial', '', 11)
                pdf.cell(60, 6, 'Sentiment Score:', 0, 0, 'L')
                pdf.cell(130, 6, f"{content.get('sentiment_score', 0):.2f}", 0, 1, 'L')
                
                pdf.cell(60, 6, 'Reason Flagged:', 0, 0, 'L')
                pdf.cell(130, 6, content.get('reason', ''), 0, 1, 'L')
        else:
            pdf.set_font('Arial', 'I', 11)
            pdf.ln(2)
            pdf.cell(190, 6, 'No suspicious content detected', 0, 1, 'L')
        
        # Network Analysis Section (if available)
        if network_results:
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 14)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(190, 10, 'Network Analysis', 0, 1, 'L', 1)
            
            # Add network visualization if available
            if 'visualization_path' in network_results:
                pdf.ln(2)
                pdf.set_font('Arial', '', 11)
                pdf.cell(190, 6, 'User Connection Network:', 0, 1, 'L')
                pdf.image(network_results['visualization_path'], x=25, y=None, w=160)
            
            # Add influential nodes
            influential_nodes = network_results.get('influential_nodes', [])
            if influential_nodes:
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(190, 8, 'Influential Accounts', 0, 1, 'L')
                
                pdf.set_font('Arial', '', 11)
                for i, node in enumerate(influential_nodes[:3]):  # Top 3 influential nodes
                    pdf.ln(2)
                    pdf.cell(60, 6, f"Account {i+1}:", 0, 0, 'L')
                    pdf.cell(130, 6, node.get('username', ''), 0, 1, 'L')
                    
                    pdf.cell(60, 6, 'Centrality Score:', 0, 0, 'L')
                    centrality = node.get('pagerank', 0) + node.get('betweenness', 0)
                    pdf.cell(130, 6, f"{centrality:.4f}", 0, 1, 'L')
                    
                    pdf.cell(60, 6, 'Suspicious:', 0, 0, 'L')
                    pdf.cell(130, 6, 'Yes' if node.get('is_suspicious', False) else 'No', 0, 1, 'L')
            
            # Add suspicious connections
            suspicious_connections = network_results.get('suspicious_connections', [])
            if suspicious_connections:
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(190, 8, 'Suspicious Network Patterns', 0, 1, 'L')
                
                pdf.set_font('Arial', '', 11)
                for i, connection in enumerate(suspicious_connections):
                    pdf.ln(2)
                    pdf.cell(60, 6, f"Pattern {i+1}:", 0, 0, 'L')
                    pdf.cell(130, 6, connection.get('type', ''), 0, 1, 'L')
                    
                    pdf.cell(60, 6, 'Description:', 0, 0, 'L')
                    pdf.cell(130, 6, connection.get('description', ''), 0, 1, 'L')
        
        # Conclusion Section
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 14)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(190, 10, 'Conclusion', 0, 1, 'L', 1)
        
        # Generate a simple conclusion based on analysis
        pdf.ln(2)
        pdf.set_font('Arial', '', 11)
        
        # Determine risk level
        risk_level = "Low"
        risk_factors = []
        
        if profile.get('is_suspicious', False):
            risk_level = "High"
            risk_factors.append("Suspicious account profile")
        
        if len(anomalies) > 0:
            if 'high' in [a.get('severity', '') for a in anomalies]:
                risk_level = "High"
            elif risk_level != "High" and len(anomalies) > 2:
                risk_level = "Medium"
            risk_factors.append(f"{len(anomalies)} posting anomalies detected")
            
        if len(suspicious_content) > 0:
            if len(suspicious_content) > 2:
                risk_level = "High"
            elif risk_level != "High":
                risk_level = "Medium"
            risk_factors.append(f"{len(suspicious_content)} suspicious posts detected")
            
        if network_results and len(network_results.get('suspicious_connections', [])) > 0:
            risk_level = "High"
            risk_factors.append(f"{len(network_results.get('suspicious_connections', []))} suspicious network patterns")
            
        # Write conclusion
        pdf.multi_cell(190, 6, f"Based on the forensic analysis of the social media data for user '{username}' on {platform}, we have determined a {risk_level.upper()} risk level.")
        
        if risk_factors:
            pdf.ln(2)
            pdf.cell(190, 6, "Risk factors identified:", 0, 1, 'L')
            for factor in risk_factors:
                pdf.cell(10, 6, "•", 0, 0, 'R')
                pdf.cell(180, 6, factor, 0, 1, 'L')
        else:
            pdf.ln(2)
            pdf.multi_cell(190, 6, "No significant risk factors were identified in this analysis.")
            
        # Add disclaimer
        pdf.ln(5)
        pdf.set_font('Arial', 'I', 9)
        pdf.multi_cell(190, 5, "DISCLAIMER: This report was generated by an automated system and should be reviewed by a human analyst before drawing final conclusions. The accuracy of this analysis depends on the quality and completeness of the input data.")
        
        # Save the PDF
        pdf.output(output_path)
        
        return output_path 