# YouTube Transcript Extractor (Tactiq.io)

This Python script leverages Selenium to automate the process of extracting YouTube video transcripts from the Tactiq.io YouTube Transcript Generator. It's designed to run in a headless browser (Firefox) and automatically removes timestamps from the extracted transcript, providing a clean, continuous text output.

## Table of Contents

1.  [Overview](#overview)
2.  [Features](#features)
3.  [Prerequisites](#prerequisites)
4.  [Installation](#installation)
5.  [Geckodriver Setup](#geckodriver-setup)
6.  [Usage](#usage)
7.  [Function Reference](#function-reference)
    *   [`get_youtube_transcript_from_tactiq(youtube_video_url: str) -> str`](#get_youtube_transcript_from_tactiqyoutube_video_url-str---str)
8.  [Example](#example)
9.  [Troubleshooting](#troubleshooting)

## Overview

The script automates the following steps:
1.  Navigates to `https://tactiq.io/tools/youtube-transcript`.
2.  Inputs a given YouTube video URL into the designated field.
3.  Clicks the "Get Video Transcript" button.
4.  Waits for the transcript page to load.
5.  Extracts the raw transcript text.
6.  Removes all timestamps (e.g., `00:00:00.000`) and associated whitespace from the transcript.
7.  Returns the cleaned transcript as a string.

## Features

*   **Automated Transcript Extraction:** Fetches transcripts directly from Tactiq.io.
*   **Headless Execution:** Runs in the background using Firefox without opening a visible browser window.
*   **Timestamp Removal:** Automatically cleans the transcript by removing timestamp markers.
*   **Robustness:** Uses explicit waits to handle dynamic web content loading.
*   **Error Handling:** Includes `try-except-finally` blocks for graceful error management and browser cleanup.

## Prerequisites

Before running this script, ensure you have the following installed:

*   **Python 3.x:** Download and install from [python.org](https://www.python.org/downloads/).
*   **Mozilla Firefox Browser:** The script uses Firefox as its browser.
*   **geckodriver:** The WebDriver for Firefox. See [Geckodriver Setup](#geckodriver-setup) for installation instructions.

## Installation

1.  **Install Selenium:**
    Open your terminal or command prompt and install the Selenium library using pip:
    ```bash
    pip install selenium
    ```

## Geckodriver Setup

`geckodriver` is essential for Selenium to control Firefox.

1.  **Download geckodriver:**
    Visit the [geckodriver releases page on GitHub](https://github.com/mozilla/geckodriver/releases). Download the appropriate version for your operating system (e.g., `geckodriver-vX.Y.Z-win64.zip` for Windows, `geckodriver-vX.Y.Z-linux64.tar.gz` for Linux, `geckodriver-vX.Y.Z-macos.tar.gz` for macOS).

2.  **Extract geckodriver:**
    Unzip or untar the downloaded file. You will find an executable file named `geckodriver` (or `geckodriver.exe` on Windows).

3.  **Add geckodriver to your PATH:**
    For the script to find `geckodriver` automatically, its location must be in your system's PATH environment variable.
    *   **Windows:**
        *   Move `geckodriver.exe` to a directory that's already in your PATH (e.g., `C:\Windows`, or a custom directory you add to PATH).
        *   Alternatively, add the directory where you placed `geckodriver.exe` to your system's PATH variable.
    *   **macOS/Linux:**
        *   Move `geckodriver` to `/usr/local/bin` (or another directory in your PATH, like `/usr/bin`):
            ```bash
            sudo mv /path/to/geckodriver /usr/local/bin/
            sudo chmod +x /usr/local/bin/geckodriver
            ```
        *   Verify installation by running `geckodriver --version` in your terminal.

    *If you cannot add `geckodriver` to your PATH*, you will need to specify its path directly in the script during WebDriver initialization:
    ```python
    # Example for specifying executable_path
    from selenium.webdriver.firefox.service import Service
    service = Service(executable_path='/path/to/your/geckodriver')
    driver = webdriver.Firefox(service=service, options=options)
    ```

## Usage

1.  **Save the Script:**
    Save the provided Python code as a `.py` file (e.g., `tactiq_transcript_extractor.py`).

2.  **Run the Script:**
    Open your terminal or command prompt, navigate to the directory where you saved the script, and run it:
    ```bash
    python tactiq_transcript_extractor.py
    ```
    The script will print progress messages to the console and then display the extracted transcript (truncated for brevity) and its total length.

3.  **Modify the YouTube URL:**
    To get a transcript for a different YouTube video, change the `test_youtube_url` variable in the `if __name__ == "__main__":` block:
    ```python
    test_youtube_url = "YOUR_YOUTUBE_VIDEO_URL_HERE"
    ```

## Function Reference

### `get_youtube_transcript_from_tactiq(youtube_video_url: str) -> str`

Extracts the YouTube video transcript from Tactiq.io, removing timestamps.

*   **Parameters:**
    *   `youtube_video_url` (`str`): The full URL of the YouTube video for which you want to retrieve the transcript.

*   **Returns:**
    *   `str`: The cleaned transcript text of the YouTube video, with all timestamps removed.

*   **Raises:**
    *   `Exception`: If any error occurs during the Selenium automation process, such as:
        *   `TimeoutException`: An element was not found or a page did not load within the specified timeout.
        *   `WebDriverException`: A general error with the Selenium WebDriver (e.g., `geckodriver` not found, browser crash).
        *   Any other unexpected error during execution.

*   **Internal Logic:**
    1.  Initializes a headless Firefox WebDriver instance.
    2.  Navigates to the Tactiq.io YouTube transcript generator page.
    3.  Locates the input field with `id="yt-2"` and enters the provided `youtube_video_url`.
    4.  Locates the button with `value="Get Video Transcript"` and clicks it.
    5.  Waits for the URL to change, indicating the transcript results page has loaded.
    6.  Locates the transcript container element with `id="transcript"`.
    7.  Waits until the transcript container is not empty, ensuring the text has loaded.
    8.  Extracts the raw text content.
    9.  Uses a regular expression (`r"\d{2}:\d{2}:\d{2}\.\d{3}\s*"`) to find and remove all patterns matching `HH:MM:SS.mmm` followed by any whitespace (including newlines).
    10. Returns the cleaned transcript.
    11. Ensures the WebDriver is quit in a `finally` block to clean up browser processes.

## Example

```python
# Example Usage (from the script's __main__ block)
if __name__ == "__main__":
    test_youtube_url = "https://www.youtube.com/watch?v=sVhU_q1ZYjQ"

    print(f"Attempting to extract transcript for: {test_youtube_url} using Tactiq.io with Firefox")
    try:
        transcript = get_youtube_transcript_from_tactiq(test_youtube_url)

        print("\n--- Extracted Transcript (first 500 characters, no timestamps) ---")
        print(transcript[:500])

        print("\n--- Extracted Transcript (last 500 characters, no timestamps) ---")
        print(transcript[-500:])

        print(f"\nTotal cleaned transcript length: {len(transcript)} characters.")

        # Verification checks for specific content
        if transcript.startswith("[Music]\nAt some point...") and transcript.endswith(
            "models suck?\n[Music]"
        ):
            print("\nVerification successful: Transcript starts and ends as expected (without timestamps).")
        else:
            print(
                "\nWarning: Transcript start/end phrases do not exactly match the example (after timestamp removal)."
            )
            print(f"Actual start: '{transcript[:50]}'")
            print(f"Actual end: '{transcript[-50:]}'")

    except Exception as e:
        print(f"Error extracting transcript: {e}")
```

## Troubleshooting

*   **`selenium.common.exceptions.WebDriverException: Message: 'geckodriver' executable needs to be in PATH.`**
    *   This means `geckodriver` is not found. Ensure you've followed the [Geckodriver Setup](#geckodriver-setup) instructions correctly, especially adding it to your system's PATH.

*   **Browser/Driver Version Mismatch:**
    *   Sometimes, an older `geckodriver` might not be compatible with a newer Firefox browser, or vice-versa. If you encounter errors related to browser sessions not starting, try updating both Firefox and `geckodriver` to their latest stable versions.

*   **`selenium.common.exceptions.TimeoutException`:**
    *   This indicates that an element the script was waiting for did not appear within the specified timeout period (e.g., 10, 20, or 60 seconds). This could be due to slow internet connection, changes in the Tactiq.io website's structure, or temporary server issues. You might try increasing the `WebDriverWait` timeouts, but be aware that overly long waits can slow down the script.

*   **Website Changes:**
    *   Websites can change their HTML structure (element IDs, class names, XPATHs). If Tactiq.io updates its layout, the locators (`By.ID`, `By.XPATH`) used in the script (`yt-2`, `Get Video Transcript`, `transcript`) might become invalid, causing the script to fail. You would need to inspect the Tactiq.io page again using your browser's developer tools to find the new locators and update the script accordingly.