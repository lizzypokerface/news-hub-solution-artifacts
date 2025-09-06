import re
import logging
import pandas as pd
from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser
from googleapiclient.errors import HttpError

# Configure basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def _get_channel_id_from_url(url: str, youtube_service) -> str | None:
    """
    Extracts a YouTube channel ID from a URL, supporting /@handle formats.

    Args:
        url (str): The URL of the YouTube channel.
        youtube_service: An initialized YouTube API service object.

    Returns:
        The channel ID as a string, or None if it cannot be resolved.
    """
    match = re.search(r"youtube\.com/(@[A-Za-z0-9_-]+)", url)
    if not match:
        logging.warning(
            f"Could not find a valid handle in URL: {url}. Only '@handle' URLs are supported."
        )
        return None

    handle = match.group(1)
    try:
        search_response = (
            youtube_service.search()
            .list(q=handle, part="id", type="channel", maxResults=1)
            .execute()
        )
        if search_response.get("items"):
            channel_id = search_response["items"][0]["id"]["channelId"]
            logging.info(
                f"Successfully resolved handle '{handle}' to channel ID '{channel_id}'."
            )
            return channel_id
        else:
            logging.warning(f"Could not find a channel with the handle: {handle}")
            return None
    except HttpError as e:
        logging.error(f"YouTube API error while resolving handle '{handle}': {e}")
        return None


def fetch_youtube_video_data(
    source: dict,
    youtube_service,
    max_results: int = 50,
    weeks_ago: int = 1,
) -> pd.DataFrame:
    """
    Fetches recent videos from a YouTube channel and returns them as a DataFrame.

    This is the primary callable function of the module. It checks that the
    source format is 'youtube' before processing.

    Args:
        source (dict): A dictionary containing source details.
                       Expected keys: 'name', 'url', 'type', 'format'.
        youtube_service: An initialized YouTube API service object.
        max_results (int): The maximum number of videos to retrieve from the playlist.
                           Defaults to 50.
        weeks_ago (int): The number of weeks back to search for videos.
                         Defaults to 1.

    Returns:
        pd.DataFrame: A DataFrame containing video data with columns:
                      ['source', 'type', 'format', 'title', 'url', 'region'].
                      Returns an empty DataFrame if no videos are found or an error occurs.
    """
    # Define the expected columns for the output DataFrame
    output_columns = ["source", "type", "format", "title", "url", "region"]

    # This guard clause ensures we only process YouTube sources with this function.
    if source.get("format") != "youtube":
        logging.warning(
            f"Source '{source['name']}' has format '{source.get('format')}' and will be skipped. "
            "Only 'youtube' format is supported by this function."
        )
        return pd.DataFrame(columns=output_columns)

    video_data_list = []
    cutoff_date = datetime.now(timezone.utc) - timedelta(weeks=weeks_ago)

    try:
        channel_id = _get_channel_id_from_url(source["url"], youtube_service)
        if not channel_id:
            return pd.DataFrame(columns=output_columns)

        channel_response = (
            youtube_service.channels()
            .list(id=channel_id, part="contentDetails")
            .execute()
        )
        if not channel_response.get("items"):
            logging.warning(
                f"Could not find YouTube channel details for ID: {channel_id}"
            )
            return pd.DataFrame(columns=output_columns)

        uploads_playlist_id = channel_response["items"][0]["contentDetails"][
            "relatedPlaylists"
        ]["uploads"]

        playlist_items = (
            youtube_service.playlistItems()
            .list(
                playlistId=uploads_playlist_id,
                part="snippet",
                maxResults=max_results,
            )
            .execute()
        )

        for item in playlist_items.get("items", []):
            snippet = item["snippet"]
            published_date = date_parser.isoparse(snippet["publishedAt"])

            if published_date >= cutoff_date:
                video_id = snippet["resourceId"]["videoId"]
                video_data_list.append(
                    {
                        "source": source["name"],
                        "type": source["type"],
                        "format": source["format"],  # --- New: Added format column ---
                        "title": snippet["title"],
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "region": "",
                    }
                )

        logging.info(
            f"Found {len(video_data_list)} recent videos for source '{source['name']}'."
        )

    except HttpError as e:
        logging.error(
            f"A YouTube API error occurred for source '{source['name']}': {e}"
        )
    except Exception as e:
        logging.error(
            f"An unexpected error occurred for source '{source['name']}': {e}"
        )

    if not video_data_list:
        return pd.DataFrame(columns=output_columns)

    df = pd.DataFrame(video_data_list)

    # Ensure the column order is exactly as requested
    return df[output_columns]
