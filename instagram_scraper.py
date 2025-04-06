import requests
import time
import json
import os
import re
import urllib.parse
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from openai import OpenAI
import html

# --- Constants ---
MEDIA_QUERY_HASH = "f2405b236d85e8296cf30347c9f08c2a"
GRAPHQL_URL = "https://www.instagram.com/graphql/query/"
DEFAULT_POSTS_PER_PAGE = 12
MAX_PAGES = 10
REQUEST_DELAY_SECONDS = 2
OUTPUT_FILENAME_TEMPLATE = "{username}_paginated_posts.json"


def analyze_sentiment(text):
    """Analyzes the sentiment of a text using VADER."""
    if not text: # Handle cases with no text
        return None
    try:
        # Lazy load analyzer if needed, or keep instance global/passed if script grows
        analyzer = SentimentIntensityAnalyzer()
        vs = analyzer.polarity_scores(text)
        return vs['compound'] # Return the compound score (-1 to +1)
    except Exception as e:
        print(f"Error during sentiment analysis: {e}")
        return None


def extract_graph_data_llm(biography_text):
    """Extracts entities and relationships for a network graph using OpenRouter LLM."""
    if not biography_text:
        return {"error": "No biography text provided"}

    try:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("Warning: OPENROUTER_API_KEY environment variable not set. Skipping LLM graph extraction.")
            return {"error": "API Key Missing"}

        print(f"Extracting graph data from biography with OpenRouter (Claude 3.5 Sonnet): \"{biography_text[:50]}...\"")

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

        # Define the desired JSON structure in the prompt
        prompt = f"""Analyze the following Instagram biography. Identify key entities (People, Organizations, Locations, Hashtags, Topics/Concepts) and any implied relationships between them. 
Output ONLY a valid JSON object with two keys: "nodes" and "edges".
- "nodes" should be a list of objects, each with 'id' (the entity name) and 'type' (e.g., Person, Organization, Location, Hashtag, Topic).
- "edges" should be a list of objects, each with 'source' (source node id), 'target' (target node id), and 'label' (description of the relationship, e.g., mentions, works_at, located_in, related_to).

Biography: "{biography_text}"

JSON Output:"""

        completion = client.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=500, # Increased max_tokens for JSON output
            temperature=0.3 # Keep temperature low for structured output
            # Optional headers for OpenRouter ranking (can be omitted)
        )

        llm_response_content = completion.choices[0].message.content.strip()
        print(f"  LLM Raw Response: {llm_response_content[:200]}...") # Log raw response

        # Attempt to parse the response as JSON
        try:
            # Clean potential markdown code fences if the LLM adds them
            if llm_response_content.startswith("```json"):
                llm_response_content = llm_response_content.strip("```json\n ")
            elif llm_response_content.startswith("```"):
                 llm_response_content = llm_response_content.strip("```\n ")
            
            graph_data = json.loads(llm_response_content)
            # Basic validation of expected keys
            if isinstance(graph_data, dict) and "nodes" in graph_data and "edges" in graph_data:
                 print(f"  Successfully parsed graph JSON from LLM.")
                 return graph_data
            else:
                print("  Warning: LLM response parsed but missing expected 'nodes' or 'edges' keys.")
                return {"error": "LLM response missing required keys", "raw_response": llm_response_content}

        except json.JSONDecodeError as json_err:
            print(f"  Error: Failed to parse LLM response as JSON. {json_err}")
            return {"error": "LLM response was not valid JSON", "raw_response": llm_response_content}

    except Exception as e:
        print(f"Error during OpenRouter LLM graph extraction: {e}")
        return {"error": f"LLM Error: {e.__class__.__name__}"}


def get_user_info_and_id(username, cookies, headers):
    """Fetches basic profile info and the crucial user ID."""
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=15)
        response.raise_for_status()
        data = response.json()
        user_data = data.get('data', {}).get('user', {})
        if not user_data:
            print(f"Error: Could not find 'user' object in profile info for {username}")
            return None, None
        user_id = user_data.get('id')
        if not user_id:
            print(f"Error: Could not extract user ID for {username}")
            return None, None

        basic_info = {
            'full_name': user_data.get('full_name'),
            'biography': user_data.get('biography'),
            'followers_count': user_data.get('edge_followed_by', {}).get('count'),
            'following_count': user_data.get('edge_follow', {}).get('count'),
            'is_private': user_data.get('is_private'),
            'is_verified': user_data.get('is_verified'),
        }
        return user_id, basic_info

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch initial profile info: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"Response status: {e.response.status_code}")
             content_type = e.response.headers.get('Content-Type', '')
             if 'text' in content_type or 'json' in content_type:
                 print(f"Response text: {e.response.text[:500]}...")
             else:
                 print(f"Response content type: {content_type}")
        return None, None
    except json.JSONDecodeError:
        print("Failed to decode JSON response for initial profile info.")
        return None, None


def fetch_posts_paginated(user_id, username, cookies, headers):
    """Fetches all posts using pagination via the GraphQL endpoint."""
    all_posts = []
    end_cursor = None
    has_next_page = True
    pages_fetched = 0

    print(f"Starting paginated post fetch for {username} (ID: {user_id})...")

    while has_next_page and pages_fetched < MAX_PAGES:
        pages_fetched += 1
        variables = {
            'id': user_id,
            'first': DEFAULT_POSTS_PER_PAGE,
        }
        if end_cursor:
            variables['after'] = end_cursor

        params = {
            'query_hash': MEDIA_QUERY_HASH,
            'variables': json.dumps(variables)
        }
        paginated_url = f"{GRAPHQL_URL}?{urllib.parse.urlencode(params)}"

        print(f"  Fetching page {pages_fetched} (Cursor: {end_cursor})...")

        try:
            response = requests.get(paginated_url, headers=headers, cookies=cookies, timeout=20)
            response.raise_for_status()
            data = response.json()

            media_data = data.get('data', {}).get('user', {}).get('edge_owner_to_timeline_media', {})
            if not media_data:
                print("  Error: Could not find media data in GraphQL response.")
                print(f"  Response snippet: {str(data)[:500]}...")
                break

            posts = media_data.get('edges', [])
            if posts:
                all_posts.extend(posts)
                print(f"    Added {len(posts)} posts. Total now: {len(all_posts)}")
            else:
                print("    No 'edges' found on this page.")

            page_info = media_data.get('page_info', {})
            has_next_page = page_info.get('has_next_page', False)
            end_cursor = page_info.get('end_cursor')

            if not has_next_page:
                print("  No more pages found.")
                break

            print(f"  Waiting {REQUEST_DELAY_SECONDS}s before next request...")
            time.sleep(REQUEST_DELAY_SECONDS)

        except requests.exceptions.RequestException as e:
            print(f"  Failed to fetch page {pages_fetched}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                 print(f"  Response status: {e.response.status_code}")
                 content_type = e.response.headers.get('Content-Type', '')
                 if 'text' in content_type or 'json' in content_type:
                     print(f"  Response text: {e.response.text[:500]}...")
                 else:
                     print(f"  Response content type: {content_type}")
            break
        except json.JSONDecodeError:
            print(f"  Failed to decode JSON response for page {pages_fetched}.")
            break
        except Exception as e:
            print(f"  An unexpected error occurred during pagination: {e}")
            break

    if pages_fetched >= MAX_PAGES and has_next_page:
        print(f"Warning: Reached maximum page limit ({MAX_PAGES}). May not have fetched all posts.")

    print(f"Finished pagination. Fetched a total of {len(all_posts)} posts across {pages_fetched} pages.")
    return all_posts


def parse_profile_data(post_edges):
    """Parses the list of post edges extracted from paginated fetches."""
    if not post_edges:
        print("No post edges provided to parse.")
        return []

    print(f"Parsing details for {len(post_edges)} fetched posts...")
    extracted_posts = []

    for edge in post_edges:
        node = edge.get('node', {})
        if not node:
            print("Warning: Found an edge without a node.")
            continue

        caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
        caption = caption_edges[0].get('node', {}).get('text') if caption_edges else None
        caption_sentiment = analyze_sentiment(caption)

        comment_info = node.get('edge_media_to_comment', {})
        comment_count = comment_info.get('count')
        comment_texts = [
            cmt_edge.get('node', {}).get('text')
            for cmt_edge in comment_info.get('edges', [])
            if cmt_edge.get('node')
        ]

        tagged_users_in_caption = []
        if caption:
            tagged_users_in_caption = re.findall(r'@(\w+)', caption)

        tagged_users_in_media = [
            tag_edge.get('node', {}).get('user', {}).get('username')
            for tag_edge in node.get('edge_media_to_tagged_user', {}).get('edges', [])
            if tag_edge.get('node', {}).get('user')
        ]

        post_info = {
            'id': node.get('id'),
            'shortcode': node.get('shortcode'),
            'timestamp': node.get('taken_at_timestamp'),
            'media_type': node.get('__typename'),
            'display_url': node.get('display_url'),
            'likes_count': node.get('edge_liked_by', {}).get('count'),
            'comments_count': comment_count,
            'caption': caption,
            'caption_sentiment_compound': caption_sentiment,
            'comment_previews': comment_texts,
            'tagged_users_in_caption': tagged_users_in_caption,
            'tagged_users_in_media': tagged_users_in_media
        }
        extracted_posts.append(post_info)

    print(f"Successfully parsed {len(extracted_posts)} posts.")
    return extracted_posts


def main():
    username = "zuck"

    session_id = os.getenv("INSTAGRAM_SESSIONID", "60078234834%3ArnOpb62xkuBKLX%3A12%3AAYdh5WMhR7y-1xVo9yDHZKbSLxGNni6cnQPsPYyIRiMR")
    ds_user_id_val = os.getenv("INSTAGRAM_DS_USER_ID", "60078234834")
    csrf_token_val = os.getenv("INSTAGRAM_CSRFTOKEN", "f0n3xVrSHEcNRC0MKk4N9XIGBq8RxrHx")

    if not all([session_id, ds_user_id_val, csrf_token_val]):
        print("Error: One or more required cookies are missing.")
        return

    cookies = {
        "sessionid": session_id,
        "ds_user_id": ds_user_id_val,
        "csrftoken": csrf_token_val,
    }

    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "referer": f"https://www.instagram.com/{username}/",
        "sec-ch-prefers-color-scheme": "dark",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "x-csrftoken": cookies.get("csrftoken"),
        "x-ig-app-id": "936619743392459",
        "x-requested-with": "XMLHttpRequest",
        "x-ig-user-id": cookies.get("ds_user_id")
    }

    print(f"Attempting to fetch user ID for '{username}'...")
    user_id, basic_info = get_user_info_and_id(username, cookies, headers)

    if user_id:
        print(f"Successfully found User ID: {user_id}")

        report_data = {
            "username": username,
            "user_id": user_id,
            "full_name": basic_info.get('full_name', 'N/A'),
            "biography": basic_info.get('biography', ''),
            "followers_count": basic_info.get('followers_count', 'N/A'),
            "following_count": basic_info.get('following_count', 'N/A'),
            "is_private": basic_info.get('is_private', 'N/A'),
            "is_verified": basic_info.get('is_verified', 'N/A'),
            "graph_data": None # Initialize graph data field
        }

        # --- Extract Graph Data from Biography using LLM ---
        if report_data['biography']:
            graph_data_result = extract_graph_data_llm(report_data['biography'])
            report_data['graph_data'] = graph_data_result # Store the result (JSON or error dict)
        else:
             report_data['graph_data'] = {"error": "No biography available for analysis"}

        # --- Generate HTML Report (Updated) --- 
        # Prepare graph data for HTML display (using <pre> for raw JSON)
        graph_html = "<p><i>No biography available for graph extraction.</i></p>"
        if report_data['graph_data']:
            if "error" in report_data['graph_data']:
                graph_html = f"<p><strong>Graph Extraction Error:</strong> {report_data['graph_data'].get('error', 'Unknown')}</p>"
                if "raw_response" in report_data['graph_data']:
                     graph_html += f"<p>Raw LLM Response:</p><pre><code>{html.escape(report_data['graph_data']['raw_response'])}</code></pre>"
            else:
                # Pretty print the JSON for the <pre> tag
                graph_json_str = json.dumps(report_data['graph_data'], indent=2)
                # Use html.escape to prevent HTML injection from JSON content
                graph_html = f"<p>Extracted Graph Data (JSON):</p><pre><code>{html.escape(graph_json_str)}</code></pre>"
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instagram Profile Reconnaissance: {report_data['username']}</title>
    <style>
        body {{ font-family: sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }}
        .report-card {{ background-color: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 25px; max-width: 600px; margin: auto; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #555; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 20px; text-align: center; }}
        .data-item {{ margin-bottom: 15px; display: flex; }}
        .data-label {{ font-weight: bold; color: #666; min-width: 120px; flex-shrink: 0; }}
        .data-value {{ word-break: break-word; }}
        .status-verified {{ color: #0095f6; font-weight: bold; }}
        .status-private {{ color: #ed4956; font-weight: bold; }}
        .note {{ background-color: #fffbe6; border: 1px solid #ffe58f; border-radius: 4px; padding: 15px; margin-top: 25px; font-size: 0.9em; color: #8a6d3b; }}
    </style>
</head>
<body>
    <div class="report-card">
        <h1>Initial Profile Reconnaissance</h1>
        
        <div class="data-item">
            <span class="data-label">Target User:</span>
            <span class="data-value">@{report_data['username']}</span>
        </div>
        <div class="data-item">
            <span class="data-label">User ID:</span>
            <span class="data-value">{report_data['user_id']}</span>
        </div>
        <div class="data-item">
            <span class="data-label">Full Name:</span>
            <span class="data-value">{report_data['full_name']}</span>
        </div>
        <div class="data-item">
            <span class="data-label">Biography:</span>
            <span class="data-value">{html.escape(report_data['biography']) if report_data['biography'] else '<i>(No biography)</i>'}</span>
        </div>
        
        <!-- Add Graph Data Section -->
        <div class="data-item" style="display: block; border-top: 1px solid #eee; margin-top: 20px; padding-top: 20px;">
            <span class="data-label" style="margin-bottom: 10px; display: block;">Extracted Graph Data (LLM):</span>
            <div class="data-value" style="max-height: 300px; overflow-y: auto; background-color: #f8f8f8; padding: 10px; border-radius: 4px;">
                {graph_html}
            </div>
        </div>
        
        <div class="data-item">
            <span class="data-label">Followers:</span>
            <span class="data-value">{report_data['followers_count']}</span>
        </div>
        <div class="data-item">
            <span class="data-label">Following:</span>
            <span class="data-value">{report_data['following_count']}</span>
        </div>
        <div class="data-item">
            <span class="data-label">Status:</span>
            <span class="data-value">
                {f'<span class="status-private">Private</span>' if report_data['is_private'] else 'Public'}
                {f'<span class="status-verified"> | Verified</span>' if report_data['is_verified'] else ''}
            </span>
        </div>

        <div class="note">
            <strong>Note:</strong> Attempt to retrieve full post data via pagination failed. This may be due to API changes, rate limiting, or insufficient permissions. The report contains only reliably fetched profile metadata.
        </div>
    </div>
</body>
</html>
        """

        # --- Write HTML to file ---
        output_html_filename = f"{username}_recon_report.html"
        try:
            with open(output_html_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"\nSuccessfully generated HTML report: {output_html_filename}")
        except IOError as e:
            print(f"\nError writing HTML report to file: {e}")

        # --- Stop here, do not attempt pagination ---

    else:
        print(f"\nCould not retrieve User ID for '{username}'. Cannot proceed.")


if __name__ == "__main__":
    main() 