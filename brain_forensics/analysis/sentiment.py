import nltk
import os
import sys
import re
from textblob import TextBlob
import pandas as pd
from collections import Counter
import joblib

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Download necessary NLTK data
try:
    os.makedirs(config.NLTK_DATA_PATH, exist_ok=True)
    nltk.data.path.append(config.NLTK_DATA_PATH)
    nltk.download('punkt', download_dir=config.NLTK_DATA_PATH, quiet=True)
    nltk.download('stopwords', download_dir=config.NLTK_DATA_PATH, quiet=True)
    nltk.download('wordnet', download_dir=config.NLTK_DATA_PATH, quiet=True)
except Exception as e:
    print(f"Warning: Failed to download NLTK data: {e}")

class SentimentAnalyzer:
    """
    Analyze sentiment of social media posts
    """
    def __init__(self):
        self.cache_dir = os.path.join(config.DATA_DIR, "sentiment_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        try:
            self.stopwords = set(nltk.corpus.stopwords.words('english'))
        except:
            self.stopwords = set(['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 
                                 'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 
                                 'his', 'himself', 'she', 'her', 'hers', 'herself'])
    
    def _clean_text(self, text):
        """Clean and preprocess text for analysis"""
        if not text:
            return ""
            
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        
        # Remove mentions
        text = re.sub(r'@\w+', '', text)
        
        # Remove hashtags but keep the text
        text = re.sub(r'#(\w+)', r'\1', text)
        
        # Remove special characters
        text = re.sub(r'[^\w\s]', '', text)
        
        # Convert to lowercase
        text = text.lower()
        
        return text
    
    def analyze_post(self, post):
        """
        Analyze sentiment of a single post
        
        Args:
            post (dict): Post data with content field
            
        Returns:
            dict: Sentiment analysis results
        """
        content = post.get('content', '')
        cleaned_text = self._clean_text(content)
        
        if not cleaned_text:
            return {
                'sentiment_score': 0,
                'sentiment_label': 'neutral',
                'subjectivity': 0,
                'keywords': [],
                'word_count': 0
            }
        
        # Use TextBlob for sentiment analysis
        blob = TextBlob(cleaned_text)
        sentiment_score = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Determine sentiment label
        if sentiment_score <= config.SENTIMENT_THRESHOLD_NEGATIVE:
            sentiment_label = 'negative'
        elif sentiment_score >= config.SENTIMENT_THRESHOLD_POSITIVE:
            sentiment_label = 'positive'
        else:
            sentiment_label = 'neutral'
        
        # Extract keywords (words not in stopwords)
        words = [word for word in blob.words if word.lower() not in self.stopwords and len(word) > 2]
        word_count = len(words)
        
        # Get most common words as keywords
        keywords = [word for word, count in Counter(words).most_common(5)]
        
        return {
            'sentiment_score': sentiment_score,
            'sentiment_label': sentiment_label,
            'subjectivity': subjectivity,
            'keywords': keywords,
            'word_count': word_count
        }
    
    def analyze_user_posts(self, user_data):
        """
        Analyze all posts for a user
        
        Args:
            user_data (dict): User data containing posts
            
        Returns:
            dict: Sentiment analysis results for all posts
        """
        results = {
            'username': user_data.get('user', ''),
            'platform': user_data.get('platform', ''),
            'sentiment_scores': [],
            'sentiment_distribution': {
                'positive': 0,
                'neutral': 0,
                'negative': 0
            },
            'average_sentiment': 0,
            'top_keywords': [],
            'suspicious_content': []
        }
        
        posts = user_data.get('posts', [])
        if not posts:
            return results
            
        # Analyze each post
        sentiment_scores = []
        all_keywords = []
        
        for post in posts:
            analysis = self.analyze_post(post)
            
            # Add sentiment score to list
            sentiment_scores.append(analysis['sentiment_score'])
            
            # Update sentiment distribution
            results['sentiment_distribution'][analysis['sentiment_label']] += 1
            
            # Add keywords to list
            all_keywords.extend(analysis['keywords'])
            
            # Check for suspicious content
            if analysis['sentiment_score'] < -0.5 and analysis['subjectivity'] > 0.7:
                suspicious_content = {
                    'post_id': post.get('id', ''),
                    'content': post.get('content', ''),
                    'sentiment_score': analysis['sentiment_score'],
                    'subjectivity': analysis['subjectivity'],
                    'reason': 'Highly negative and subjective content'
                }
                results['suspicious_content'].append(suspicious_content)
                
            # Attach analysis to post
            post['sentiment_analysis'] = analysis
        
        # Calculate average sentiment
        results['average_sentiment'] = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        results['sentiment_scores'] = sentiment_scores
        
        # Get top keywords
        keyword_counts = Counter(all_keywords)
        results['top_keywords'] = [word for word, count in keyword_counts.most_common(10)]
        
        return results
    
    def detect_anomalies(self, user_data):
        """
        Detect anomalies in posting patterns and sentiment
        
        Args:
            user_data (dict): User data containing posts and sentiment analysis
            
        Returns:
            dict: Detected anomalies
        """
        anomalies = []
        posts = user_data.get('posts', [])
        
        if len(posts) < 2:
            return anomalies
            
        # Convert timestamps to pandas series for time series analysis
        timestamps = pd.Series([post['timestamp'] for post in posts]).sort_values()
        
        # Look for unusually rapid posting (more than 3 posts within 1 hour)
        if len(timestamps) > 3:
            for i in range(len(timestamps) - 3):
                window = timestamps[i:i+3]
                time_diff = window.max() - window.min()
                
                # If 3 posts within 1 hour (3600 seconds)
                if time_diff < 3600:
                    start_time = pd.to_datetime(window.min(), unit='s')
                    anomaly = {
                        'type': 'rapid_posting',
                        'description': f'Unusually rapid posting detected: 3 posts within {time_diff/60:.1f} minutes',
                        'timestamp': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'severity': 'medium'
                    }
                    anomalies.append(anomaly)
        
        # Look for sudden changes in sentiment
        sentiment_scores = user_data.get('sentiment_scores', [])
        if len(sentiment_scores) > 2:
            for i in range(len(sentiment_scores) - 1):
                change = abs(sentiment_scores[i+1] - sentiment_scores[i])
                
                # If sentiment changes dramatically (threshold: 0.7)
                if change > 0.7:
                    anomaly = {
                        'type': 'sentiment_change',
                        'description': f'Sudden change in sentiment detected: shift of {change:.2f}',
                        'post_index': i+1,
                        'severity': 'high' if change > 0.9 else 'medium'
                    }
                    anomalies.append(anomaly)
        
        return anomalies 