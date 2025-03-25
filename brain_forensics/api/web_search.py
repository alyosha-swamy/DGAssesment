import requests
import time
import json
import os
import random
from bs4 import BeautifulSoup
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class WebSearchAPI:
    """
    Class to simulate social media API functionality by using web search
    """
    def __init__(self, api_key=None):
        self.api_key = api_key or config.TAVILY_API_KEY
        self.cache_dir = os.path.join(config.DATA_DIR, "search_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _get_cache_path(self, query):
        """Generate cache file path based on query"""
        # Create a filename-safe version of the query
        safe_query = "".join(c if c.isalnum() else "_" for c in query)
        return os.path.join(self.cache_dir, f"{safe_query[:50]}.json")
    
    def _get_from_cache(self, query):
        """Try to get results from cache"""
        cache_path = self._get_cache_path(query)
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None
    
    def _save_to_cache(self, query, results):
        """Save results to cache"""
        cache_path = self._get_cache_path(query)
        with open(cache_path, 'w') as f:
            json.dump(results, f)
    
    def search(self, query, platform=None):
        """
        Search for information about a user on social media
        
        Args:
            query (str): Search query (usually username)
            platform (str): Specific platform to search on (twitter, facebook, etc.)
            
        Returns:
            dict: Search results
        """
        # Check cache first
        cached_results = self._get_from_cache(query)
        if cached_results:
            return cached_results
            
        # In a real implementation, we'd use Tavily or other search API here
        # For the prototype, we'll simulate results
        simulated_results = self._simulate_search_results(query, platform)
        
        # Cache the results
        self._save_to_cache(query, simulated_results)
        
        return simulated_results
    
    def _simulate_search_results(self, query, platform=None):
        """Generate simulated search results for prototype"""
        platforms = [platform] if platform else config.PLATFORMS
        results = []
        
        for p in platforms:
            # Simulate 3-7 posts per platform
            num_posts = random.randint(3, 7)
            platform_results = []
            
            for i in range(num_posts):
                # Create a simulated post
                post = self._create_simulated_post(query, p, i)
                platform_results.append(post)
            
            results.append({
                "platform": p,
                "user": query,
                "posts": platform_results,
                "profile": self._create_simulated_profile(query, p)
            })
        
        return {
            "query": query,
            "timestamp": time.time(),
            "results": results
        }
    
    def _create_simulated_post(self, user, platform, index):
        """Create a simulated social media post"""
        # List of potential content templates
        templates = [
            "Just shared my thoughts on {topic}. What do you think?",
            "Can't believe what's happening with {topic} right now!",
            "This {topic} situation is getting out of hand. #concerned",
            "Really enjoyed learning about {topic} today. #learning",
            "Anyone else following the {topic} controversy?",
            "{topic} is the best thing ever. Change my mind.",
            "This article about {topic} is completely false! Don't believe it!",
            "Breaking: New developments in the {topic} case. #news",
            "My hot take on {topic} - controversial but true.",
            "So tired of all the {topic} misinformation spreading around."
        ]
        
        # List of potential topics
        topics = [
            "climate change", "cryptocurrency", "election", "pandemic", 
            "vaccine", "technology", "privacy concerns", "data leaks",
            "artificial intelligence", "market crash", "political scandal"
        ]
        
        # Generate random timestamp within last 30 days
        timestamp = time.time() - random.randint(0, 30*24*60*60)
        date_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        
        # Randomly select content template and topic
        content_template = random.choice(templates)
        topic = random.choice(topics)
        content = content_template.replace("{topic}", topic)
        
        # Add some platform-specific features
        if platform == "twitter":
            content += " #trending"
            likes = random.randint(0, 1000)
            shares = random.randint(0, 200)
            comments = random.randint(0, 50)
        elif platform == "facebook":
            likes = random.randint(0, 500)
            shares = random.randint(0, 100)
            comments = random.randint(0, 200)
        elif platform == "instagram":
            content += " #picoftheday"
            likes = random.randint(0, 2000)
            shares = 0
            comments = random.randint(0, 100)
        else:  # linkedin
            content = "Professional post: " + content
            likes = random.randint(0, 300)
            shares = random.randint(0, 50)
            comments = random.randint(0, 30)
        
        # Occasionally add a URL
        has_url = random.random() < 0.3
        url = f"https://example.com/article{random.randint(1000, 9999)}" if has_url else ""
        
        # Sometimes add location data
        has_location = random.random() < 0.2
        locations = ["New York", "San Francisco", "London", "Tokyo", "Sydney", "Berlin"]
        location = random.choice(locations) if has_location else ""
        
        # Device info
        devices = ["iPhone", "Android", "Web", "iPad", "Desktop"]
        device = random.choice(devices)
        
        # Generate a post ID
        post_id = f"{platform}_{user}_{int(timestamp)}"
        
        return {
            "id": post_id,
            "content": content,
            "timestamp": timestamp,
            "date": date_str,
            "likes": likes,
            "shares": shares,
            "comments": comments,
            "url": url,
            "location": location,
            "device": device,
            "platform": platform
        }
    
    def _create_simulated_profile(self, user, platform):
        """Create a simulated user profile"""
        # Choose a random creation date (1-5 years ago)
        days_ago = random.randint(365, 5*365)
        created_timestamp = time.time() - (days_ago * 24 * 60 * 60)
        created_date = time.strftime("%Y-%m-%d", time.localtime(created_timestamp))
        
        # Random follower/following counts
        if random.random() < 0.1:  # 10% chance of being a potential bot/influential account
            followers = random.randint(10000, 1000000)
            following = random.randint(10, 1000)
            is_suspicious = True
        else:
            followers = random.randint(50, 5000)
            following = random.randint(50, 2000)
            is_suspicious = False
        
        # Post frequency (posts per day on average)
        post_frequency = round(random.uniform(0.1, 10), 2)
        
        # Profile completeness (percentage)
        profile_completeness = random.randint(30, 100)
        
        # Verification status
        verified = random.random() < 0.2
        
        # Bio text
        bio_templates = [
            f"Just a regular {user} sharing thoughts",
            f"Official account of {user}",
            f"{platform.capitalize()} enthusiast | Thoughts are my own",
            f"Living life to the fullest | {random.choice(['Writer', 'Speaker', 'Thinker', 'Creator'])}",
            ""  # Empty bio
        ]
        bio = random.choice(bio_templates)
        
        return {
            "username": user,
            "platform": platform,
            "created_date": created_date,
            "followers": followers,
            "following": following,
            "post_frequency": post_frequency,
            "profile_completeness": profile_completeness,
            "verified": verified,
            "bio": bio,
            "is_suspicious": is_suspicious
        } 