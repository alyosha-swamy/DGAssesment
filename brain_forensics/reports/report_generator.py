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
import networkx as nx

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
        
        # Configure PDF styles
        self.section_font_size = 12
        self.text_font_size = 10
        self.line_height = 6
        
    def _create_sentiment_chart(self, sentiment_data):
        """Create sentiment distribution chart"""
        # Extract sentiment data
        avg_sentiment = sentiment_data.get('average_sentiment', 0)
        sentiment_dist = sentiment_data.get('sentiment_distribution', {
            'Positive': 0,
            'Neutral': 0,
            'Negative': 0
        })
        
        # Create data for chart
        labels = list(sentiment_dist.keys())
        values = list(sentiment_dist.values())
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # Pie chart for sentiment distribution
        colors = ['#2ecc71', '#3498db', '#e74c3c']
        ax1.pie(
            values, 
            labels=labels, 
            colors=colors,
            autopct='%1.1f%%', 
            startangle=90,
            wedgeprops={'edgecolor': 'white', 'linewidth': 1}
        )
        ax1.set_title('Sentiment Distribution')
        
        # Gauge chart for average sentiment
        sentiment_gauge = (avg_sentiment + 1) / 2  # Convert from [-1,1] to [0,1]
        gauge_colors = [(1-sentiment_gauge, sentiment_gauge, 0, 0.8)]
        ax2.pie([sentiment_gauge, 1-sentiment_gauge], colors=[gauge_colors[0], 'lightgray'], 
                startangle=90, counterclock=False)
        ax2.set_title(f'Average Sentiment: {avg_sentiment:.2f}')
        
        # Save to BytesIO
        img_bytes = BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight')
        plt.close()
        img_bytes.seek(0)
        
        return img_bytes
    
    def _create_posting_timeline(self, posts):
        """Create timeline of posts"""
        if not posts:
            return None
            
        # Extract timestamps and engagement metrics
        data = []
        for post in posts:
            timestamp = post.get('timestamp')
            if timestamp:
                data.append({
                    'date': datetime.fromtimestamp(timestamp),
                    'likes': post.get('likes', 0),
                    'shares': post.get('shares', 0),
                    'comments': post.get('comments', 0)
                })
        
        if not data:
            return None
        
        # Create a dataframe
        df = pd.DataFrame(data)
        df = df.sort_values('date')
        
        # Plot
        plt.figure(figsize=(10, 5))
        
        # Plot engagement metrics
        plt.plot(df['date'], df['likes'], 'o-', label='Likes', color=self.colors['primary'])
        plt.plot(df['date'], df['shares'], 's-', label='Shares', color=self.colors['success'])
        plt.plot(df['date'], df['comments'], '^-', label='Comments', color=self.colors['warning'])
        
        plt.title('Engagement Over Time')
        plt.xlabel('Date')
        plt.ylabel('Count')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        # Save to BytesIO
        img_bytes = BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight')
        plt.close()
        img_bytes.seek(0)
        
        return img_bytes
    
    def _create_wordcloud(self, sentiment_data, posts):
        """Create wordcloud from post content and keywords"""
        # Get keywords from sentiment analysis
        keywords = sentiment_data.get('top_keywords', [])
        
        # Get text from posts
        post_texts = [post.get('content', '') for post in posts if post.get('content')]
        
        if not keywords and not post_texts:
            return None
            
        # Combine all text
        all_text = " ".join(post_texts)
        
        # Create word frequencies
        word_freq = {}
        
        # Add keywords with high frequency
        for keyword in keywords:
            word_freq[keyword] = 100
            
        # Add words from posts
        if all_text:
            # Generate wordcloud
            wordcloud = WordCloud(
                width=800, 
                height=400, 
                background_color='white',
                colormap='viridis',
                max_words=100,
                prefer_horizontal=0.7
            ).generate(all_text)
            
            # Update frequencies with actual text
            word_freq.update(wordcloud.words_)
        
        # Generate final wordcloud
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            colormap='viridis',
            max_words=100,
            prefer_horizontal=0.7
        ).generate_from_frequencies(word_freq)
        
        # Create plot
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('Content Analysis - Key Terms')
        
        # Save to BytesIO
        img_bytes = BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight')
        plt.close()
        img_bytes.seek(0)
        
        return img_bytes
    
    def _create_network_graph(self, network_results):
        """Create network visualization"""
        if not network_results or 'image' not in network_results:
            return None
            
        # Convert base64 image to BytesIO
        try:
            img_data = base64.b64decode(network_results['image'])
            img_bytes = BytesIO(img_data)
            return img_bytes
        except:
            return None
    
    def generate_report(self, user_data, analysis_results, network_results=None, filename=None):
        """
        Generate a PDF forensic report
        
        Args:
            user_data (dict): User profile data
            analysis_results (dict): Results from sentiment analysis
            network_results (dict): Results from network analysis (optional)
            filename (str): Output filename (optional)
            
        Returns:
            str: Path to the saved report
        """
        if not filename:
            timestamp = int(time.time())
            username = user_data.get('username', 'unknown')
            platform = user_data.get('platform', 'unknown')
            filename = f"forensic_report_{username}_{platform}_{timestamp}.pdf"
            
        output_path = os.path.join(self.output_dir, filename)
        
        # Create PDF document
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(190, 10, 'Social Media Forensic Analysis Report', 0, 1, 'C')
        
        # Add timestamp
        pdf.set_font('Arial', 'I', 10)
        report_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        pdf.cell(190, 5, f'Generated on: {report_date}', 0, 1, 'C')
        pdf.ln(5)
        
        # User Profile Section
        pdf.set_font('Arial', 'B', self.section_font_size)
        pdf.cell(190, self.line_height, 'User Profile', 0, 1, 'L')
        pdf.ln(2)
        
        pdf.set_font('Arial', '', self.text_font_size)
        profile_data = [
            ('Username', user_data.get('username', 'N/A')),
            ('Platform', user_data.get('platform', 'N/A')),
            ('Followers', str(user_data.get('followers', 'N/A'))),
            ('Following', str(user_data.get('following', 'N/A'))),
            ('Bio', user_data.get('bio', 'N/A'))
        ]
        
        for label, value in profile_data:
            pdf.cell(40, self.line_height, label + ':', 0, 0, 'L')
            pdf.cell(150, self.line_height, str(value), 0, 1, 'L')
        
        pdf.ln(5)
        
        # Sentiment Analysis Section
        pdf.set_font('Arial', 'B', self.section_font_size)
        pdf.cell(190, self.line_height, 'Sentiment Analysis', 0, 1, 'L')
        pdf.ln(2)
        
        # Add sentiment chart
        sentiment_chart = self._create_sentiment_chart(analysis_results.get('sentiment_analysis', {}))
        if sentiment_chart:
            pdf.image(sentiment_chart, x=10, w=190)
        
        pdf.ln(5)
        
        # Timeline Section
        pdf.set_font('Arial', 'B', self.section_font_size)
        pdf.cell(190, self.line_height, 'Posting Activity', 0, 1, 'L')
        pdf.ln(2)
        
        # Add timeline chart
        timeline_chart = self._create_posting_timeline(user_data.get('posts', []))
        if timeline_chart:
            pdf.image(timeline_chart, x=10, w=190)
        
        pdf.ln(5)
        
        # Content Analysis Section
        pdf.set_font('Arial', 'B', self.section_font_size)
        pdf.cell(190, self.line_height, 'Content Analysis', 0, 1, 'L')
        pdf.ln(2)
        
        # Add wordcloud
        wordcloud = self._create_wordcloud(
            analysis_results.get('sentiment_analysis', {}),
            user_data.get('posts', [])
        )
        if wordcloud:
            pdf.image(wordcloud, x=10, w=190)
        
        pdf.ln(5)
        
        # Network Analysis Section
        if network_results:
            pdf.add_page()
            pdf.set_font('Arial', 'B', self.section_font_size)
            pdf.cell(190, self.line_height, 'Network Analysis', 0, 1, 'L')
            pdf.ln(2)
            
            # Add network visualization
            network_graph = self._create_network_graph(network_results)
            if network_graph:
                pdf.image(network_graph, x=10, w=190)
            
            # Add network metrics
            pdf.set_font('Arial', '', self.text_font_size)
            
            if network_results.get('influential_nodes'):
                pdf.ln(5)
                pdf.set_font('Arial', 'B', self.text_font_size)
                pdf.cell(190, self.line_height, 'Influential Connections:', 0, 1, 'L')
                pdf.set_font('Arial', '', self.text_font_size)
                for node in network_results['influential_nodes'][:5]:
                    pdf.cell(190, self.line_height, f"• {node}", 0, 1, 'L')
            
            if network_results.get('suspicious_connections'):
                pdf.ln(5)
                pdf.set_font('Arial', 'B', self.text_font_size)
                pdf.cell(190, self.line_height, 'Suspicious Patterns:', 0, 1, 'L')
                pdf.set_font('Arial', '', self.text_font_size)
                for conn in network_results['suspicious_connections'][:5]:
                    pdf.cell(190, self.line_height, f"• {conn}", 0, 1, 'L')
        
        # Save the PDF
        pdf.output(output_path)
        
        return output_path 