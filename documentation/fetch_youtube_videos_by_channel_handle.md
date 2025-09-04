# fetch_youtube_videos_by_channel_handle

### Setup Instructions

1.  **Google Cloud Project and API Key:**
    *   Go to the [Google Cloud Console].
    *   Create a new project or select an existing one.
    *   Navigate to "APIs & Services" > "Library".
    *   Search for "YouTube Data API v3" and enable it for your project.
    *   Go to "APIs & Services" > "Credentials".
    *   Click "Create Credentials" > "API Key".
    *   Copy the generated API key. Keep this key secure, as it grants access to your project's API usage.

2.  **Install Required Libraries:**
    You'll need to install the `google-api-python-client` and `python-dateutil` libraries. Open your terminal or command prompt and run:
    ```bash
    pip install google-api-python-client python-dateutil
    ```

### Imports

The following imports are necessary for the provided code to function correctly:

```python
import re
from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
```

### Simplified Code

```python
import re
from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Provided Functions ---

def _get_channel_id_from_url(url, youtube_service):
    """
    Extracts a YouTube channel ID specifically from /@handle URL formats.
    Example: https://www.youtube.com/@GeopoliticalEconomyReport
    """
    # Pattern for /@handle format
    match = re.search(r'youtube\.com/@([A-Za-z0-9_-]+)', url)
    if match:
        search_term = match.group(1)
        try:
            # Search for the channel by its handle
            search_response = youtube_service.search().list(
                q=search_term,
                part='id',
                type='channel',
                maxResults=1
            ).execute()
            if search_response['items']:
                return search_response['items'][0]['id']['channelId']
        except HttpError as e:
            print(f"    -  YouTube API error while resolving channel handle '{search_term}': {e}")
            return None

    print(f"    -  Could not determine channel ID from URL: {url}. Only '@handle' URLs are supported.")
    return None


def fetch_youtube_videos(source, youtube_service):
    """
    Fetches videos from a YouTube channel published in the last 7 days.

    Args:
        source (dict): A source dictionary from the config.
        youtube_service: An initialized YouTube API service object.

    Returns:
        list: A list of dictionaries, each representing a recent video.
    """
    results = []
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    try:
        # 1. Get Channel ID from URL
        channel_id = _get_channel_id_from_url(source['url'], youtube_service)
        if not channel_id:
            return []

        # 2. Get the 'uploads' playlist ID from the channel ID
        channel_response = youtube_service.channels().list(
            id=channel_id,
            part='contentDetails'
        ).execute()

        if not channel_response.get('items'):
            print(f"    -  Could not find YouTube channel with ID: {channel_id}")
            return []

        uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        # 3. Get recent videos from the 'uploads' playlist
        playlist_items = youtube_service.playlistItems().list(
            playlistId=uploads_playlist_id,
            part='snippet',
            maxResults=20  # Fetch more to ensure we get recent ones
        ).execute()

        for item in playlist_items.get('items', []):
            snippet = item['snippet']
            published_at_str = snippet['publishedAt']
            published_date = date_parser.isoparse(published_at_str)

            if published_date >= one_week_ago:
                video_id = snippet['resourceId']['videoId']
                results.append({
                    'source': source['name'],
                    'title': snippet['title'],
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'date': published_date
                })

    except HttpError as e:
        print(f"    -  YouTube API error for source '{source['name']}': {e}")
    except Exception as e:
        print(f"    -  An unexpected error occurred for source '{source['name']}': {e}")

    return results

# --- Main execution block ---

if __name__ == "__main__":
    # IMPORTANT: Replace with your actual YouTube Data API Key
    API_KEY = "YOUR_API_KEY"

    if API_KEY == "YOUR_API_KEY":
        print("ERROR: Please replace 'YOUR_API_KEY' with your actual YouTube Data API Key.")
        print("Refer to the 'Setup Instructions' above.")
    else:
        # Initialize the YouTube API service
        youtube_service = build('youtube', 'v3', developerKey=API_KEY)

        # Define the YouTube channels you want to fetch videos from
        # ONLY include /@handle URLs in this list
        youtube_channels_to_fetch = [
            {"name": "Geopolitical Economy Report", "url": "https://www.youtube.com/@GeopoliticalEconomyReport"},
            {"name": "MrBeast", "url": "https://www.youtube.com/@MrBeast"},
            {"name": "Veritasium", "url": "https://www.youtube.com/@veritasium"},
            # Add more channels here as needed, ensuring they are /@handle format
            # {"name": "Another Channel", "url": "https://www.youtube.com/@AnotherHandle"}
        ]

        print("Fetching recent YouTube videos...")
        all_recent_videos = []
        for channel_source in youtube_channels_to_fetch:
            print(f"\nProcessing channel: {channel_source['name']} ({channel_source['url']})")
            videos = fetch_youtube_videos(channel_source, youtube_service)
            if videos:
                print(f"Found {len(videos)} recent videos for {channel_source['name']}:")
                for video in videos:
                    print(f"  - Title: {video['title']}")
                    print(f"    URL: {video['url']}")
                    print(f"    Published: {video['date'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
                all_recent_videos.extend(videos)
            else:
                print(f"No recent videos found for {channel_source['name']} in the last 7 days, or an error occurred.")

        print("\n--- Summary of all recent videos ---")
        if all_recent_videos:
            # Sort videos by date, newest first
            all_recent_videos.sort(key=lambda x: x['date'], reverse=True)
            for video in all_recent_videos:
                print(f"[{video['source']}] {video['date'].strftime('%Y-%m-%d')} - {video['title']} ({video['url']})")
        else:
            print("No recent videos found across all specified channels.")
```

### How to Run This Code

1.  **Save the code:** Save the complete code block above into a Python file (e.g., `youtube_handle_fetcher.py`).
2.  **Replace `YOUR_API_KEY`:** Open the saved file and replace `"YOUR_API_KEY"` with the actual API key you obtained from the Google Cloud Console.
3.  **Update `youtube_channels_to_fetch`:** Modify the `youtube_channels_to_fetch` list to include *only* YouTube channel URLs that use the `@handle` format.
4.  **Execute the script:** Open your terminal or command prompt, navigate to the directory where you saved the file, and run:
    ```bash
    python youtube_handle_fetcher.py
    ```

The script will now specifically process channels using the `youtube.com/@YourHandle` URL format to fetch their recent videos.

### What Videos are Fetched?

The code generally fetches **all public video content** from a YouTube channel within the specified timeframe (the last 7 days), because it targets the channel's "uploads" playlist.

Here's why:

*   **The "Uploads" Playlist:** The YouTube Data API provides access to a special system-generated playlist for each channel called the "uploads" playlist. This playlist automatically contains every public video that has been uploaded to that channel. [[1]](https://developers.google.com/youtube/v3/docs/playlists)[[2]](https://developers.google.com/youtube/v3/docs)
*   **What's Included:**
    *   **Regular Videos:** All standard, long-form videos uploaded by the channel will be in this playlist.
    *   **YouTube Shorts:** If a YouTube Short is uploaded as a video (which is the common method for creators to publish them), it will also appear in the channel's "uploads" playlist and thus be fetched by this code. Shorts can be added to and organized within playlists. [[3]](https://m.youtube.com/watch?v=b-m_RshSZv0)[[4]](https://predis.ai/resources/add-youtube-shorts-to-a-playlist/)
    *   **Past Live Streams:** Once a live stream concludes and is processed by YouTube, it typically becomes a regular video (Video On Demand - VOD) and is added to the channel's "uploads" playlist.
*   **What's Not Included:**
    *   **Private or Unlisted Videos:** The API, when used with a public API key, will only access publicly available content. Private or unlisted videos are not included.
    *   **Future or Ongoing Live Streams:** Only completed live streams that have been converted to VODs will appear.
    *   **Non-Video Content:** The code does not fetch other types of channel content like community posts, channel "Stories," or channel sections that are not directly video playlists.
    *   **Content Outside the Timeframe:** The code specifically filters for videos published in the last 7 days, so any video content older than that will not be included, even if it's in the "uploads" playlist.

---
Learn more:
1. [Playlists | YouTube Data API - Google for Developers](https://developers.google.com/youtube/v3/docs/playlists)
2. [API Reference | YouTube Data API - Google for Developers](https://developers.google.com/youtube/v3/docs)
3. [How To Save YouTube Shorts To Playlist (2023)](https://m.youtube.com/watch?v=b-m_RshSZv0)
4. [How to Add YouTube Shorts to a Playlist? - Predis.ai](https://predis.ai/resources/add-youtube-shorts-to-a-playlist/)
