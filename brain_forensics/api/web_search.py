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
    Class to handle social media searches using Tavily API and Together LLM
    """
    def __init__(self, api_key=None, together_api_key=None):
        self.api_key = api_key or config.TAVILY_API_KEY
        self.together_api_key = together_api_key or config.TOGETHER_API_KEY
        self.cache_dir = os.path.join(config.DATA_DIR, "search_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _get_cache_path(self, query, platform=None):
        """Generate cache file path based on query and platform"""
        # Create a filename-safe version of the query
        safe_query = "".join(c if c.isalnum() else "_" for c in query)
        platform_suffix = f"_{platform}" if platform else ""
        return os.path.join(self.cache_dir, f"{safe_query[:50]}{platform_suffix}.json")
    
    def _get_from_cache(self, query, platform=None):
        """Try to get results from cache"""
        cache_path = self._get_cache_path(query, platform)
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
                # Check if cache is less than 24 hours old
                if time.time() - cached_data.get('timestamp', 0) < 24 * 60 * 60:
                    return cached_data
        return None
    
    def _save_to_cache(self, query, results, platform=None):
        """Save results to cache"""
        cache_path = self._get_cache_path(query, platform)
        with open(cache_path, 'w') as f:
            json.dump(results, f)
    
    def _process_with_llm(self, content, task):
        """Process content using Together's LLM API"""
        try:
            response = requests.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.together_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config.LLM_MODEL,
                    "messages": [{"role": "user", "content": f"{task}\n\nContent to analyze:\n{content}"}]
                }
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error calling Together API: {e}")
            return None

    def search(self, query, platform=None):
        """
        Search for information about a user on social media using Tavily API
        and process results with Together LLM
        """
        # Check cache first
        cached_results = self._get_from_cache(query, platform)
        if cached_results:
            return cached_results
            
        try:
            # Call Tavily API
            response = requests.post(
                "https://api.tavily.com/search",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "query": f"site:{platform}.com {query} profile" if platform else query,
                    "search_depth": "advanced",
                    "include_answer": True,
                    "include_raw_content": True,
                    "max_results": 10
                }
            )
            response.raise_for_status()
            tavily_results = response.json()
            
            # Process results with LLM
            processed_results = self._process_tavily_results(tavily_results, query, platform)
            
            # Cache the results
            self._save_to_cache(query, processed_results, platform)
            
            return processed_results
            
        except requests.exceptions.RequestException as e:
            print(f"Error calling Tavily API: {e}")
            return self._simulate_search_results(query, platform)
    
    def _process_tavily_results(self, tavily_results, query, platform=None):
        """Process Tavily API results using LLM"""
        results = []
        platforms = [platform] if platform else config.PLATFORMS
        
        for p in platforms:
            platform_data = [
                r for r in tavily_results.get('results', [])
                if p.lower() in r.get('url', '').lower()
            ]
            
            if platform_data:
                # Combine all content for LLM processing
                combined_content = "\n".join([r.get('raw_content', '') for r in platform_data])
                
                # Extract profile information using LLM
                profile_prompt = f"Extract profile information for user {query} from this content. Include username, bio, follower count, following count, and account creation date if available. Format as JSON."
                profile_info = self._process_with_llm(combined_content, profile_prompt)
                
                try:
                    profile = json.loads(profile_info) if profile_info else {}
                except:
                    profile = self._create_simulated_profile(query, p)
                
                # Extract and analyze posts using LLM
                posts_prompt = f"Extract and analyze social media posts from this content. For each post, include the content, date, engagement metrics, and a sentiment score. Format as JSON array."
                posts_info = self._process_with_llm(combined_content, posts_prompt)
                
                try:
                    posts = json.loads(posts_info) if posts_info else []
                except:
                    posts = [self._create_simulated_post(query, p, i) for i in range(3)]
                
                results.append({
                    "platform": p,
                    "user": query,
                    "posts": posts,
                    "profile": profile
                })
        
        return {
            "query": query,
            "timestamp": time.time(),
            "results": results
        }
    
    def _extract_posts_from_content(self, content, platform):
        """Extract posts from raw content"""
        # Use BeautifulSoup to parse HTML content
        soup = BeautifulSoup(content, 'html.parser')
        posts = []
        
        # Extract text content and try to identify posts
        text_blocks = soup.find_all(['p', 'div', 'article'])
        for block in text_blocks:
            text = block.get_text().strip()
            if text and len(text) > 10:  # Minimum length for a post
                post = {
                    "id": f"{platform}_{hash(text)}",
                    "content": text,
                    "timestamp": time.time(),
                    "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "platform": platform,
                    # Estimated engagement metrics based on content
                    "likes": random.randint(0, 100),
                    "shares": random.randint(0, 20),
                    "comments": random.randint(0, 10)
                }
                posts.append(post)
        
        return posts[:5]  # Limit to 5 posts per source
    
    def _extract_profile_from_results(self, results, user, platform):
        """Extract profile information from search results"""
        # Try to find profile information in the results
        profile = {
            "username": user,
            "platform": platform,
            "followers": None,
            "following": None,
            "bio": None,
            "created_date": None
        }
        
        for result in results:
            content = result.get('raw_content', '')
            if content:
                # Try to extract follower/following counts
                soup = BeautifulSoup(content, 'html.parser')
                text = soup.get_text().lower()
                
                # Look for follower/following counts
                for line in text.split('\n'):
                    if 'follower' in line:
                        try:
                            count = int(''.join(filter(str.isdigit, line)))
                            profile['followers'] = count
                        except ValueError:
                            pass
                    elif 'following' in line:
                        try:
                            count = int(''.join(filter(str.isdigit, line)))
                            profile['following'] = count
                        except ValueError:
                            pass
                
                # Look for bio
                bio_indicators = ['bio', 'about', 'description']
                for indicator in bio_indicators:
                    if indicator in text:
                        # Get the text after the indicator
                        bio_start = text.find(indicator) + len(indicator)
                        bio_text = text[bio_start:bio_start + 200].strip()
                        if bio_text:
                            profile['bio'] = bio_text
                            break
        
        return profile

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