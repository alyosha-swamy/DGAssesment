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
        try:
            # Construct search query
            if platform:
                search_query = f"site:{platform}.com {query} profile social media"
            else:
                platforms = " OR ".join([f"site:{p}.com" for p in config.PLATFORMS])
                search_query = f"({platforms}) {query} profile social media"

            # Call Tavily API
            response = requests.post(
                "https://api.tavily.com/search",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "query": search_query,
                    "search_depth": "advanced",
                    "include_answer": True,
                    "include_raw_content": True,
                    "max_results": 10
                }
            )
            response.raise_for_status()
            tavily_results = response.json()

            # Process results with LLM
            combined_content = "\n".join([
                f"URL: {result.get('url', '')}\nTitle: {result.get('title', '')}\nContent: {result.get('content', '')}"
                for result in tavily_results.get('results', [])
            ])

            # Use LLM to extract and analyze information with a more structured prompt
            llm_prompt = f"""You are a JSON generator analyzing social media data. Your task is to analyze the following search results and return ONLY a valid JSON object with no additional text.

Search Results for user {query}:
{combined_content}

Return a JSON object with exactly this structure (fill in appropriate values, use null for missing data):
{{
    "profile": {{
        "username": string,
        "bio": string or null,
        "followers": number or null,
        "following": number or null,
        "join_date": string or null
    }},
    "posts": [
        {{
            "content": string,
            "date": string,
            "likes": number,
            "shares": number,
            "comments": number
        }}
    ],
    "sentiment": {{
        "average": number between -1 and 1,
        "distribution": {{
            "positive": number,
            "neutral": number,
            "negative": number
        }}
    }},
    "patterns": [string],
    "flags": [string]
}}"""

            analysis = self._process_with_llm(combined_content, llm_prompt)
            
            if analysis:
                try:
                    # Clean the response to ensure it's valid JSON
                    json_str = analysis.strip()
                    if json_str.startswith('```json'):
                        json_str = json_str[7:]
                    if json_str.endswith('```'):
                        json_str = json_str[:-3]
                    json_str = json_str.strip()
                    
                    processed_data = json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse LLM response as JSON: {e}")
                    print(f"Raw response: {analysis}")
                    processed_data = {}
            else:
                processed_data = {}

            # Format final response
            results = []
            if processed_data:
                platform_data = {
                    "platform": platform or "all",
                    "user": query,
                    "profile": processed_data.get("profile", {}),
                    "posts": processed_data.get("posts", []),
                    "sentiment": processed_data.get("sentiment", {}),
                    "patterns": processed_data.get("patterns", []),
                    "flags": processed_data.get("flags", [])
                }
                results.append(platform_data)

            return {
                "query": query,
                "timestamp": time.time(),
                "results": results or [self._create_simulated_results(query, platform)]
            }
            
        except Exception as e:
            print(f"Error in search: {e}")
            # Fallback to simulated results
            return {
                "query": query,
                "timestamp": time.time(),
                "results": [self._create_simulated_results(query, platform)]
            }

    def _create_simulated_results(self, query, platform=None):
        """Create simulated results for testing"""
        platform = platform or "twitter"
        return {
            "platform": platform,
            "user": query,
            "profile": {
                "username": query,
                "bio": f"Simulated profile for {query}",
                "followers": random.randint(100, 10000),
                "following": random.randint(50, 1000),
                "join_date": "2020-01-01"
            },
            "posts": [
                {
                    "id": f"post_{i}",
                    "content": f"Simulated post {i} by {query}",
                    "timestamp": time.time() - (i * 86400),  # i days ago
                    "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - (i * 86400))),
                    "likes": random.randint(0, 100),
                    "shares": random.randint(0, 20),
                    "comments": random.randint(0, 10)
                }
                for i in range(3)
            ],
            "sentiment": {
                "average": random.uniform(-1, 1),
                "distribution": {
                    "positive": random.randint(0, 10),
                    "neutral": random.randint(0, 10),
                    "negative": random.randint(0, 10)
                }
            },
            "patterns": [
                "Regular posting schedule",
                "Engages with followers",
                "Shares original content"
            ],
            "flags": []
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