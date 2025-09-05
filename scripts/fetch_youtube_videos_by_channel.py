import re
import time
from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def _get_channel_id_from_url(url, youtube_service):
    """
    Extracts a YouTube channel ID specifically from /@handle URL formats.
    Example: https://www.youtube.com/@GeopoliticalEconomyReport
    """
    # Pattern for /@handle format
    match = re.search(r"youtube\.com/@([A-Za-z0-9_-]+)", url)
    if match:
        search_term = match.group(1)
        try:
            # Search for the channel by its handle
            search_response = (
                youtube_service.search()
                .list(q=search_term, part="id", type="channel", maxResults=1)
                .execute()
            )
            if search_response["items"]:
                return search_response["items"][0]["id"]["channelId"]
        except HttpError as e:
            print(
                f"    -  YouTube API error while resolving channel handle '{search_term}': {e}"
            )
            return None

    print(
        f"    -  Could not determine channel ID from URL: {url}. Only '@handle' URLs are supported."
    )
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
        channel_id = _get_channel_id_from_url(source["url"], youtube_service)
        if not channel_id:
            return []

        # 2. Get the 'uploads' playlist ID from the channel ID
        channel_response = (
            youtube_service.channels()
            .list(id=channel_id, part="contentDetails")
            .execute()
        )

        if not channel_response.get("items"):
            print(f"    -  Could not find YouTube channel with ID: {channel_id}")
            return []

        uploads_playlist_id = channel_response["items"][0]["contentDetails"][
            "relatedPlaylists"
        ]["uploads"]

        # 3. Get recent videos from the 'uploads' playlist
        playlist_items = (
            youtube_service.playlistItems()
            .list(
                playlistId=uploads_playlist_id,
                part="snippet",
                maxResults=30,  # Fetch more to ensure we get recent ones
            )
            .execute()
        )

        for item in playlist_items.get("items", []):
            snippet = item["snippet"]
            published_at_str = snippet["publishedAt"]
            published_date = date_parser.isoparse(published_at_str)

            if published_date >= one_week_ago:
                video_id = snippet["resourceId"]["videoId"]
                results.append(
                    {
                        "source": source["name"],
                        "title": snippet["title"],
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "date": published_date,
                    }
                )

    except HttpError as e:
        print(f"    -  YouTube API error for source '{source['name']}': {e}")
    except Exception as e:
        print(f"    -  An unexpected error occurred for source '{source['name']}': {e}")

    return results


if __name__ == "__main__":
    # IMPORTANT: Replace with your actual YouTube Data API Key
    API_KEY = "AIzaSyBAmGmUB5hQh9FO-DxFwLyVznT_QFxDsK0"
    if API_KEY == "YOUR_API_KEY":
        print(
            "ERROR: Please replace 'YOUR_API_KEY' with your actual YouTube Data API Key."
        )
        print("Refer to the 'Setup Instructions' above.")
    else:
        # Initialize the YouTube API service
        youtube_service = build("youtube", "v3", developerKey=API_KEY)

        # Define the YouTube channels you want to fetch videos from
        # ONLY include /@handle URLs in this list
        youtube_channels_to_fetch = [
            # {
            #     "name": "Geopolitical Economy Report",
            #     "url": "https://www.youtube.com/@GeopoliticalEconomyReport",
            # },
            # {
            #     "name": "BreakThrough News",
            #     "url": "https://www.youtube.com/@BreakThroughNews",
            # },
            # {
            #     "name": "Democracy At Work",
            #     "url": "https://www.youtube.com/@democracyatwrk",
            # },
            {
                "name": "Al Jazeera English",
                "url": "https://www.youtube.com/@aljazeeraenglish",
            },
        ]

        print("Fetching recent YouTube videos...")
        all_recent_videos = []
        for channel_source in youtube_channels_to_fetch:
            print(
                f"\nProcessing channel: {channel_source['name']} ({channel_source['url']})"
            )
            videos = fetch_youtube_videos(channel_source, youtube_service)
            if videos:
                print(
                    f"Found {len(videos)} recent videos for {channel_source['name']}:"
                )
                for video in videos:
                    print(f"  - Title: {video['title']}")
                    print(f"    URL: {video['url']}")
                    print(
                        f"    Published: {video['date'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    )
                all_recent_videos.extend(videos)
            else:
                print(
                    f"No recent videos found for {channel_source['name']} in the last 7 days, or an error occurred."
                )
            time.sleep(1)

        print("\n--- Summary of all recent videos ---")
        if all_recent_videos:
            # Sort videos by date, newest first
            all_recent_videos.sort(key=lambda x: x["date"], reverse=True)
            for video in all_recent_videos:
                print(
                    f"[{video['source']}] {video['date'].strftime('%Y-%m-%d')} - {video['title']} ({video['url']})"
                )
        else:
            print("No recent videos found across all specified channels.")
