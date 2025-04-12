import requests
import time
import json
import os # Added for potential env var usage later
import re # Added for parsing mentions
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
# Consider using WebDriverWait for more robust waits
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.by import By

# You might need webdriver-manager if ChromeDriver isn't in your PATH
# pip install selenium webdriver-manager
# from webdriver_manager.chrome import ChromeDriverManager 


def get_instagram_profile_info(username, cookies):
    if not cookies:
        print("Cannot fetch profile info without cookies.")
        return None

    # Ensure essential login cookies are present
    if not all(k in cookies for k in ("sessionid", "ds_user_id", "csrftoken")):
        print("Error: Missing required login cookies (sessionid, ds_user_id, csrftoken).")
        print("Please provide these cookies obtained after logging into Instagram.")
        return None

    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"

    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "referer": f"https://www.instagram.com/{username}/",
        "sec-ch-prefers-color-scheme": "dark",
        # Update UA/platform if needed, but often less critical when logged in
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        # Use the provided csrftoken
        "x-csrftoken": cookies.get("csrftoken"),
        "x-ig-app-id": "936619743392459",
        # These might not be strictly necessary when authenticated with sessionid
        # "x-asbd-id": "129477",
        # "x-ig-www-claim": "0",
        "x-requested-with": "XMLHttpRequest",
        # Add user ID header, sometimes helps
        "x-ig-user-id": cookies.get("ds_user_id")
    }

    try:
        # Pass the cookies dict directly to requests
        response = requests.get(url, headers=headers, cookies=cookies, timeout=15) # Increased timeout slightly

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"Response status: {e.response.status_code}")
             # Limit printing potentially large HTML responses in case of failure
             content_type = e.response.headers.get('Content-Type', '')
             if 'text' in content_type or 'json' in content_type:
                 print(f"Response text: {e.response.text[:500]}...")
             else:
                 print(f"Response content type: {content_type}")
        return None
    except json.JSONDecodeError:
        print("Failed to decode JSON response.")
        # Don't assume response exists if JSON decoding failed after a successful status
        # print(f"Response text: {response.text[:500]}...")
        return None


def main():
    username = "sw_vit"

    # --- Manually Provided Cookies ---
    # IMPORTANT: Storing sensitive cookies directly in code is not recommended
    # for production. Consider using environment variables or a config file.
    # Example using environment variables (if set):
    # session_id = os.getenv("INSTAGRAM_SESSIONID")
    # ds_user_id_val = os.getenv("INSTAGRAM_DS_USER_ID")
    # csrf_token_val = os.getenv("INSTAGRAM_CSRFTOKEN")

    # Using the provided values directly for this example:
    session_id = "60078234834%3ArnOpb62xkuBKLX%3A12%3AAYdh5WMhR7y-1xVo9yDHZKbSLxGNni6cnQPsPYyIRiMR"
    ds_user_id_val = "60078234834"
    csrf_token_val = "f0n3xVrSHEcNRC0MKk4N9XIGBq8RxrHx"

    if not all([session_id, ds_user_id_val, csrf_token_val]):
        print("Error: One or more required cookies (sessionid, ds_user_id, csrftoken) are missing.")
        print("Please provide them manually in the script or via environment variables.")
        return

    cookies = {
        "sessionid": session_id,
        "ds_user_id": ds_user_id_val,
        "csrftoken": csrf_token_val,
        # Include other common cookies if available/needed, though often optional with sessionid
        # "mid": "...",
        # "ig_did": "...",
    }

    print(f"Attempting to fetch profile info for '{username}' using provided cookies...")

    profile_info = get_instagram_profile_info(username, cookies)

    if profile_info:
        output_filename = f"{username}_profile_info.json"
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(profile_info, f, ensure_ascii=False, indent=4)
            print(f"Successfully fetched profile info and saved to {output_filename}")

            # Optional summary print
            user_data = profile_info.get('data', {}).get('user', {})
            print(f"  Full Name: {user_data.get('full_name')}")
            print(f"  Biography: {user_data.get('biography', '')[:100]}...")
            print(f"  Followers: {user_data.get('edge_followed_by', {}).get('count')}")
            print(f"  Following: {user_data.get('edge_follow', {}).get('count')}")
            print(f"  Is Private: {user_data.get('is_private')}")
            print(f"  Is Verified: {user_data.get('is_verified')}") # Added verified status

        except IOError as e:
            print(f"Error writing profile info to file: {e}")
        except Exception as e:
            print(f"An unexpected error occurred processing the profile info: {e}")

    else:
        print(f"Error fetching profile info for '{username}'. Check cookies and network.")


def parse_profile_data(filename):
    """Parses the saved JSON profile data to extract relevant post information."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at {filename}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filename}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred reading {filename}: {e}")
        return None

    extracted_posts = []
    user_data = profile_data.get('data', {}).get('user', {})
    posts_data = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])

    if not posts_data:
        print("No posts found in the JSON data.")
        return []

    print(f"Found {len(posts_data)} posts. Parsing details...")

    for edge in posts_data:
        node = edge.get('node', {})
        if not node:
            continue

        # --- Extract Caption ---
        caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
        caption = caption_edges[0].get('node', {}).get('text') if caption_edges else None

        # --- Extract Comments ---
        # Note: The API usually only returns the count and maybe a few preview comments.
        # Full comment scraping often requires different techniques/endpoints.
        comment_info = node.get('edge_media_to_comment', {})
        comment_count = comment_info.get('count')
        # Example of getting preview comment texts if available (adjust key names if needed)
        comment_texts = [
            cmt_edge.get('node', {}).get('text')
            for cmt_edge in comment_info.get('edges', [])
            if cmt_edge.get('node')
        ]

        # --- Extract Tagged Users (from caption mentions) ---
        tagged_users = []
        if caption:
            # Simple regex to find @mentions
            tagged_users = re.findall(r'@(\w+)', caption)

        # --- Extract Other Details ---
        post_info = {
            'id': node.get('id'),
            'shortcode': node.get('shortcode'),
            'timestamp': node.get('taken_at_timestamp'),
            'media_type': node.get('__typename'),
            'display_url': node.get('display_url'),
            'likes_count': node.get('edge_liked_by', {}).get('count'),
            'comments_count': comment_count,
            'caption': caption,
            'comment_previews': comment_texts, # Store preview texts if found
            'tagged_users_in_caption': tagged_users,
            # Placeholder for tags from 'usertags' if that field exists
            # 'tagged_users_in_photo': [tag_edge.get('node',{}).get('user',{}).get('username')
            #                           for tag_edge in node.get('usertags', {}).get('edges', [])
            #                           if tag_edge.get('node',{}).get('user')]
        }
        extracted_posts.append(post_info)

    print(f"Successfully parsed {len(extracted_posts)} posts.")
    return extracted_posts


def get_instagram_cookies(driver: webdriver.Chrome):
    """
    Attempts to retrieve cookies from the current Instagram session.
    Assumes the user is *already logged in* within the browser session 
    controlled by the driver.

    Args:
        driver: An active Selenium WebDriver instance potentially logged into Instagram.

    Returns:
        A list of cookie dictionaries obtained from the browser, 
        or None if an error occurs or no cookies are found.
    """
    try:
        # Optional: Navigate to a page that confirms login state, like the profile edit page
        # driver.get("https://www.instagram.com/accounts/edit/")
        # Or simply ensure you are on an Instagram page
        current_url = driver.current_url
        if "instagram.com" not in current_url:
            print("Warning: Not on an Instagram domain. Navigating to homepage.")
            driver.get("https://www.instagram.com/")
            # Using a fixed sleep based on your original code.
            # Replace with WebDriverWait for better reliability.
            time.sleep(5) 

        print("Attempting to retrieve cookies...")
        cookies = driver.get_cookies()

        if not cookies:
            print("No cookies found. Ensure you are logged in to Instagram in this browser session.")
            return None

        print(f"Successfully retrieved {len(cookies)} cookies.")
        
        # The 'sessionid' cookie is typically the main session identifier.
        session_cookie = next((cookie for cookie in cookies if cookie['name'] == 'sessionid'), None)
        if session_cookie:
             # Avoid printing the full sensitive session ID value in logs
            print(f"Found 'sessionid' cookie (value starts with: {session_cookie['value'][:10]}...).")
        else:
            print("Warning: The 'sessionid' cookie was not found. You might not be fully logged in.")

        # The original code also checked localStorage for 'Session'. This might be
        # specific to a particular flow or older version. Usually, HTTP cookies 
        # (like 'sessionid') are sufficient for session management.
        # If you specifically need that localStorage item:
        # try:
        #     session_local = driver.execute_script("return window.localStorage.getItem('Session');")
        #     print(f"Value from localStorage for key 'Session': {session_local}")
        # except Exception as e:
        #     print(f"Could not retrieve 'Session' from localStorage: {e}")


        return cookies

    except WebDriverException as e:
        print(f"A WebDriver error occurred: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


if __name__ == "__main__":
    main()

    # --- Add parsing step after main execution ---
    # Assuming main() saves the file before this runs
    username_for_file = "sw_vit" # Make sure this matches the username used in main()
    json_filename = f"{username_for_file}_profile_info.json"

    if os.path.exists(json_filename):
        parsed_data = parse_profile_data(json_filename)
        if parsed_data:
            print(f"\n--- Example Parsed Data (First Post) ---")
            if parsed_data:
                # Print details of the first post as an example
                # Use json.dumps for cleaner dictionary printing
                print(json.dumps(parsed_data[0], indent=2, ensure_ascii=False))
            else:
                print("No posts were parsed.")

            # Here you would typically pass parsed_data to your visualization functions
            # e.g., perform_sentiment_analysis(parsed_data)
            #       generate_tagged_user_graph(parsed_data)
            #       etc.
    else:
        print(f"\nJSON file {json_filename} not found. Skipping parsing step.")
        print("Ensure the main scraping function ran successfully first.")

    # --- Example Usage ---
    # You would need to instantiate the driver and handle login *before* calling the function.

    # Example (Conceptual - requires manual login in the browser):
    # if __name__ == "__main__":
    #     options = webdriver.ChromeOptions()
    #     # Add any necessary options (e.g., user data directory if you want to use an existing profile)
    #     # options.add_argument("user-data-dir=/path/to/your/chrome/profile") 
    #     service = Service() # Assumes chromedriver is in PATH or use ChromeDriverManager
    #     driver = webdriver.Chrome(service=service, options=options)
    
    #     try:
    #         driver.get("https://www.instagram.com/accounts/login/")
    #         print("Please log in to Instagram in the browser window that opened.")
    #         print("Press Enter in this console after you have logged in...")
    #         input() # Pauses script execution until user presses Enter

    #         # Now that login is presumably done, get the cookies
    #         ig_cookies = get_instagram_cookies(driver)

    #         if ig_cookies:
    #             print("\n--- Retrieved Cookies ---")
    #             # Process or save the cookies as needed
    #             for cookie in ig_cookies:
    #                  print(f"- {cookie['name']}: {cookie['value'][:20]}...") # Print truncated value
            
    #             # You could save these cookies to a file (e.g., using json)
    #             # import json
    #             # with open("instagram_cookies.json", "w") as f:
    #             #     json.dump(ig_cookies, f)
    #             # print("\nCookies saved to instagram_cookies.json")

    #     except Exception as e:
    #         print(f"An error occurred during the process: {e}")
    #     finally:
    #         if 'driver' in locals() and driver:
    #             print("Closing browser...")
    #             driver.quit()