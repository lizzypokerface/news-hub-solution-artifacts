# what_the_world_is_saying

Excellent. This is a great way to structure a project, separating configuration from the core logic. We will build the `what_is_the_world_saying.py` script to be driven by the `test_config.yaml` file.

The script will include a `ConfigManager` class, filter for `datapoint` YouTube sources, fetch their video titles, synthesize the events using Ollama, and finally, save the structured data into a timestamped JSON file.

### `what_is_the_world_saying.py`

```python
import os
import re
import sys
import json
import time
from datetime import datetime, timedelta, timezone

# --- Setup and Configuration ---

# 1. Install Required Python Libraries:
#    pip install PyYAML google-api-python-client python-dateutil langchain langchain_community

# 2. Create the YAML config file:
#    - Create a folder named 'configs' in the parent directory of this script.
#    - Inside 'configs', create a file named 'test_config.yaml' with the content you provided.
#    - The script assumes the path '../configs/test_config.yaml'.

# 3. Install and Run Ollama:
#    - Download and install Ollama from https://ollama.com
#    - In your terminal, pull the Llama 3 model: `ollama run llama3`
#    - IMPORTANT: The Ollama application must be running in the background.

try:
    import yaml
    from dateutil import parser as date_parser
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from langchain_community.llms import Ollama
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
except ImportError as e:
    print(f"Error: A required library is not installed. {e}", file=sys.stderr)
    print("Please run: pip install PyYAML google-api-python-client python-dateutil langchain langchain_community", file=sys.stderr)
    sys.exit(1)


# --- Part 1: Configuration Management ---

class ConfigManager:
    """Handles loading and accessing the YAML configuration file."""
    def __init__(self, config_path='../configs/test_config.yaml'):
        self.config_path = config_path
        self.config = None

    def load_config(self):
        """Loads the YAML file into memory."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            print(f"Configuration loaded successfully from '{self.config_path}'")
            return True
        except FileNotFoundError:
            print(f"FATAL: Configuration file not found at '{self.config_path}'", file=sys.stderr)
            return False
        except yaml.YAMLError as e:
            print(f"FATAL: Error parsing YAML file: {e}", file=sys.stderr)
            return False

    def get_api_key(self):
        return self.config.get('api_keys', {}).get('youtube_api')

    def get_output_directory(self):
        return self.config.get('output_directory', 'outputs/')

    def get_sources(self):
        return self.config.get('sources', [])


# --- Part 2: YouTube Data Fetching ---

def _get_channel_id_from_url(url, youtube_service):
    """Extracts a YouTube channel ID from a /@handle URL."""
    match = re.search(r"youtube\.com/(@[A-Za-z0-9_.-]+)", url)
    if not match: return None
    handle = match.group(1)
    try:
        search_response = youtube_service.search().list(q=handle, part="id", type="channel", maxResults=1).execute()
        return search_response["items"][0]["id"]["channelId"] if search_response.get("items") else None
    except HttpError: return None

def fetch_recent_youtube_titles(source, youtube_service):
    """Fetches video titles from a YouTube channel published in the last 7 days."""
    results = []
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    try:
        channel_id = _get_channel_id_from_url(source["url"], youtube_service)
        if not channel_id: return []
        channel_response = youtube_service.channels().list(id=channel_id, part="contentDetails").execute()
        if not channel_response.get("items"): return []
        uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        playlist_items = youtube_service.playlistItems().list(playlistId=uploads_playlist_id, part="snippet", maxResults=50).execute()
        for item in playlist_items.get("items", []):
            snippet = item["snippet"]
            if date_parser.isoparse(snippet["publishedAt"]) >= one_week_ago:
                results.append(snippet["title"])
        results.reverse()
        return results
    except (HttpError, Exception) as e:
        print(f"    -  An error occurred for '{source['name']}': {e}")
    return []


# --- Part 3: AI Synthesis ---

def synthesize_events_from_titles(channel_name, titles, llm_chain):
    """Generates a compact list of events by synthesizing a list of video titles."""
    if not titles: return "No video titles were available to synthesize."
    formatted_titles = "\n".join(f"- {title}" for title in titles)
    try:
        print("    -> Sending title list to Ollama for synthesis...")
        result = llm_chain.invoke({"channel_name": channel_name, "title_list": formatted_titles})
        return result['text'].strip()
    except Exception as e:
        return f"Event synthesis failed. Error communicating with Ollama: {e}"


# --- Main Execution Block ---

if __name__ == "__main__":
    print("--- Starting 'What is the World Saying' ---")

    # 1. Load Configuration
    config_manager = ConfigManager(config_path='../configs/test_config.yaml')
    if not config_manager.load_config():
        sys.exit(1)

    API_KEY = config_manager.get_api_key()
    OUTPUT_DIR = config_manager.get_output_directory()
    SOURCES = config_manager.get_sources()

    if not API_KEY or "AIzaSyxxxxxxxx" in API_KEY:
        print("FATAL: YouTube API key is missing or is a placeholder in the config file.", file=sys.stderr)
        sys.exit(1)

    # 2. Initialize Services
    try:
        youtube_service = build("youtube", "v3", developerKey=API_KEY)
        prompt_template = """
You are an information synthesizer. Your task is to analyze the following list of YouTube video titles and identify the distinct, ongoing events or topics they cover.
From this list, extract the individual ongoing events. Each event must be presented as a short sentence or phrase of 10-15 words.
Your final output must be a single, compact text block containing these short sentences, separated by commas. Do not use bullet points, numbering, or introductory text.
EXAMPLE OUTPUT:
Something happening in Libya, something happening in Somalia, continuation of problems in Africa, continuation of problems in America, transpacific trade deal something happening.
CHANNEL NAME: {channel_name}
VIDEO TITLES FROM THE PAST WEEK:
{title_list}
COMPACT EVENT SUMMARY:
"""
        prompt = PromptTemplate(template=prompt_template, input_variables=["channel_name", "title_list"])
        llm = Ollama(model="llama3")
        llm_chain = LLMChain(prompt=prompt, llm=llm)
    except Exception as e:
        print(f"\nFatal Error during service initialization: {e}", file=sys.stderr)
        print("Please ensure Ollama is running and your API key is valid.", file=sys.stderr)
        sys.exit(1)

    print("Services initialized successfully.\n")

    # 3. Filter for relevant sources
    datapoint_sources = [
        s for s in SOURCES
        if s.get('type') == 'datapoint' and s.get('format') == 'youtube'
    ]

    if not datapoint_sources:
        print("No sources with type 'datapoint' and format 'youtube' found in config file.")
        sys.exit(0)

    # 4. Main Processing Loop
    all_results = []
    for source in datapoint_sources:
        print(f"--- Processing Source: {source['name']} ---")

        video_titles = fetch_recent_youtube_titles(source, youtube_service)

        if not video_titles:
            print("    -> No recent videos found or an API error occurred.\n")
            time.sleep(1)
            continue

        print(f"    -> Found {len(video_titles)} recent video title(s).")

        event_summary = synthesize_events_from_titles(source['name'], video_titles, llm_chain)

        # Construct the dictionary for this source
        source_result = {
            "source": source['name'],
            "titles": video_titles,
            "llm_synthesis": event_summary
        }
        all_results.append(source_result)

        print(f"    -> Synthesis complete for {source['name']}.\n")
        time.sleep(1)

    # 5. Save Output to JSON
    if not all_results:
        print("--- Processing complete. No data was generated to save. ---")
        sys.exit(0)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_filename = f"world_saying_{datetime.now().strftime('%Y-%m-%d')}.json"
    output_filepath = os.path.join(OUTPUT_DIR, output_filename)

    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"--- Processing complete. ---")
        print(f"✅ Output successfully saved to: {output_filepath}")
    except IOError as e:
        print(f"FATAL: Could not write to output file '{output_filepath}'. Error: {e}", file=sys.stderr)

```
