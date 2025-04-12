import os
import requests
import json
import html
import time # For timestamp
import pytz # For timezone aware timestamp
from datetime import datetime
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed # For parallelism

# Note: Removed functions related to manual pagination (fetch_posts_paginated)
# as they were unreliable and we are focusing on profile info + LLM analysis of bio.

# --- Constants ---
# Set your API Key securely via environment variables
# NEVER hardcode API keys in production code!
API_KEY = os.getenv("OPENROUTER_API_KEY", "")
DEFAULT_MODEL = "google/gemini-2.5-pro-preview-03-25"

def get_user_info_and_id(username, cookies, headers):
    """Fetches basic profile info, user ID, and initial post edges if available."""
    # Reuse the existing function, ensure it returns None, None on specific errors
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    print(f"Fetching user info for {username}...") # Log start
    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=15)
        response.raise_for_status()
        data = response.json()
        # --- Added line to print the raw JSON response ---
        # print("--- Raw JSON Response from web_profile_info ---:")
        # print(json.dumps(data, indent=2)) # Temporarily commented out for cleaner logs
        # print("-----------------------------------------------")
        user_data = data.get('data', {}).get('user', {})
        if not user_data:
            print(f"Error: Could not find 'user' object in profile info for {username}")
            return None, None, None, "User object not found in response"

        user_id = user_data.get('id')
        if not user_id:
            print(f"Error: Could not extract user ID for {username}")
            return None, None, None, "User ID not found in response"

        basic_info = {
            'full_name': user_data.get('full_name'),
            'biography': user_data.get('biography'),
            'followers_count': user_data.get('edge_followed_by', {}).get('count'),
            'following_count': user_data.get('edge_follow', {}).get('count'),
            'is_private': user_data.get('is_private'),
            'is_verified': user_data.get('is_verified'),
            # Add profile pic URL if needed
            'profile_pic_url': user_data.get('profile_pic_url_hd') or user_data.get('profile_pic_url')
        }

        # --- Extract initial post edges --- 
        post_edges = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])
        post_count = user_data.get('edge_owner_to_timeline_media', {}).get('count', 0)
        if post_edges:
             print(f"Successfully fetched info for User ID: {user_id}. Found {len(post_edges)} initial post edges (out of {post_count}).")
        else:
             print(f"Successfully fetched info for User ID: {user_id}. No initial post edges found in this response (Total posts: {post_count}).")

        return user_id, basic_info, post_edges, None # Return posts and None for error on success

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error fetching initial profile info for {username}: {http_err}")
        status_code = http_err.response.status_code
        error_msg = f"HTTP Error: {status_code}"
        if status_code == 404:
            error_msg = "Profile not found (404 Error)"
        elif status_code == 401 or status_code == 403:
             error_msg = "Unauthorized or Forbidden (401/403 Error) - Check cookies/login"
        elif status_code == 429:
             error_msg = "Rate Limited (429 Error) - Wait before trying again"
        # Optionally log response text for debugging other errors
        # print(f"Response text: {http_err.response.text[:500]}...")
        return None, None, None, error_msg # Return None for posts on error

    except requests.exceptions.RequestException as e:
        print(f"Network error fetching initial profile info for {username}: {e}")
        return None, None, None, f"Network Error: {e.__class__.__name__}" # Return None for posts on error
    except json.JSONDecodeError:
        print(f"Failed to decode JSON response for initial profile info for {username}.")
        return None, None, None, "Invalid JSON Response Received" # Return None for posts on error
    except Exception as e:
        print(f"An unexpected error occurred fetching profile info: {e}")
        return None, None, None, f"Unexpected Error: {e.__class__.__name__}" # Return None for posts on error

# ----- NEW HELPER FUNCTION -----
def _prepare_post_data_for_llm(post_edges, max_posts=5, max_caption_len=200):
    """Extracts key info from post edges and formats it as a string for LLM prompts."""
    if not post_edges:
        return "No initial posts data provided."

    post_summaries = []
    limited_edges = post_edges[:max_posts] # Limit number of posts

    for i, edge in enumerate(limited_edges):
        node = edge.get('node', {})
        shortcode = node.get('shortcode', 'N/A')
        typename = node.get('__typename', 'UnknownType')
        timestamp = node.get('taken_at_timestamp')
        dt_object = datetime.fromtimestamp(timestamp, tz=pytz.utc) if timestamp else None
        formatted_time = dt_object.strftime('%Y-%m-%d %H:%M:%S %Z') if dt_object else "No Timestamp"

        caption_node = node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {})
        caption_text = caption_node.get('text', '')
        truncated_caption = (caption_text[:max_caption_len] + '...') if len(caption_text) > max_caption_len else caption_text

        likes = node.get('edge_liked_by', {}).get('count', 0)
        comments = node.get('edge_media_to_comment', {}).get('count', 0)
        views = node.get('video_view_count') # None if not a video or not present

        summary = f"  Post {i+1} ({shortcode}, {typename}, {formatted_time}):\n"
        summary += f"    Likes: {likes}, Comments: {comments}"
        if views is not None:
            summary += f", Views: {views}"
        summary += f"\n    Caption: \"{truncated_caption}\"\n"
        post_summaries.append(summary)

    header = f"Summary of the first {len(limited_edges)} posts (out of {len(post_edges)} initially retrieved):\n"
    return header + "\n".join(post_summaries)

# --- Original extract_graph_data_llm removed as JSON generation is handled by extract_json_data_llm ---

# Helper to prepare headers (moved from old main)
def prepare_headers(username, cookies):
     return {
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

# Helper to prepare cookies (moved from old main)
def prepare_cookies():
    # WARNING: Hardcoding cookies is a security risk! Replace with your actual values.
    session_id = "60078234834%3ArnOpb62xkuBKLX%3A12%3AAYcbk03m8QjbURU6hgrPRhbFGLatzWvp3aYyGRcmmxjc" # Replace! os.getenv("INSTAGRAM_SESSIONID", "...")
    ds_user_id_val = "60078234834" # Replace! os.getenv("INSTAGRAM_DS_USER_ID", "...")
    csrf_token_val = "f0n3xVrSHEcNRC0MKk4N9XIGBq8RxrHx" # Replace! os.getenv("INSTAGRAM_CSRFTOKEN", "...")

    # Added checks for placeholders
    if not all([session_id, ds_user_id_val, csrf_token_val]) or \
       "YOUR_" in session_id or \
       "YOUR_" in ds_user_id_val or \
       "YOUR_" in csrf_token_val:
        print("Warning: One or more Instagram cookies are missing or are still placeholders. Please hardcode your actual values. Scraping will likely fail.")

    return {
        "sessionid": session_id,
        "ds_user_id": ds_user_id_val,
        "csrftoken": csrf_token_val,
    } 

# Helper function to make a single LLM call
def _call_llm(api_key, model, prompt, max_tokens, temperature):
    """Makes a call to the OpenRouter API."""
    try:
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        response = completion.choices[0].message.content.strip()
        # Basic cleaning (can be done per-function if needed)
        if response.startswith("```json"):
             response = response.strip("```json\n `")
        elif response.startswith("```"):
             response = response.strip("```\n `")
        return response
    except Exception as e:
        print(f"LLM call failed: {e}")
        # Return a clear error indicator string
        return f"LLM_ERROR: {e.__class__.__name__}: {str(e)}"

# --- Specific Analysis Functions ---

def generate_report_llm(api_key, username, biography_text, post_edges): # Added post_edges
    """Generates the narrative reconnaissance report, incorporating post data."""
    model = DEFAULT_MODEL
    max_tokens = 1500 # Increased tokens for post analysis
    temperature = 0.5

    # Prepare post data summary
    post_summary = _prepare_post_data_for_llm(post_edges)

    report_prompt = f"""**Task:** Generate an "Initial Profile Reconnaissance" report based on the provided Instagram username, biography text, AND summary of recent posts. Output ONLY plain text.

**Username Context:** {username}
**Biography Text:** "{biography_text}"

**Recent Post Summary:**
{post_summary}

**Report Structure (Use Plain Text Headings/Lists):**
1.  Profile Overview: Briefly mention the username ({username}).
2.  Biography Summary: Summarize the key themes, stated purpose, or activities mentioned in the biography text (2-4 sentences). If empty or nonsensical, state that.
3.  Recent Activity Analysis: Based *only* on the 'Recent Post Summary' provided above, summarize the apparent themes, topics, or types of content from the recent posts (2-4 sentences). Mention any notable patterns (e.g., frequent video posts, specific topics in captions). If no posts provided, state that.
4.  Sentiment Analysis: State the inferred overall sentiment considering *both* the biography text *and* the tone of recent post captions (Positive, Negative, Neutral, Mixed, or Not Applicable).
5.  Key Information Extraction: List any explicitly mentioned key entities (locations, organizations, projects, skills, @mentions, #hashtags) identified *in the bio text OR in the provided post captions*. If none, state "No specific entities mentioned in bio or recent posts." Use simple list format.
6.  Potential Interests (Inferred): Briefly mention 1-3 potential high-level interests that *might* be inferred *speculatively* from the bio, username, *or recent post content*, clearly labeling them as speculative (e.g., "Potential interest in [topic] based on post captions about X."). If none inferred, state "No specific interests could be reasonably inferred."
7.  Concluding Remark: Add a brief concluding sentence (e.g., "Analysis based on provided bio and summary of recent posts.").

**Output:** Generate ONLY the plain text report. **Do NOT use any markdown formatting (no asterisks, no hashes, no markdown lists).** Use simple line breaks for structure. Address all sections.
"""
    print("Generating narrative report (with post data)...")
    report_text = _call_llm(api_key, model, report_prompt, max_tokens, temperature)
    if report_text.startswith("LLM_ERROR"):
         print(f"  Report generation failed: {report_text}")
         return f"Failed to generate report: {report_text}"
    print("  Report generation successful.")
    return report_text

def generate_forensic_analysis_llm(api_key, username, biography_text, post_edges): # Added post_edges
    """Generates text notes highlighting potential forensic points of interest from bio and posts."""
    model = DEFAULT_MODEL
    max_tokens = 1500 # Increased tokens for post analysis
    temperature = 0.4

    # Prepare post data summary
    post_summary = _prepare_post_data_for_llm(post_edges)

    forensic_prompt = f"""**Task:** Analyze the provided Instagram biography text AND recent post summary *strictly* for potential digital forensic points of interest. Focus *only* on patterns and explicit mentions within the text provided. **Do not make assumptions beyond the text.** Output ONLY plain text.

**Biography Text:** "{biography_text}"

**Recent Post Summary:**
{post_summary}

**Analysis Points (Use Plain Text Headings/Lists):**
1.  Potential PII Indicators: Identify any patterns that *might resemble* PII (e.g., email format, phone patterns, specific location names) mentioned explicitly *in the bio OR the provided post captions*. Note the *presence* of the pattern/mention. If none, state "No direct PII pattern indicators identified in bio or recent post captions."
2.  Explicitly Mentioned Locations: List any specific cities, states, countries, landmarks, or geotagged locations mentioned *in the bio OR post captions/data*. If none, state "No locations mentioned." Use simple list format.
3.  Explicit Mentions/Connections: List any other usernames (@mentions), specific websites (URLs), or #hashtags found directly *in the bio or post captions*. If none, state "No external usernames, URLs, or hashtags mentioned." Use simple list format.
4.  Keywords/Themes of Interest: List 3-5 key terms, concepts, or topics directly present *in the bio or post captions* that might be relevant for further investigation (e.g., specific tech, projects, orgs, events, sentiments). If none, state "No specific keywords/themes identified." Use simple list format.
5.  Posting Activity Notes: Briefly comment on the posting times or frequency *if discernible from the provided timestamps* (e.g., "Posts mainly during UTC evenings", "Apparent gap in posting"). If timestamps are unavailable or insufficient, state "Posting activity patterns not analyzed."
6.  Language/Tone Notes: Briefly comment if the language used *in the bio or posts* seems unusual, coded, highly technical, or noteworthy in tone (optional, only if prominent).

**Output:** Generate ONLY the analysis notes as plain text. Use simple headings (e.g., "1. Potential PII Indicators:") and simple lists (e.g., "- Item"). **Do NOT use any markdown formatting.** State clearly if no relevant information was found for a point. Emphasize that findings are based solely on the provided text and post summary.
"""
    print("Generating forensic notes (with post data)...")
    forensic_text = _call_llm(api_key, model, forensic_prompt, max_tokens, temperature)
    if forensic_text.startswith("LLM_ERROR"):
         print(f"  Forensic note generation failed: {forensic_text}")
         return f"Failed to generate forensic notes: {forensic_text}"
    print("  Forensic note generation successful.")
    return forensic_text


def extract_json_data_llm(api_key, username, biography_text, post_edges): # Added post_edges
    """Generates the structured forensic JSON data, incorporating post analysis."""
    model = DEFAULT_MODEL
    max_tokens = 7000 # INCREASED tokens significantly for post details + analysis
    temperature = 0.5

    timestamp = datetime.now(pytz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    escaped_bio = json.dumps(biography_text) # Escape bio text for safe JSON embedding

    # --- Prepare detailed post data for JSON output ---
    # (This is done by the LLM based on instructions below, but we need the prompt structure)
    # We also pass the summary to the LLM for context
    post_summary_for_prompt = _prepare_post_data_for_llm(post_edges, max_posts=5, max_caption_len=150) # Shorter summary for prompt context

    # Revised JSON prompt with post analysis integration
    json_prompt = f"""**Task:** Perform a detailed forensic analysis of the provided Instagram username, biography, AND recent post summary. Extract structured data relevant for Social Media Analysis Toolkit (SMAT) investigations. Generate ONLY a single, valid JSON object adhering strictly to the specified structure. Be exhaustive and inventive, incorporating information from BOTH bio and posts.

**Username:** "{username}"
**Biography Text:** {escaped_bio} // Biography text is pre-escaped for JSON
**Recent Post Summary (Context for LLM):**
{post_summary_for_prompt} // This is a summary; use it AND your general knowledge to interpret potential post content.

**JSON Output Structure:**
{{
  "analysis_metadata": {{
    "timestamp_utc": "{timestamp}",
    "model_used": "{model}"
  }},
  "profile_context": {{
    "username": "{username}",
    "biography_text": {escaped_bio}
  }},
  // --- NEW: Section for analyzed post data ---
  "initial_posts_summary": [
      // Populate this list based on the 'Recent Post Summary' provided above.
      // For each post summarized, create an object like this:
      // {{
      //   "post_index": "integer (1-based)",
      //   "shortcode": "string",
      //   "type": "string (e.g., GraphVideo, GraphImage)",
      //   "timestamp_utc": "string (YYYY-MM-DD HH:MM:SS Z)",
      //   "caption_snippet": "string (brief snippet)",
      //   "likes_count": "integer",
      //   "comments_count": "integer",
      //   "views_count": "integer or null",
      //   "detected_entities_in_caption": ["list", "of", "strings"], // Entities extracted *by the LLM* from this post's caption
      //   "inferred_topics_in_caption": ["list", "of", "strings"]  // Topics inferred *by the LLM* from this post's caption
      // }}
  ],
  "linguistic_analysis": {{ // Consider bio AND post captions
    "summary": "string (Overall summary considering bio and posts)",
    "language": "string",
    "sentiment_overall_label": "string",
    "sentiment_overall_score": "float",
    "keywords": ["list", "of", "strings (from bio AND posts)"],
    "topics": ["list", "of", "strings (from bio AND posts)"],
    "writing_style_notes": "string (Consider bio and posts)"
  }},
  "entity_extraction": {{ // Extract from bio AND post captions
    "mentions": ["list", "of", "strings"],
    "hashtags": ["list", "of", "strings"],
    "urls": ["list", "of", "strings"],
    "emails": ["list", "of", "strings"],
    "phone_numbers": ["list", "of", "strings"],
    "locations": ["list", "of", "strings"],
    "organizations": ["list", "of", "strings"],
    "persons": ["list", "of", "strings"],
    "technologies_tools": ["list", "of", "strings"],
    "projects_products": ["list", "of", "strings"]
  }},
  "network_connections_explicit": {{ // Base on bio AND post content (mentions, captions, topics)
    "nodes": [
      {{"id": "profile_owner", "label": "{username}", "type": "ProfileOwner"}},
      // Add nodes from entity_extraction (bio+posts) and interpretable concepts/activities from bio/posts.
    ],
    "edges": [
      // Connect profile_owner to nodes representing activities/skills/concepts/mentions from bio AND posts.
      // Connect extracted entities to each other if relationships are implied in bio/posts.
    ]
  }},
  "inferred_analysis": {{ // Infer based on bio AND post content
    "potential_interests": [ {{ "interest": "string", "reasoning": "string (cite bio or post)", "confidence": "Low/Medium/High" }} ],
    "potential_affiliations": [ {{ "affiliation": "string", "reasoning": "string (cite bio or post)", "confidence": "Low/Medium/High" }} ],
    "potential_skills": [ {{ "skill": "string", "reasoning": "string (cite bio or post)", "confidence": "Low/Medium/High" }} ],
    "potential_locations": [ {{ "location": "string", "reasoning": "string (cite bio or post)", "confidence": "Low/Medium/High" }} ]
  }},
  "threat_indicators_potential": {{ // Analyze bio AND post captions
    "violent_extremism_keywords": ["list", "of", "strings"],
    "misinformation_themes": ["list", "of", "strings"],
    "hate_speech_indicators": ["list", "of", "strings"],
    "self_harm_indicators": ["list", "of", "strings"],
    "overall_risk_assessment_llm": "string (Consider bio and posts; include disclaimer)"
  }},
  "cross_platform_links_potential": [ // Look for clues in bio OR posts
      {{ "platform": "string", "identifier": "string", "reasoning": "string" }}
  ],
  "suggestions_for_investigation": {{ // Base on combined analysis
    "similar_users_suggested": [ {{ "suggestion": "string", "reasoning": "string" }} ],
    "relevant_hashtags_suggested": [ {{ "suggestion": "string", "reasoning": "string" }} ],
    "topics_to_monitor": ["list", "of", "strings"]
  }}
}}

**Instructions & Constraints:**
1.  **Analyze BOTH Bio and Post Summary:** Integrate information from both sources throughout the JSON structure.
2.  **Populate `initial_posts_summary`:** Accurately reflect the provided post summary, extracting key fields and performing LLM analysis (entity/topic detection) *per post*.
3.  **Enhance Other Sections:** Use post information (captions, timestamps, types) to enrich `linguistic_analysis`, `entity_extraction`, `network_connections_explicit`, `inferred_analysis`, and `threat_indicators_potential`.
4.  **Inventive Explicit Graph:** Include nodes/edges derived from post content (mentions, topics, activities described in captions) in `network_connections_explicit`. Connect them logically to `profile_owner` or other entities.
5.  **Populate All Fields:** Use empty lists `[]` or `null`/`"Not Applicable"`.
6.  **VALID JSON ONLY:** Output MUST be a single, valid JSON object. No extra text.

"""
    print("Generating structured forensic JSON data (with post analysis)...")
    json_string = _call_llm(api_key, model, json_prompt, max_tokens, temperature)

    # Default error structure for JSON
    error_json = {"error": "Unknown JSON processing error"}

    if json_string.startswith("LLM_ERROR"):
        print(f"  Error during JSON generation call: {json_string}")
        error_json["error"] = f"LLM call failed: {json_string}"
        return error_json

    try:
        # Attempt to find JSON block even if there's surrounding text
        json_match = None
        if '```json' in json_string:
            json_match = json_string.split('```json', 1)[1].rsplit('```', 1)[0]
        elif '{' in json_string and '}' in json_string:
             # Basic heuristic: find first { and last }
             start = json_string.find('{')
             end = json_string.rfind('}')
             if start != -1 and end != -1 and end > start:
                  json_match = json_string[start:end+1]

        if not json_match:
            # Fallback to trying the whole string if no clear block found
            json_match = json_string

        analysis_data = json.loads(json_match)
        print("  Successfully parsed forensic JSON data.")
        # Basic validation (can be expanded significantly)
        required_keys = ["analysis_metadata", "profile_context", "initial_posts_summary", # Added new key check
                         "linguistic_analysis", "entity_extraction", "network_connections_explicit",
                         "inferred_analysis", "threat_indicators_potential",
                         "cross_platform_links_potential", "suggestions_for_investigation"]
        if all(key in analysis_data for key in required_keys):
             # Ensure profile_owner node exists
             graph_data = analysis_data.get("network_connections_explicit", {})
             nodes = graph_data.get("nodes", [])
             if not any(node.get("id") == "profile_owner" for node in nodes):
                 print("  Warning: LLM JSON response missing 'profile_owner' node. Adding default.")
                 # Ensure nodes list exists before inserting
                 if analysis_data["network_connections_explicit"].get("nodes") is None:
                      analysis_data["network_connections_explicit"]["nodes"] = []
                 analysis_data["network_connections_explicit"]["nodes"].insert(0, {"id": "profile_owner", "label": username, "type": "ProfileOwner"})

             return analysis_data
        else:
            missing_keys = [key for key in required_keys if key not in analysis_data]
            print(f"  Warning: Parsed JSON missing some top-level forensic keys: {missing_keys}")
            error_json["error"] = f"Parsed JSON missing required forensic keys: {missing_keys}"
            error_json["raw_response"] = json_string # Include raw response for debugging
            return error_json

    except json.JSONDecodeError as e:
        print(f"  Error: Failed to parse LLM response as JSON. {e}")
        print(f"  Problematic JSON string snippet: {json_string[:500]}...") # Log snippet
        error_json["error"] = "LLM response was not valid JSON"
        error_json["raw_response"] = json_string # Include raw response for debugging
        return error_json
    except Exception as e: # Catch other potential errors during processing
        print(f"  Error processing LLM JSON response: {e}")
        error_json["error"] = f"Error processing JSON response: {e.__class__.__name__}"
        error_json["raw_response"] = json_string
        return error_json


# --- Main Function for Parallel Execution ---

def run_all_analyses_parallel(username, biography_text, post_edges): # Added post_edges
    """Runs the three LLM analysis functions in parallel, incorporating post data."""
    
    # Check for API key in environment variable
    api_key = API_KEY
    if not api_key:
         print("CRITICAL ERROR: OPENROUTER_API_KEY environment variable is not set.")
         print("Please set it before running the script: ")
         print("  export OPENROUTER_API_KEY='your-api-key'     # For Linux/macOS")
         print("  set OPENROUTER_API_KEY=your-api-key          # For Windows cmd")
         print("  $env:OPENROUTER_API_KEY='your-api-key'       # For Windows PowerShell")
         return {
             "report": "API Key Missing. Cannot run analysis. Please set the OPENROUTER_API_KEY environment variable.",
             "forensic_notes": "API Key Missing. Please set the OPENROUTER_API_KEY environment variable.",
             "json_data": {"error": "API Key Missing. Please set the OPENROUTER_API_KEY environment variable."}
         }

    # Ensure biography_text is a string, handle None case
    biography_text = biography_text if biography_text is not None else ""

    results = {
        "report": "Analysis Pending...",
        "forensic_notes": "Analysis Pending...",
        "json_data": {"error": "Analysis Pending..."} # Start with error state for JSON
    }

    start_time = time.time()
    print(f"--- Starting parallel LLM analyses for {username} (with post data) ---")

    # Use ThreadPoolExecutor for I/O-bound tasks (API calls)
    # NOTE: Actual parallelism depends on the execution environment.
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit tasks, passing post_edges to each and using the secure api_key
        future_report = executor.submit(generate_report_llm, api_key, username, biography_text, post_edges)
        future_forensic = executor.submit(generate_forensic_analysis_llm, api_key, username, biography_text, post_edges)
        future_json = executor.submit(extract_json_data_llm, api_key, username, biography_text, post_edges)

        # Store futures with identifiers
        futures = {
            future_report: "report",
            future_forensic: "forensic_notes",
            future_json: "json_data"
        }

        # Process completed tasks as they finish
        for future in as_completed(futures):
            identifier = futures[future]
            try:
                # Get the result from the future
                result = future.result()
                results[identifier] = result
                print(f"  Task '{identifier}' completed.")
            except Exception as exc:
                print(f"  Task '{identifier}' generated an exception: {exc}")
                # Store the error message
                if identifier == "json_data":
                    results[identifier] = {"error": f"Task execution failed: {exc}"}
                else:
                    results[identifier] = f"Task execution failed: {exc}"

    end_time = time.time()
    print(f"--- Parallel LLM analyses finished in {end_time - start_time:.2f} seconds ---")

    # Final check on JSON data for top-level error key
    if isinstance(results["json_data"], dict) and results["json_data"].get("error"):
        print(f"  JSON data generation resulted in an error: {results['json_data']['error']}")
    elif not isinstance(results["json_data"], dict):
         print(f"  JSON data generation returned unexpected type: {type(results['json_data'])}")
         results["json_data"] = {"error": "Unexpected return type from JSON generation task."}


    return results 