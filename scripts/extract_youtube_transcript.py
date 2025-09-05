import sys
from urllib.parse import urlparse, parse_qs

# --- Setup and Configuration ---

# 1. Install Required Library:
#    pip install youtube-transcript-api
#    (As per the documentation: https://pypi.org/project/youtube-transcript-api/)

try:
    from youtube_transcript_api import (
        YouTubeTranscriptApi,
        TranscriptsDisabled,
        NoTranscriptFound,
    )
except ImportError:
    print(
        "Error: The 'youtube-transcript-api' library is not installed.", file=sys.stderr
    )
    print(
        "Please install it by running: pip install youtube-transcript-api",
        file=sys.stderr,
    )
    sys.exit(1)


# --- Core Transcript Extraction Function (Updated) ---


def get_youtube_transcript(video_url: str) -> str | None:
    """
    Extracts the full, clean transcript from a YouTube video URL using the correct
    API usage as per the official documentation.

    Args:
        video_url: The full URL of the YouTube video.

    Returns:
        A single, compact string containing the entire transcript, or None if an
        error occurs.
    """
    video_id = None
    try:
        # Parse the URL to robustly find the video ID
        parsed_url = urlparse(video_url)
        if "youtube.com" in parsed_url.hostname:
            video_id = parse_qs(parsed_url.query).get("v", [None])[0]
        elif "youtu.be" in parsed_url.hostname:
            video_id = parsed_url.path.lstrip("/")

        if not video_id:
            print(
                f"Error: Could not extract video ID from URL: {video_url}",
                file=sys.stderr,
            )
            return None

        # According to the documentation, we must first instantiate the class.
        ytt_api = YouTubeTranscriptApi()

        # Then, call the .fetch() method on the instance to get the transcript data.
        # This returns a list-like 'FetchedTranscript' object.
        transcript_data = ytt_api.fetch(video_id)

        # The 'snippet' is an object, so we must use dot notation (snippet.text)
        # instead of dictionary-style square bracket notation (snippet['text']).
        text_segments = [snippet.text for snippet in transcript_data]

        # Join all text segments into a single, compact string
        full_transcript = " ".join(text_segments)

        return full_transcript

    except (TranscriptsDisabled, NoTranscriptFound) as e:
        # Catch specific, documented exceptions from the library
        print(f"Could not retrieve transcript for {video_url}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        # Catch any other unexpected errors
        print(
            f"An unexpected error occurred for video ID '{video_id}': {e}",
            file=sys.stderr,
        )
        return None


# --- Test Script Execution (No changes needed here) ---

if __name__ == "__main__":
    print("--- Starting YouTube Transcript Extraction Test ---\n")

    test_video_urls = [
        "https://www.youtube.com/watch?v=9pVbqwnmSuM",  # Double Down News
        "https://www.youtube.com/watch?v=sVhU_q1ZYjQ",  # Second Thought
        "https://youtu.be/GldhNwj80K0",  # Breakthrough News (Short URL)
        "https://www.youtube.com/watch?v=non_existent_video_id",  # Example of a video that will fail
    ]

    for i, url in enumerate(test_video_urls):
        print(f"--- Test Case {i + 1}: Processing URL: {url} ---")

        transcript = get_youtube_transcript(url)

        if transcript:
            print("\n>>> EXTRACTED TRANSCRIPT (COMPACT):")
            print(transcript)
        else:
            print("\n>>> FAILED to retrieve transcript for this video.")

        print("\n" + "=" * 70 + "\n")

    print("--- Test Complete ---")
