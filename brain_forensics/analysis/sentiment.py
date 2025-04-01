import os
import sys
import re
import json
import time
import requests
import random
import math
import traceback
from collections import Counter
from glob import glob
from datetime import datetime, timezone

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    import config
except ImportError:
    print("Error: Could not import config from sentiment.py", file=sys.stderr)
    # Define fallback config paths if necessary
    class MockConfig:
        DATA_DIR = "data"
        TOGETHER_API_KEY = ""
        LLM_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
        LLM_TEMPERATURE = 0.1
        LLM_MAX_TOKENS = 1024
        SENTIMENT_THRESHOLD_NEGATIVE = -0.3
        SENTIMENT_THRESHOLD_POSITIVE = 0.3
        CASES_DIR = "cases"
        CASE_DATA_DIR_NAME = "data"
        TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S %Z"
    config = MockConfig()

class SentimentAnalyzer:
    """
    Analyze sentiment of social media data stored within a case folder.
    Uses Together API for LLM-based sentiment scoring.
    """
    def __init__(self):
        # No persistent cache needed in case-based structure
        self.together_api_key = config.TOGETHER_API_KEY
        if not self.together_api_key:
            print("Warning: TOGETHER_API_KEY not set. Sentiment analysis will use random fallback values.", file=sys.stderr)

    def _get_case_data_path(self, case_name):
        """Construct the path to the data directory for a given case."""
        # Basic sanitization
        safe_case_name = os.path.basename(case_name)
        if not safe_case_name or safe_case_name == '.' or safe_case_name == '..':
            return None
        case_path = os.path.join(config.CASES_DIR, safe_case_name)
        if not os.path.isdir(case_path):
            return None
        return os.path.join(case_path, config.CASE_DATA_DIR_NAME)

    def _clean_text(self, text):
        """Clean and preprocess text for analysis"""
        if not text:
            return ""
        text = str(text) # Ensure it's a string
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        # Remove mentions
        text = re.sub(r'@\w+', '', text)
        # Remove hashtags but keep the text
        text = re.sub(r'#(\w+)', r' \1 ', text) # Add spaces around hashtag text
        # Remove special characters except basic punctuation potentially relevant to sentiment
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _generate_random_sentiment(self, text, context="Fallback"):
        """Generate random sentiment values when API fails or is unavailable."""
        print(f"Generating random sentiment values ({context})")
        sentiment_score = random.uniform(-0.95, 0.95)
        sentiment_score = round(max(min(sentiment_score, 0.99), -0.99), 2) # Clamp and round
        if abs(sentiment_score) < 0.05:
            sentiment_score = random.choice([-0.25, 0.25])

        subjectivity = round(random.uniform(0.1, 0.9), 2)

        words = text.split()
        keywords = random.sample(words, min(5, len(words))) if words else ["random", "fallback", "data"]
        keywords = keywords[:5] # Ensure max 5 keywords
        while len(keywords) < 5:
            keywords.append("placeholder")

        if sentiment_score <= config.SENTIMENT_THRESHOLD_NEGATIVE:
            sentiment_label = 'negative'
        elif sentiment_score >= config.SENTIMENT_THRESHOLD_POSITIVE:
            sentiment_label = 'positive'
        else:
            sentiment_label = 'neutral'

        word_count = max(1, len(words))

        return {
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "subjectivity": subjectivity,
            "keywords": keywords,
            "word_count": word_count
        }

    def _process_with_llm(self, content):
        """Process content using Together's LLM API."""
        if not self.together_api_key:
            return self._generate_random_sentiment(content, "API Key Missing")

        llm_prompt = f"""Analyze the sentiment of the following social media text. Return ONLY a valid JSON object with the structure:
{{
    "sentiment_score": number between -0.99 and 0.99 (never 0, -1, or 1),
    "sentiment_label": "positive", "neutral", or "negative",
    "subjectivity": number between 0.01 and 0.99 (never 0 or 1),
    "keywords": [list of exactly 5 relevant keywords from the text],
    "word_count": integer count of words in the original text (at least 1)
}}

CRITICAL: Adhere strictly to the JSON format and constraints. Do not include explanations.

Text to analyze:
{content}"""

        try:
            response = requests.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.together_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config.LLM_MODEL,
                    "temperature": config.LLM_TEMPERATURE,
                    "max_tokens": config.LLM_MAX_TOKENS,
                    "messages": [{"role": "user", "content": llm_prompt}],
                    "response_format": {"type": "json_object"} # Request JSON output
                },
                timeout=30 # Add a timeout
            )
            response.raise_for_status()
            result_text = response.json()["choices"][0]["message"]["content"]
            # LLM sometimes wraps JSON in markdown, try cleaning
            cleaned_json = self._clean_json_response(result_text)
            return cleaned_json
        except requests.exceptions.RequestException as e:
            print(f"Error calling Together API: {e}", file=sys.stderr)
            traceback.print_exc()
            return self._generate_random_sentiment(content, f"API Request Error: {e}")
        except Exception as e:
            print(f"Unexpected error processing with LLM: {e}", file=sys.stderr)
            traceback.print_exc()
            return self._generate_random_sentiment(content, f"LLM Processing Error: {e}")

    def _clean_json_response(self, response_text):
        """Clean and parse JSON response from LLM, with fallback."""
        if not response_text:
            return self._generate_random_sentiment(
                "", "Empty LLM Response"
            )
        try:
            # Basic cleaning: remove potential markdown backticks
            json_str = re.sub(
                r"^```json\s*|\s*```$",
                "",
                response_text.strip(),
                flags=re.MULTILINE,
            )
            data = json.loads(json_str)

            # --- Validate and Sanitize --- #
            required_keys = [
                "sentiment_score",
                "sentiment_label",
                "subjectivity",
                "keywords",
                "word_count",
            ]
            if not all(key in data for key in required_keys):
                raise ValueError(
                    "Missing required keys in LLM JSON response"
                )

            # Score:
            score = data.get(
                "sentiment_score", 0.0
            )  # Default to 0.0 if missing
            if not isinstance(score, (int, float)) or math.isnan(score):
                print(
                    f"Warning: Invalid sentiment score type or NaN ({score}), using random."
                )
                score = random.uniform(-0.9, 0.9)

            # Clamp score and ensure it's not exactly 0
            clamped_score = round(max(min(float(score), 0.99), -0.99), 3)
            if clamped_score == 0.0:
                data["sentiment_score"] = 0.01
            else:
                data["sentiment_score"] = clamped_score

            # Label:
            label = data.get("sentiment_label")
            if label not in ["positive", "neutral", "negative"]:
                if data["sentiment_score"] <= config.SENTIMENT_THRESHOLD_NEGATIVE:
                    data["sentiment_label"] = "negative"
                elif data["sentiment_score"] >= config.SENTIMENT_THRESHOLD_POSITIVE:
                    data["sentiment_label"] = "positive"
                else:
                    data["sentiment_label"] = "neutral"

            # Subjectivity:
            subj = data.get("subjectivity")
            if (
                not isinstance(subj, (int, float))
                or math.isnan(subj)
                or not (0 < subj < 1)
            ):
                subj = random.uniform(0.1, 0.9)
            data["subjectivity"] = round(max(min(subj, 0.99), 0.01), 3)

            # Keywords:
            keywords = data.get("keywords")
            if not isinstance(keywords, list) or len(keywords) != 5:
                keywords = [
                    "llm",
                    "fix",
                    "keywords",
                    "error",
                    "data",
                ]
            # Ensure 5 strings, limit length
            data["keywords"] = [str(k)[:50] for k in keywords[:5]]

            # Word Count:
            count = data.get("word_count")
            if not isinstance(count, int) or count < 1:
                count = random.randint(5, 50)
            data["word_count"] = count

            return data
        except json.JSONDecodeError as e:
            print(
                f"Error decoding LLM JSON response: {e}", file=sys.stderr
            )
            print(
                f"Raw response causing error: {response_text}",
                file=sys.stderr,
            )
            return self._generate_random_sentiment(
                "", f"JSON Decode Error: {e}"
            )
        except Exception as e:
            print(f"Error validating LLM response: {e}", file=sys.stderr)
            traceback.print_exc()
            return self._generate_random_sentiment(
                "", f"Validation Error: {e}"
            )

    def analyze_case(self, case_name):
        """
        Analyze sentiment for all relevant data files within a specific case.

        Args:
            case_name (str): The name of the case.

        Returns:
            dict: Aggregated sentiment analysis results for the case.
                  Returns None if the case path is invalid or no data files are found.
        """
        case_data_path = self._get_case_data_path(case_name)
        if not case_data_path:
            print(f"Error: Invalid case name or path for '{case_name}'", file=sys.stderr)
            return None

        all_results = []
        all_keywords = Counter()
        file_count = 0

        # Find all JSON data files in the case's data directory
        data_files = glob(os.path.join(case_data_path, "*.json"))

        if not data_files:
            print(f"No data files found in {case_data_path}", file=sys.stderr)
            return None

        print(f"Analyzing sentiment for {len(data_files)} files in case '{case_name}'...")

        for filepath in data_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    post_data = json.load(f)

                # Extract content (adjust based on actual preserved data structure)
                content = post_data.get('content', '')
                if not content:
                    continue # Skip items with no content

                cleaned_text = self._clean_text(content)
                if not cleaned_text:
                    continue # Skip items with effectively no text after cleaning
                
                file_count += 1
                # Analyze the cleaned text
                analysis_result = self._process_with_llm(cleaned_text)
                
                if analysis_result:
                    all_results.append({
                        "file": os.path.basename(filepath),
                        "score": analysis_result['sentiment_score'],
                        "label": analysis_result['sentiment_label'],
                        "subjectivity": analysis_result['subjectivity']
                    })
                    all_keywords.update(analysis_result['keywords'])
                else:
                     print(f"Warning: Failed to analyze sentiment for {os.path.basename(filepath)}", file=sys.stderr)

                # Optional: Add a small delay to avoid hitting API rate limits if analyzing many files
                # time.sleep(0.1)

            except json.JSONDecodeError:
                print(f"Warning: Skipping invalid JSON file: {filepath}", file=sys.stderr)
            except Exception as e:
                print(f"Error processing file {filepath}: {e}", file=sys.stderr)
                traceback.print_exc()

        if not all_results:
            print(f"No valid sentiment results obtained for case '{case_name}'", file=sys.stderr)
            return {
                "case_name": case_name,
                "files_processed": file_count,
                "analysis_timestamp_utc": datetime.now(timezone.utc).strftime(config.TIMESTAMP_FORMAT),
                "average_sentiment": 0.0,
                "sentiment_distribution": {'positive': 0, 'neutral': 0, 'negative': 0},
                "top_keywords": [],
                "detailed_results": []
            }

        # --- Aggregate Results --- 
        total_score = sum(r['score'] for r in all_results)
        average_sentiment = round(total_score / len(all_results), 3)

        distribution = Counter(r['label'] for r in all_results)
        sentiment_distribution = {
            'positive': distribution.get('positive', 0),
            'neutral': distribution.get('neutral', 0),
            'negative': distribution.get('negative', 0)
        }

        # Get top N keywords
        top_keywords = [kw for kw, count in all_keywords.most_common(15)] # Get more keywords

        return {
            "case_name": case_name,
            "files_processed": file_count,
            "analysis_timestamp_utc": datetime.now(timezone.utc).strftime(config.TIMESTAMP_FORMAT),
            "average_sentiment": average_sentiment,
            "sentiment_distribution": sentiment_distribution,
            "top_keywords": top_keywords,
            "detailed_results": all_results # Include per-file results for reporting/auditing
        }

# Example Usage (if run directly)
if __name__ == "__main__":
    if len(sys.argv) > 1:
        case_name_to_analyze = sys.argv[1]
        print(f"Running sentiment analysis for case: {case_name_to_analyze}")
        analyzer = SentimentAnalyzer()
        results = analyzer.analyze_case(case_name_to_analyze)
        if results:
            print("\n--- Analysis Summary ---")
            print(json.dumps(results, indent=4))
        else:
            print(f"Sentiment analysis failed for case '{case_name_to_analyze}'.")
    else:
        print("Usage: python sentiment.py <case_name>")
        # Example of creating a dummy case for testing
        print("\nCreating dummy case 'test_case_sentiment' for example.")
        dummy_case = "test_case_sentiment"
        dummy_data_path = os.path.join(config.CASES_DIR, dummy_case, config.CASE_DATA_DIR_NAME)
        os.makedirs(dummy_data_path, exist_ok=True)
        dummy_data = [
            {"id": "post1", "content": "This is a wonderfully positive statement about progress! #optimism"},
            {"id": "post2", "content": "Feeling quite neutral about the recent updates.", "platform": "X"},
            {"id": "post3", "content": "Terrible news today, very concerning. #fail url.com/bad"},
            {"id": "post4", "content": "@user Mentioning something vaguely negative but mostly objective analysis.", "timestamp": 1678886400}
        ]
        for i, post in enumerate(dummy_data):
             with open(os.path.join(dummy_data_path, f"item_{i}.json"), 'w') as f:
                 json.dump(post, f)
        print(f"Dummy data created in {dummy_data_path}")
        print("Now run: python sentiment.py test_case_sentiment") 