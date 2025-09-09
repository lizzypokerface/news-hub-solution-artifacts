# Content Summarization Script Documentation

## Table of Contents
1.  [Introduction](#introduction)
2.  [Features](#features)
3.  [Prerequisites](#prerequisites)
4.  [Installation](#installation)
5.  [Configuration](#configuration)
6.  [Usage](#usage)
7.  [Module Functions](#module-functions)
8.  [Output](#output)
9.  [Error Handling](#error-handling)

## 1. Introduction
This Python script is designed to automate the process of extracting content from various online sources (YouTube videos and general webpages) and generating journalistic summaries using the Poe API. It provides a robust solution for intelligence analysts or news reporters to quickly get detailed briefings from online documents.

## 2. Features
*   **YouTube Transcript Extraction:** Automatically fetches and cleans transcripts from YouTube video URLs.
*   **Webpage Text Extraction:** Extracts clean, readable text from any given webpage URL by stripping HTML tags.
*   **Poe API Integration:** Leverages the Poe API (specifically `openai` library compatible models like Claude-Sonnet-4) to generate detailed, journalistic summaries based on a predefined prompt.
*   **Manual Input Fallback:** If automatic content extraction fails (e.g., video transcript unavailable, webpage unreachable), the script prompts the user to manually paste the content for summarization.
*   **Markdown Output:** Saves each generated summary into a separate Markdown (`.md`) file for easy readability and sharing.
*   **Robust Error Handling:** Catches and reports errors during content fetching and API calls.

## 3. Prerequisites
Before running the script, ensure you have the following:
*   **Python 3.x:** The script is written in Python and requires a compatible version.
*   **Poe API Key:** You will need an API key from Poe. You can obtain one from [poe.com/api_keys](https://poe.com/api_keys).

## 4. Installation
1.  **Clone or Download the Script:** Get the `summarizer.py` file to your local machine.
2.  **Install Required Python Libraries:** Open your terminal or command prompt and run the following command:
    ```bash
    pip install requests beautifulsoup4 youtube-transcript-api openai
    ```
    *   `requests`: For making HTTP requests to fetch webpage content.
    *   `beautifulsoup4`: For parsing HTML and extracting text from webpages.
    *   `youtube-transcript-api`: For fetching YouTube video transcripts.
    *   `openai`: The official OpenAI Python client, used here to interact with the Poe API.

## 5. Configuration
The script requires your Poe API key to function.
1.  **Open the Script:** Locate the line `poe_api_key = "YOUR_POE_API_KEY"` in the `if __name__ == "__main__":` block.
2.  **Replace Placeholder:** Replace `"YOUR_POE_API_KEY"` with your actual API key obtained from Poe.
    ```python
    # Example:
    poe_api_key = "pk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
    ```
    **Security Note:** For production environments or sharing your code, it's highly recommended to load API keys from environment variables instead of hardcoding them in the script. You can uncomment and use `poe_api_key = os.getenv("POE_API_KEY")` and then set the `POE_API_KEY` environment variable before running the script.

## 6. Usage
To run the script, navigate to the directory where you saved `summarizer.py` in your terminal or command prompt and execute:

```bash
python summarizer.py
```

The script will then:
1.  **Process URLs:** Iterate through the predefined list of YouTube and webpage URLs.
2.  **Attempt Automatic Extraction:** For each URL, it will first try to automatically extract content (transcript for YouTube, text for webpages).
3.  **Prompt for Manual Input (if needed):**
    *   If automatic extraction fails, it will print an error message and then prompt you to manually paste the content.
    *   You can paste the raw text and press `Enter` twice to signal the end of your input.
    *   If you have no content to provide manually, simply press `Enter` twice without typing anything.
4.  **Generate Summary:** If content is available (either automatically extracted or manually provided), it will send this content to the Poe API for summarization.
5.  **Save Output:** The generated summary will be saved as a Markdown file in a `summaries` directory (created automatically if it doesn't exist).

### Example Interaction (Manual Input):
```
Processing URL 4/8: https://www.youtube.com/watch?v=nonexistentvideo123
Automatic content extraction failed for https://www.youtube.com/watch?v=nonexistentvideo123.
Please paste the content manually below (press Enter twice to finish, or just Enter if no content):
This is some manual text that I am providing.
It could be a transcript or an article.
I will press enter twice now.

Manual content received.
Generating summary with Poe API...
Summary generated successfully.
Summary saved to: summaries/summary_4_https___www_youtube_com_watch_v_nonexistentvideo123_truncated.md
```

## 7. Module Functions

The script is structured with the following key functions:

*   `get_youtube_transcript(video_url: str) -> str | None`:
    *   **Purpose:** Extracts the full, clean transcript from a YouTube video URL.
    *   **Returns:** The transcript as a single string, or `None` if extraction fails (e.g., no transcript, private video).

*   `extract_text_from_url(url: str) -> str | None`:
    *   **Purpose:** Fetches content from a URL, removes HTML tags using BeautifulSoup, and returns clean, compact text.
    *   **Returns:** The extracted text as a single string, or `None` if extraction fails (e.g., network error, invalid URL).

*   `get_summarizable_content(url: str) -> str | None`:
    *   **Purpose:** Acts as the primary content fetching function. It determines if the URL is YouTube or a general webpage and calls the appropriate extractor.
    *   **Returns:** The extracted content as a string, or `None` if neither automatic method succeeds.

*   `summarize_content_with_poe(content: str, poe_api_key: str, model: str = "Claude-Sonnet-4") -> str`:
    *   **Purpose:** Generates a journalistic summary of the provided text content using the Poe API. It constructs the specific prompt required by the task.
    *   **Parameters:**
        *   `content`: The text to be summarized.
        *   `poe_api_key`: Your Poe API key.
        *   `model`: The Poe model to use (default: "Claude-Sonnet-4").
    *   **Returns:** The generated summary as a string.
    *   **Raises:** An `Exception` if the API call fails.

*   `sanitize_filename(url: str) -> str`:
    *   **Purpose:** Helper function to convert a URL into a safe and descriptive filename for saving summaries.

## 8. Output
Summaries are saved in a newly created directory named `summaries/` in the same location as the script. Each summary file is named using a sequential number and a sanitized version of the original URL, with a `.md` extension (e.g., `summary_1_https___www_youtube_com_watch_v_zsaWFKKhChA.md`).

## 9. Error Handling
The script includes error handling for:
*   **Content Extraction Failures:** If a URL cannot be reached or its content cannot be extracted automatically, the script will prompt for manual input.
*   **Poe API Errors:** If there's an issue communicating with the Poe API (e.g., invalid API key, rate limits, model errors), an exception will be caught and reported to the console.
*   **Missing API Key:** The script will exit if the `poe_api_key` is not configured.

For any unhandled exceptions, a general error message will be displayed, indicating the URL that caused the issue.