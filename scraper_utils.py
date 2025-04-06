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
# Set your API Key securely here or via environment variables
# WARNING: Hardcoding is a security risk!
API_KEY = ""
DEFAULT_MODEL = "google/gemini-2.5-pro-preview-03-25"

def get_user_info_and_id(username, cookies, headers):
    """Fetches basic profile info and the crucial user ID."""
    # Reuse the existing function, ensure it returns None, None on specific errors
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    print(f"Fetching user info for {username}...") # Log start
    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=15)
        response.raise_for_status()
        data = response.json()
        user_data = data.get('data', {}).get('user', {})
        if not user_data:
            print(f"Error: Could not find 'user' object in profile info for {username}")
            return None, None, "User object not found in response"

        user_id = user_data.get('id')
        if not user_id:
            print(f"Error: Could not extract user ID for {username}")
            return None, None, "User ID not found in response"

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
        print(f"Successfully fetched info for User ID: {user_id}")
        return user_id, basic_info, None # Return None for error message on success

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
        return None, None, error_msg

    except requests.exceptions.RequestException as e:
        print(f"Network error fetching initial profile info for {username}: {e}")
        return None, None, f"Network Error: {e.__class__.__name__}"
    except json.JSONDecodeError:
        print(f"Failed to decode JSON response for initial profile info for {username}.")
        return None, None, "Invalid JSON Response Received"
    except Exception as e:
        print(f"An unexpected error occurred fetching profile info: {e}")
        return None, None, f"Unexpected Error: {e.__class__.__name__}"

def extract_graph_data_llm(biography_text):
    """Extracts entities, relationships, summary, inferred items, and suggestions using OpenRouter LLM."""
    # Default structure for success or partial failure
    default_result = {
        "graph_data": {"nodes": [{"id": "profile_owner", "label": "Profile Owner", "type": "Person"}], "edges": []},
        "summary": "Analysis incomplete.",
        "inferred_items": [],
        "related_suggestions": {"similar_users": [], "similar_hashtags": []},
        "error": None # No error initially
    }

    if not biography_text:
        default_result["summary"] = "No biography text provided."
        default_result["error"] = "No biography text provided"
        return default_result

    try:
        # WARNING: Hardcoding API key is a security risk!
        api_key = "" # Ensure this is your actual key
        if not api_key or "YOUR_" in api_key:
            print("Error: OPENROUTER_API_KEY is not set or is still a placeholder.")
            default_result["summary"] = "LLM analysis skipped: Missing API key."
            default_result["error"] = "API Key Missing or Placeholder"
            return default_result

        print(f"Extracting complex analysis+suggestions from biography: \"{biography_text[:50]}...\"")

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

        # Enhanced prompt for complex analysis including suggestions
        prompt = f"""**Task:** Perform a detailed analysis of the provided Instagram biography. Extract a comprehensive knowledge graph, provide a summary with sentiment, infer potential related items, and suggest potentially similar users/hashtags.

**Biography:** "{biography_text}"

**Instructions:**
1.  **Analyze Biography:** Read the biography text carefully.
2.  **Extract Explicit Graph (Comprehensive):** Identify **all possible** entities (Person, Organization, Brand, Project, Location, Website, Hashtag, Skill, Interest, Topic) explicitly mentioned or strongly implied in the bio. Create a detailed graph with `nodes` (with `id`, `label`, `type`) and `edges` (with `from`, `to`, `label`) representing these direct connections. Be exhaustive. Include a `profile_owner` node `{{"id": "profile_owner", "label": "Profile Owner", "type": "Person"}}` in the nodes list, even if no other nodes are found. Connect relevant extracted entities to `profile_owner`.
3.  **Summarize and Assess Sentiment:** Write a brief text `summary` (2-3 sentences) capturing the key themes or focus of the biography. If the bio is sparse, state that. Analyze the overall sentiment of the *biography text itself* and include it (e.g., "Overall sentiment appears Positive/Neutral/Negative/Not Applicable.").
4.  **Infer/Generate Potential Items (Highly Speculative):** Based on the biography (if any), username, and general context/knowledge, generate a list (`inferred_items`) of 3-5 *potentially relevant* entities (Topics, Interests, Hashtags, People, Organizations) that the user *might* be associated with. **Generate these even if the bio provides little information.** For each item, provide: `label`, `type` (indicating speculation, e.g., "Potential Topic"), and a *very brief* `reasoning`. **Do NOT add sentiment scores.**
5.  **Suggest Related Users/Hashtags (Speculative Simulation):** Based on the analysis (bio, inferred items, context), simulate finding related content. Generate an object (`related_suggestions`) containing two keys:
    *   `similar_users`: A list of 2-4 objects, each representing a potentially similar Instagram user. Each object should have:
        *   `suggestion`: The suggested username (string, e.g., "@similar_user").
        *   `reasoning`: A brief explanation (string) why this user might be relevant (e.g., "Shares interest in AI").
    *   `similar_hashtags`: A list of 2-4 objects, each representing a potentially relevant hashtag. Each object should have:
        *   `suggestion`: The suggested hashtag (string, e.g., "#relevanttopic").
        *   `reasoning`: A brief explanation (string) why this hashtag might be relevant (e.g., "Related to mentioned project").
    *   These suggestions are speculative LLM outputs based on patterns, not real-time network analysis.
6.  **Output Format:** Return ONLY a single, valid JSON object with the following top-level keys:
    *   `graph_data`: Object with `nodes` and `edges` (from step 2).
    *   `summary`: String summary with sentiment (from step 3).
    *   `inferred_items`: List of inferred item objects (from step 4).
    *   `related_suggestions`: Object with `similar_users` list and `similar_hashtags` list (from step 5).
    *   **It is absolutely critical that the entire output is valid JSON and nothing else.**
7.  **Empty/Minimal Cases Handling:**
    *   Always return the full JSON structure.
    *   If the bio is empty, populate fields appropriately (e.g., empty graph edges, summary indicating emptiness, generated inferred items and suggestions based on context). Ensure `related_suggestions` and its lists exist, even if empty.

**JSON Output:**"""

        completion = client.chat.completions.create(
            model="google/gemini-2.5-pro-preview-03-25", # Make sure model name is correct
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=4000, # Increased tokens again for suggestions
            temperature=0.55 # Slightly more creative temp
        )

        llm_response_content = completion.choices[0].message.content.strip()
        print(f"  LLM Raw Response (Suggestive): {llm_response_content[:300]}...") # Log raw response

        try:
            # Clean potential markdown code fences
            if llm_response_content.startswith("```json"):
                llm_response_content = llm_response_content.strip("```json\n `")
            elif llm_response_content.startswith("```"):
                 llm_response_content = llm_response_content.strip("```\n `")

            analysis_data = json.loads(llm_response_content)

            # Validate the extended structure
            if (isinstance(analysis_data, dict) and
                isinstance(analysis_data.get("graph_data"), dict) and
                isinstance(analysis_data["graph_data"].get("nodes"), list) and
                isinstance(analysis_data["graph_data"].get("edges"), list) and
                isinstance(analysis_data.get("summary"), str) and
                isinstance(analysis_data.get("inferred_items"), list) and
                isinstance(analysis_data.get("related_suggestions"), dict) and
                isinstance(analysis_data["related_suggestions"].get("similar_users"), list) and
                isinstance(analysis_data["related_suggestions"].get("similar_hashtags"), list)):

                 # Optional: Deeper validation of suggestion structure could go here

                 # Ensure profile_owner node exists in graph_data.nodes
                 nodes = analysis_data["graph_data"].get("nodes", [])
                 if not any(node.get("id") == "profile_owner" for node in nodes):
                     print("  Warning: LLM response missing 'profile_owner' node. Adding it.")
                     analysis_data["graph_data"]["nodes"].insert(0, {"id": "profile_owner", "label": "Profile Owner", "type": "Person"})

                 print(f"  Successfully parsed complex analysis+suggestions JSON.")
                 analysis_data["error"] = None # Explicitly set error to None on success
                 return analysis_data # Return the whole dict
            else:
                print("  Warning: LLM response parsed but missing required structure (graph_data, summary, inferred_items, related_suggestions).")
                default_result["summary"] = "LLM analysis failed: Response missing required structure."
                default_result["error"] = "LLM response missing required structure"
                default_result["raw_response"] = llm_response_content
                return default_result

        except json.JSONDecodeError as json_err:
            print(f"  Error: Failed to parse LLM response as JSON. {json_err}")
            default_result["summary"] = "LLM analysis failed: Invalid JSON response."
            default_result["error"] = "LLM response was not valid JSON"
            default_result["raw_response"] = llm_response_content
            return default_result

    except Exception as e:
        error_type = e.__class__.__name__
        error_message = str(e)
        print(f"Error during OpenRouter LLM complex analysis+suggestions: {error_type}: {error_message}")
        # import traceback
        # traceback.print_exc()
        default_result["summary"] = f"LLM analysis failed: {error_type}"
        default_result["error"] = f"LLM Error: {error_type}"
        return default_result

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
    session_id = "YOUR_INSTAGRAM_SESSIONID" # Replace! os.getenv("INSTAGRAM_SESSIONID", "...")
    ds_user_id_val = "YOUR_INSTAGRAM_DS_USER_ID" # Replace! os.getenv("INSTAGRAM_DS_USER_ID", "...")
    csrf_token_val = "YOUR_INSTAGRAM_CSRFTOKEN" # Replace! os.getenv("INSTAGRAM_CSRFTOKEN", "...")

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

def generate_report_llm(api_key, username, biography_text):
    """Generates the narrative reconnaissance report."""
    model = DEFAULT_MODEL
    max_tokens = 1000
    temperature = 0.5

    report_prompt = f"""**Task:** Generate an "Initial Profile Reconnaissance" report based *only* on the provided Instagram biography text and username context. Output ONLY plain text.

**Username Context:** Analyze potential implications of the username ({username}) itself if relevant.
**Biography Text:** "{biography_text}"

**Report Structure (Use Plain Text Headings/Lists):**
1.  Profile Overview: Briefly mention the username ({username}).
2.  Biography Summary: Summarize the key themes, stated purpose, or activities mentioned in the biography text (2-4 sentences). If empty or nonsensical, state that.
3.  Sentiment Analysis: State the inferred overall sentiment of the biography text (Positive, Negative, Neutral, Mixed, or Not Applicable if empty/nonsensical).
4.  Key Information Extraction: List any explicitly mentioned key entities like locations, organizations, projects, or skills identified directly *in the bio text*. If none, state "No specific entities mentioned." Use simple list format (e.g., "- Entity 1").
5.  Potential Interests (Inferred): Briefly mention 1-2 potential high-level interests that *might* be inferred *speculatively* from the bio or username, clearly labeling them as such (e.g., "Potential interest in [topic] based on bio phrasing."). If none inferred, state "No specific interests could be reasonably inferred."
6.  Concluding Remark: Add a brief concluding sentence (e.g., "Analysis based solely on provided bio text.").

**Output:** Generate ONLY the plain text report. **Do NOT use any markdown formatting (no asterisks, no hashes, no markdown lists).** Use simple line breaks for structure.
"""
    print("Generating narrative report...")
    report_text = _call_llm(api_key, model, report_prompt, max_tokens, temperature)
    if report_text.startswith("LLM_ERROR"):
         print(f"  Report generation failed: {report_text}")
         return f"Failed to generate report: {report_text}"
    print("  Report generation successful.")
    return report_text

def generate_forensic_analysis_llm(api_key, username, biography_text):
    """Generates text notes highlighting potential forensic points of interest."""
    model = DEFAULT_MODEL
    max_tokens = 1000
    temperature = 0.4

    forensic_prompt = f"""**Task:** Analyze the provided Instagram biography text *strictly* for potential digital forensic points of interest. Focus *only* on patterns and explicit mentions within the text provided. **Do not make assumptions beyond the text.** Output ONLY plain text.

**Biography Text:** "{biography_text}"

**Analysis Points (Use Plain Text Headings/Lists):**
1.  Potential PII Indicators: Identify any patterns that *might resemble* PII (e.g., email format `user@domain.com`, phone number patterns `XXX-XXX-XXXX`, specific location names). Note the *presence* of the pattern/mention found in the text. If none, state "No direct PII pattern indicators identified in the bio text."
2.  Explicitly Mentioned Locations: List any specific cities, states, countries, or landmarks mentioned. If none, state "No locations mentioned." Use simple list format (e.g., "- Location 1").
3.  Explicit Mentions/Connections: List any other usernames (@mentions) or specific websites (URLs beginning with http/https) found directly in the text. If none, state "No external usernames or URLs mentioned." Use simple list format.
4.  Keywords/Themes of Interest: List 3-5 key terms or concepts directly present in the bio that might be relevant for further investigation (e.g., specific technologies, project names, organizations, event names). If none, state "No specific keywords/themes identified." Use simple list format.
5.  Language/Tone Notes: Briefly comment if the language used seems unusual, coded, highly technical, or noteworthy in tone (optional, only if prominent).

**Output:** Generate ONLY the analysis notes as plain text. Use simple headings (e.g., "1. Potential PII Indicators:") and simple lists (e.g., "- Item"). **Do NOT use any markdown formatting.** State clearly if no relevant information was found for a point. Emphasize that findings are based solely on the provided text.
"""
    print("Generating forensic notes...")
    forensic_text = _call_llm(api_key, model, forensic_prompt, max_tokens, temperature)
    if forensic_text.startswith("LLM_ERROR"):
         print(f"  Forensic note generation failed: {forensic_text}")
         return f"Failed to generate forensic notes: {forensic_text}"
    print("  Forensic note generation successful.")
    return forensic_text


def extract_json_data_llm(api_key, username, biography_text):
    """Generates the structured forensic JSON data."""
    model = DEFAULT_MODEL
    max_tokens = 6000 # Needs generous tokens for complex structure + reasoning
    temperature = 0.5

    timestamp = datetime.now(pytz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    escaped_bio = json.dumps(biography_text) # Escape bio text for safe JSON embedding

    # Revised JSON prompt (more explicit graph focus, more inventive)
    json_prompt = f"""**Task:** Perform a detailed forensic analysis of the provided Instagram username and biography. Extract structured data relevant for Social Media Analysis Toolkit (SMAT) investigations. Generate ONLY a single, valid JSON object adhering strictly to the specified structure. Be exhaustive and inventive in extracting explicit graph data, even from simple bios. Infer and generate relevant details, clearly marking speculation.

**Username:** "{username}"
**Biography Text:** {escaped_bio} // Biography text is pre-escaped for JSON

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
  "linguistic_analysis": {{
    "summary": "string",
    "language": "string",
    "sentiment_overall_label": "string",
    "sentiment_overall_score": "float",
    "keywords": ["list", "of", "strings"],
    "topics": ["list", "of", "strings"],
    "writing_style_notes": "string"
  }},
  "entity_extraction": {{
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
  "network_connections_explicit": {{ // Graph based *only* on extracted_entities AND direct interpretations of bio text
    "nodes": [
      {{"id": "profile_owner", "label": "{username}", "type": "ProfileOwner"}},
      // {{"id": "unique_id", "label": "Display Name", "type": "EntityType"}}
      // CRITICAL: Include nodes representing activities/skills/concepts directly stated or clearly implied in the bio.
    ],
    "edges": [
      // {{"from": "source_id", "to": "target_id", "label": "relationship_type", "context": "from bio text"}}
      // CRITICAL: Connect the profile_owner to nodes representing activities/skills/concepts directly from the bio.
    ]
  }},
  "inferred_analysis": {{
    "potential_interests": [ {{ "interest": "string", "reasoning": "string", "confidence": "Low/Medium/High" }} ],
    "potential_affiliations": [ {{ "affiliation": "string", "reasoning": "string", "confidence": "Low/Medium/High" }} ],
    "potential_skills": [ {{ "skill": "string", "reasoning": "string", "confidence": "Low/Medium/High" }} ],
    "potential_locations": [ {{ "location": "string", "reasoning": "string", "confidence": "Low/Medium/High" }} ]
  }},
  "threat_indicators_potential": {{
    "violent_extremism_keywords": ["list", "of", "strings"],
    "misinformation_themes": ["list", "of", "strings"],
    "hate_speech_indicators": ["list", "of", "strings"],
    "self_harm_indicators": ["list", "of", "strings"],
    "overall_risk_assessment_llm": "string" // Include disclaimer in reasoning
  }},
  "cross_platform_links_potential": [
      {{ "platform": "string", "identifier": "string", "reasoning": "string" }}
  ],
  "suggestions_for_investigation": {{
    "similar_users_suggested": [ {{ "suggestion": "string", "reasoning": "string" }} ],
    "relevant_hashtags_suggested": [ {{ "suggestion": "string", "reasoning": "string" }} ],
    "topics_to_monitor": ["list", "of", "strings"]
  }}
}}

**Instructions & Constraints:**
1.  **Prioritize Forensic Relevance.**
2.  **Populate All Fields.** Use empty lists `[]` or `null`/`"Not Applicable"` if no data.
3.  **Mark Speculation:** Clearly distinguish `entity_extraction`/`network_connections_explicit` (from bio text) from inferred/generated sections.
4.  **Comprehensive & Inventive Explicit Graph:** Make `network_connections_explicit` as detailed and interconnected as possible based *only* on `entity_extraction` AND creative, direct interpretations of activities/skills/concepts in the bio text. **Be extremely inventive: Interpret every possible noun/verb/concept (e.g., "build", "stuff", "create", "design", "travel", "music", "art") as an explicit node (e.g., type "Stated Activity", "Stated Skill", "Stated Concept"). Connect these nodes exhaustively to the `profile_owner` node with appropriate relationship labels (e.g., "performs", "interested_in", "mentions"). Aim to graphically represent *all* explicit bio content, even single words, if interpretable.** Always include `profile_owner`.
5.  **Generate Boldly:** Populate inferred/generated sections even if bio is sparse.
6.  **VALID JSON ONLY:** Output MUST be a single, valid JSON object matching this structure. No extra text, comments, or explanations outside the JSON.

"""
    print("Generating structured forensic JSON data...")
    json_string = _call_llm(api_key, model, json_prompt, max_tokens, temperature)

    # Default error structure for JSON
    error_json = {"error": "Unknown JSON processing error"}

    if json_string.startswith("LLM_ERROR"):
        print(f"  Error during JSON generation call: {json_string}")
        error_json["error"] = f"LLM call failed: {json_string}"
        return error_json

    try:
        analysis_data = json.loads(json_string)
        print("  Successfully parsed forensic JSON data.")
        # Basic validation (can be expanded significantly)
        required_keys = ["analysis_metadata", "profile_context", "linguistic_analysis",
                         "entity_extraction", "network_connections_explicit",
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
            print("  Warning: Parsed JSON missing some top-level forensic keys.")
            error_json["error"] = "Parsed JSON missing required forensic keys"
            error_json["raw_response"] = json_string # Include raw response for debugging
            return error_json

    except json.JSONDecodeError as e:
        print(f"  Error: Failed to parse LLM response as JSON. {e}")
        error_json["error"] = "LLM response was not valid JSON"
        error_json["raw_response"] = json_string # Include raw response for debugging
        return error_json
    except Exception as e: # Catch other potential errors during processing
        print(f"  Error processing LLM JSON response: {e}")
        error_json["error"] = f"Error processing JSON response: {e.__class__.__name__}"
        error_json["raw_response"] = json_string
        return error_json


# --- Main Function for Parallel Execution ---

def run_all_analyses_parallel(username, biography_text):
    """Runs the three LLM analysis functions in parallel."""
    if not API_KEY or "YOUR_" in API_KEY:
         print("CRITICAL ERROR: API_KEY is missing or is a placeholder in scraper_utils.py")
         return {
             "report": "API Key Missing. Cannot run analysis.",
             "forensic_notes": "API Key Missing.",
             "json_data": {"error": "API Key Missing."}
         }

    # Ensure biography_text is a string, handle None case
    biography_text = biography_text if biography_text is not None else ""

    results = {
        "report": "Analysis Pending...",
        "forensic_notes": "Analysis Pending...",
        "json_data": {"error": "Analysis Pending..."} # Start with error state for JSON
    }

    start_time = time.time()
    print(f"--- Starting parallel LLM analyses for {username} ---")

    # Use ThreadPoolExecutor for I/O-bound tasks (API calls)
    # NOTE: Actual parallelism depends on the execution environment.
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit tasks
        future_report = executor.submit(generate_report_llm, API_KEY, username, biography_text)
        future_forensic = executor.submit(generate_forensic_analysis_llm, API_KEY, username, biography_text)
        future_json = executor.submit(extract_json_data_llm, API_KEY, username, biography_text)

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