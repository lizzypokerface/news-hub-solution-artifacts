# generate_youtube_channel_digest

Here is the updated script. It no longer requires `youtube-transcript-api` and instead focuses on inferring the weekly narrative purely from the video titles.

### `generate_digest_from_titles.py`

```python
import re
import sys
import time
from datetime import datetime, timedelta, timezone

# --- Setup and Configuration ---

# 1. Install Required Python Libraries:
#    pip install google-api-python-client python-dateutil langchain langchain_community

# 2. Get a YouTube Data API Key:
#    - Follow instructions at: https://developers.google.com/youtube/v3/getting-started
#    - Enable the "YouTube Data API v3" in your Google Cloud Console.
#    - Create an API Key and paste it into the `API_KEY` variable below.

# 3. Install and Run Ollama:
#    - Download and install Ollama from https://ollama.com
#    - In your terminal, pull the Llama 3 model: `ollama run llama3`
#    - IMPORTANT: The Ollama application must be running in the background.

try:
    from dateutil import parser as date_parser
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from langchain_community.llms import Ollama
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
except ImportError as e:
    print(f"Error: A required library is not installed. {e}", file=sys.stderr)
    print("Please run: pip install google-api-python-client python-dateutil langchain langchain_community", file=sys.stderr)
    sys.exit(1)


# --- Part 1: Fetching YouTube Videos (Adapted from info.txt) ---

def _get_channel_id_from_url(url, youtube_service):
    """Extracts a YouTube channel ID from a /@handle URL."""
    match = re.search(r"youtube\.com/(@[A-Za-z0-9_.-]+)", url)
    if not match:
        print(f"    -  Could not parse handle from URL: {url}. Only '@handle' URLs are supported.")
        return None

    handle = match.group(1)
    try:
        search_response = youtube_service.search().list(
            q=handle, part="id", type="channel", maxResults=1
        ).execute()
        if search_response.get("items"):
            return search_response["items"][0]["id"]["channelId"]
        else:
            print(f"    -  Could not find a channel for handle '{handle}'.")
            return None
    except HttpError as e:
        print(f"    -  YouTube API error resolving handle '{handle}': {e}")
        return None

def fetch_recent_youtube_videos(source, youtube_service):
    """Fetches video titles from a YouTube channel published in the last 7 days."""
    results = []
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    try:
        channel_id = _get_channel_id_from_url(source["url"], youtube_service)
        if not channel_id:
            return []

        channel_response = youtube_service.channels().list(
            id=channel_id, part="contentDetails"
        ).execute()
        if not channel_response.get("items"):
            print(f"    -  Could not find channel details for ID: {channel_id}")
            return []

        uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        playlist_items = youtube_service.playlistItems().list(
            playlistId=uploads_playlist_id, part="snippet", maxResults=50
        ).execute()

        for item in playlist_items.get("items", []):
            snippet = item["snippet"]
            published_date = date_parser.isoparse(snippet["publishedAt"])

            if published_date >= one_week_ago:
                results.append(snippet["title"])

        results.reverse() # Sort by oldest first for a chronological list
        return results

    except HttpError as e:
        print(f"    -  YouTube API error for '{source['name']}': {e}")
    except Exception as e:
        print(f"    -  An unexpected error occurred for '{source['name']}': {e}")
    return []


# --- Part 2: AI Summarization from Titles ---

def create_commentary_from_titles(channel_name, titles, llm_chain):
    """
    Generates a weekly commentary by inferring themes from a list of video titles.
    """
    if not titles:
        return "No video titles were available to generate a commentary."

    # Format the list of titles into a clean, numbered string for the prompt
    formatted_titles = "\n".join(f"{i+1}. {title}" for i, title in enumerate(titles))

    try:
        print("    -> Sending title list to Ollama for analysis...")
        result = llm_chain.invoke({
            "channel_name": channel_name,
            "title_list": formatted_titles
        })
        return result['text'].strip()
    except Exception as e:
        return f"Commentary could not be generated. Error communicating with Ollama: {e}"


# --- Main Execution Block ---

if __name__ == "__main__":
    # IMPORTANT: Replace with your actual YouTube Data API Key
    API_KEY = "YOUR_API_KEY"  # <--- PASTE YOUR KEY HERE

    if API_KEY == "YOUR_API_KEY":
        print("ERROR: Please replace 'YOUR_API_KEY' with your actual YouTube Data API Key in the script.", file=sys.stderr)
        sys.exit(1)

    # --- Define Channels to Analyze ---
    youtube_channels_to_process = [
        {
            "name": "Geopolitical Economy Report",
            "url": "https://www.youtube.com/@GeopoliticalEconomyReport",
        },
        {
            "name": "BreakThrough News",
            "url": "https://www.youtube.com/@BreakThroughNews",
        },
        {
            "name": "Al Jazeera English",
            "url": "https://www.youtube.com/@aljazeeraenglish",
        },
    ]

    print("--- Initializing Services for Weekly YouTube Digest from Titles ---")

    # --- Initialize API and AI Services ---
    try:
        youtube_service = build("youtube", "v3", developerKey=API_KEY)

        # This new prompt is specifically designed to work with titles only
        prompt_template = """
You are a media analyst creating a weekly digest. Your task is to infer the main themes and narrative of a YouTube channel's content over the past week, based *only* on the list of video titles provided below.

Synthesize these titles into a coherent running commentary of about 100-150 words. Speculate on the overarching story or topics the channel focused on. Do not just list the titles; instead, tell the story that the titles suggest.

CHANNEL NAME: {channel_name}

VIDEO TITLES FROM THE PAST WEEK:
{title_list}

INFERRED WEEKLY COMMENTARY:
"""
        prompt = PromptTemplate(template=prompt_template, input_variables=["channel_name", "title_list"])
        llm = Ollama(model="llama3")
        llm_chain = LLMChain(prompt=prompt, llm=llm)

    except Exception as e:
        print(f"\nFatal Error during initialization: {e}", file=sys.stderr)
        print("Please ensure Ollama is running and your API key is valid.", file=sys.stderr)
        sys.exit(1)

    print("Initialization complete. Starting channel processing...\n")

    # --- Main Loop for Each Channel ---
    for channel in youtube_channels_to_process:
        print(f"--- Processing Channel: {channel['name']} ---")

        # 1. Fetch recent video titles
        print("  - Step 1: Fetching recent video titles from the last 7 days...")
        video_titles = fetch_recent_youtube_videos(channel, youtube_service)

        if not video_titles:
            print("    -> No recent videos found or an API error occurred.\n")
            time.sleep(1)
            continue

        print(f"    -> Found {len(video_titles)} recent video(s).")

        # 2. Create weekly commentary from the list of titles
        print("  - Step 2: Generating weekly commentary from titles...")
        weekly_commentary = create_commentary_from_titles(channel['name'], video_titles, llm_chain)

        print("\n" + "="*25 + f" WEEKLY DIGEST for {channel['name']} " + "="*25)
        print(weekly_commentary)
        print("="* (68 + len(channel['name'])), "\n")

        time.sleep(1) # Be respectful to the API

    print("--- All Channels Processed ---")
```

### Key Changes and How It Works

1.  **No Transcripts**: The `youtube-transcript-api` library is no longer needed and has been removed from the imports and setup instructions. The `get_youtube_transcript` function is also gone.
2.  **`fetch_recent_youtube_videos` Modified**: This function now directly returns a simple list of video titles (`['Title 1', 'Title 2', ...]`) instead of a list of dictionaries.
3.  **New Prompt Template**: The `PromptTemplate` has been completely rewritten. It now explicitly instructs the LLM to act as a media analyst who must *infer* and *synthesize* a narrative based *only* on a list of titles. This is a higher-level reasoning task compared to summarization.
4.  **`create_commentary_from_titles`**: This new function takes the list of titles, formats them into a clean, numbered list string, and passes this string to the LLM chain.
5.  **Simplified Main Loop**: The main loop is now much cleaner. It fetches the titles and immediately passes them to the commentary function. There is no intermediate step of extracting transcripts.

This version is much more efficient and achieves the goal of creating a "running commentary" by leveraging the powerful inference capabilities of Llama 3 to connect the dots between video titles.
