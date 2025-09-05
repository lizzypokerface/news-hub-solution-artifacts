
---

# YouTube Transcript Extractor

A simple and efficient Python script to extract clean, compact, and timestamp-free transcripts from YouTube videos. This tool takes a standard YouTube video URL as input and outputs the full transcript as a single string, making it ideal for text analysis, data processing, or feeding into other applications.

## Features

-   **Extracts Full Transcripts**: Retrieves the complete transcript for any YouTube video that has one available (either manually created or auto-generated).
-   **Clean and Compact Output**: Removes all timestamps and metadata, joining the transcript segments into a single, readable paragraph.
-   **Multiple URL Formats**: Works with both standard (`youtube.com/watch?v=...`) and shortened (`youtu.be/...`) YouTube URLs.
-   **No Browser Required**: Uses the `youtube-transcript-api` library, which directly queries YouTube's internal API without needing a browser instance like Selenium.
-   **Robust Error Handling**: Gracefully handles cases where transcripts are disabled, not found, or the URL is invalid.
-   **Easy to Integrate**: The core logic is encapsulated in a single function that can be easily imported into other Python projects.

## Requirements

-   Python 3.8 or newer.
-   The `youtube-transcript-api` library.

## Setup

1.  **Save the Script**: Save the main code as a Python file named `extract_transcript.py`.

2.  **Install the Dependency**: Open your terminal or command prompt and install the required library using pip:
    ```bash
    pip install youtube-transcript-api
    ```

## How to Use

### 1. As a Standalone Script

You can run the script directly from your terminal to see it in action. The script includes a set of test URLs to demonstrate its functionality.

**Command:**

```bash
python extract_transcript.py
```

**Expected Output:**

```
--- Starting YouTube Transcript Extraction Test ---

--- Test Case 1: Processing URL: https://www.youtube.com/watch?v=9pVbqwnmSuM ---

>>> EXTRACTED TRANSCRIPT (COMPACT):
So I was the UN special reporter on the right to food for six years and I was in Gaza in November 2012 just after the Cast Lead operation by the Israeli Army against Gaza and I saw the destruction but I also saw the incredible resilience of the people there the fishermen the peasants the women the university people the students and so on and I wrote a devastating report to the Human Rights Council and to the general assembly about the situation there and the destruction of the food system in Gaza by the occupation power...

======================================================================

--- Test Case 2: Processing URL: https://www.youtube.com/watch?v=non_existent_video_id ---
Could not retrieve transcript for https://www.youtube.com/watch?v=non_existent_video_id: No transcript could be found for video id: non_existent_video_id. This may be because the video has no transcript, is private, or is unavailable.

>>> FAILED to retrieve transcript for this video.

======================================================================

--- Test Complete ---
```

### 2. Integrating into Your Own Project

The most powerful way to use this script is by importing the `get_youtube_transcript` function into your own applications.

1.  Ensure `extract_transcript.py` is in the same directory as your project file (or in a location accessible by Python's path).
2.  Import the function and call it with a YouTube URL.

**Example (`my_app.py`):**

```python
from extract_transcript import get_youtube_transcript

# The URL of the video you want to process
video_url = "https://www.youtube.com/watch?v=sVhU_q1ZYjQ"

print(f"Attempting to extract transcript from: {video_url}")

# Call the function to get the transcript
transcript = get_youtube_transcript(video_url)

# Process the result
if transcript:
    print("\n--- SUCCESS ---")
    # You can now save the transcript to a file, analyze it, etc.
    print(transcript[:300] + "...") # Print the first 300 characters
else:
    print("\n--- FAILURE ---")
    print("The transcript could not be retrieved.")

```

## Code Overview

### `get_youtube_transcript(video_url: str) -> str | None`

This is the core function of the script.

-   **Input**: It takes one argument, `video_url`, which is the string URL of the YouTube video.
-   **Process**:
    1.  It parses the URL to extract the unique `video_id`.
    2.  It uses an instance of `YouTubeTranscriptApi` to call the `.fetch()` method with the `video_id`.
    3.  It iterates through the list of `FetchedTranscriptSnippet` objects returned by the API.
    4.  It accesses the `.text` attribute of each snippet and collects them into a list.
    5.  It joins all text segments with a space to form a single, continuous string.
-   **Output**:
    -   On success, it returns the complete transcript as a single `str`.
    -   On failure (e.g., no transcript available, video is private), it prints an error message to the console and returns `None`.

## Error Handling

The script is designed to fail gracefully and provide informative messages in the following scenarios:

-   **`TranscriptsDisabled`**: Occurs if the owner of the video has explicitly disabled transcripts.
-   **`NoTranscriptFound`**: Occurs if no transcript (manual or auto-generated) exists for the video in any language.
-   **Invalid URL**: If the script cannot extract a valid video ID from the provided URL string.

In each of these cases, the function will return `None`, allowing your code to handle the failure appropriately.
