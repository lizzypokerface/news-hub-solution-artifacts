# content_extractor.py

import logging
import re
import os  # Keep os for potential future use or other environment variables
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Removed: from googleapiclient.discovery import build
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    NoTranscriptFound,
    TranscriptsDisabled,
)

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("ContentExtractor")


# --- Helper function for Selenium WebDriver setup ---
def _get_firefox_driver():
    """Initializes and returns a headless Firefox WebDriver."""
    options = FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
    )
    try:
        driver = webdriver.Firefox(options=options)
        return driver
    except WebDriverException as e:
        logger.error(
            f"Failed to initialize Firefox WebDriver. Ensure geckodriver is in your PATH. Error: {e}"
        )
        raise


# --- 1. Extract Transcript for YouTube Links (YouTube Transcript API) ---
def extract_transcript_youtube_api(youtube_url: str) -> str:
    """
    Extracts the transcript of a YouTube video using the youtube-transcript-api library.
    This method does NOT require a YouTube Data API key.

    Args:
        youtube_url (str): The URL of the YouTube video.

    Returns:
        str: The cleaned transcript text.

    Raises:
        ValueError: If the YouTube URL is invalid or video ID cannot be extracted.
        Exception: For transcript not found, disabled transcripts, or other issues.
    """
    logger.info(
        f"Attempting to extract YouTube transcript via youtube-transcript-api for: {youtube_url}"
    )

    try:
        # Extract video ID from URL
        parsed_url = urlparse(youtube_url)
        if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
            if parsed_url.path == "/watch":
                video_id = parse_qs(parsed_url.query).get("v")
                if video_id:
                    video_id = video_id[0]
                else:
                    raise ValueError(
                        f"Could not extract video ID from URL: {youtube_url}"
                    )
            elif parsed_url.path.startswith("/youtu.be/"):
                video_id = parsed_url.path.split("/")[-1]
            else:
                raise ValueError(f"Unsupported YouTube URL format: {youtube_url}")
        else:
            raise ValueError(f"Invalid YouTube URL: {youtube_url}")

        if not video_id:
            raise ValueError(f"Could not determine video ID from URL: {youtube_url}")

        # Use youtube_transcript_api to fetch transcript
        ytt_api = YouTubeTranscriptApi()
        transcript_data = ytt_api.fetch(video_id)
        transcript_text = [snippet.text for snippet in transcript_data]
        logger.info(
            f"Successfully extracted transcript for video ID: {video_id} using youtube-transcript-api."
        )
        return " ".join(transcript_text)
    
    except NoTranscriptFound:
        logger.warning(
            f"No transcript found for video: {youtube_url}. Returning empty string."
        )
        return ""
    except TranscriptsDisabled:
        logger.warning(
            f"Transcripts are disabled for video: {youtube_url}. Returning empty string."
        )
        return ""
    except ValueError as e:
        logger.error(f"Invalid YouTube URL or video ID: {e}")
        raise
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while fetching YouTube transcript via youtube-transcript-api for {youtube_url}: {e}"
        )
        raise


# --- 2. Extract Transcript for YouTube (Tactiq) ---
def extract_transcript_youtube_tactiq(youtube_url: str) -> str:
    """
    Extracts the transcript of a YouTube video using Tactiq.io via Selenium.
    Timestamps are automatically removed from the output.

    Args:
        youtube_url (str): The URL of the YouTube video.

    Returns:
        str: The cleaned transcript text.

    Raises:
        Exception: If the transcript fails to load or any other error occurs
                   during the Selenium automation.
    """
    logger.info(
        f"Attempting to extract YouTube transcript via Tactiq.io for: {youtube_url}"
    )
    tactiq_base_url = "https://tactiq.io/tools/youtube-transcript"
    driver = None

    try:
        driver = _get_firefox_driver()
        driver.get(tactiq_base_url)
        logger.info(f"Navigated to Tactiq.io: {tactiq_base_url}")

        # Locate and interact with the input field
        url_input_field = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, "yt-2"))
        )
        url_input_field.send_keys(youtube_url)
        logger.info(f"Entered YouTube URL: {youtube_url}")

        # Locate and click the "Get Video Transcript" button
        get_transcript_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//input[@value='Get Video Transcript']")
            )
        )
        get_transcript_button.click()
        logger.info("Clicked 'Get Video Transcript' button.")

        # Wait for the new page to load
        WebDriverWait(driver, 20).until(EC.url_contains("run/youtube_transcript"))
        logger.info("New transcript page loaded on Tactiq.io.")

        # Wait for the transcript content to become visible and extract it
        transcript_container = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "transcript"))
        )
        WebDriverWait(driver, 10).until(
            lambda d: transcript_container.text.strip() != ""
        )

        raw_transcript_text = transcript_container.text
        logger.info("Raw transcript content found from Tactiq.io.")

        # Remove timestamps using regex
        timestamp_pattern = r"\d{2}:\d{2}:\d{2}\.\d{3}\s*"
        cleaned_transcript_text = re.sub(timestamp_pattern, "", raw_transcript_text)
        logger.info("Timestamps removed from Tactiq.io transcript.")

        return cleaned_transcript_text.strip()

    except TimeoutException as e:
        logger.error(
            f"Timeout occurred while waiting for element or page to load on Tactiq.io for {youtube_url}: {e}"
        )
        raise Exception(f"Timeout on Tactiq.io: {e}")
    except WebDriverException as e:
        logger.error(
            f"Selenium WebDriver error during Tactiq.io transcript extraction for {youtube_url}: {e}"
        )
        raise Exception(f"Selenium WebDriver error: {e}")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during Tactiq.io transcript extraction for {youtube_url}: {e}"
        )
        raise Exception(f"Unexpected error: {e}")
    finally:
        if driver:
            driver.quit()
            logger.info("Firefox WebDriver quit.")


# --- Helper function for cleaning HTML content ---
def _clean_html_content(html_content: str) -> str:
    """
    Cleans HTML content by extracting visible text and removing extra whitespace.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style elements
    for script_or_style in soup(
        ["script", "style", "noscript", "header", "footer", "nav", "aside"]
    ):
        script_or_style.decompose()

    # Get text
    text = soup.get_text(separator=" ", strip=True)

    # Remove multiple spaces and newlines
    text = re.sub(r"\s+", " ", text)
    text = text.replace("\n", " ").replace("\r", "")

    return text.strip()


# --- 3. Extract Content for Webpage (BeautifulSoup) ---
def extract_content_webpage_bs4(webpage_url: str) -> str:
    """
    Extracts cleaned text content from a static webpage using requests and BeautifulSoup.

    Args:
        webpage_url (str): The URL of the webpage.

    Returns:
        str: The cleaned text content of the webpage.

    Raises:
        requests.exceptions.RequestException: For network-related errors.
        Exception: For other parsing or unexpected errors.
    """
    logger.info(
        f"Attempting to extract content from webpage via requests/BeautifulSoup for: {webpage_url}"
    )
    try:
        response = requests.get(webpage_url, timeout=15)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        html_content = response.text
        logger.info(f"Successfully fetched HTML content from {webpage_url}.")

        cleaned_text = _clean_html_content(html_content)
        logger.info(f"Cleaned HTML content for {webpage_url}.")
        return cleaned_text

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while fetching {webpage_url}: {e}")
        raise
    except Exception as e:
        logger.error(
            f"An error occurred while parsing {webpage_url} with BeautifulSoup: {e}"
        )
        raise


# --- 4. Extract Content for Webpage (Selenium + BeautifulSoup) ---
def extract_content_webpage_selenium_bs4(webpage_url: str) -> str:
    """
    Extracts cleaned text content from a dynamic webpage using Selenium (Firefox)
    to render content, then BeautifulSoup for parsing.

    Args:
        webpage_url (str): The URL of the webpage.

    Returns:
        str: The cleaned text content of the webpage.

    Raises:
        Exception: For Selenium or parsing errors.
    """
    logger.info(
        f"Attempting to extract content from dynamic webpage via Selenium/BeautifulSoup for: {webpage_url}"
    )
    driver = None
    try:
        driver = _get_firefox_driver()
        driver.get(webpage_url)
        logger.info(f"Navigated to webpage: {webpage_url} with Selenium.")

        # Wait for some content to load, or for a specific element if known
        # This is a generic wait, you might need to adjust for specific pages
        WebDriverWait(driver, 20).until(
            lambda d: d.find_element(By.TAG_NAME, "body").text.strip() != ""
        )
        logger.info("Page content appears to have loaded.")

        html_content = driver.page_source
        logger.info(f"Fetched page source from {webpage_url}.")

        cleaned_text = _clean_html_content(html_content)
        logger.info(f"Cleaned HTML content for {webpage_url}.")
        return cleaned_text

    except TimeoutException as e:
        logger.error(
            f"Timeout occurred while waiting for webpage content to load for {webpage_url}: {e}"
        )
        raise Exception(f"Timeout on dynamic webpage: {e}")
    except WebDriverException as e:
        logger.error(
            f"Selenium WebDriver error during dynamic webpage extraction for {webpage_url}: {e}"
        )
        raise Exception(f"Selenium WebDriver error: {e}")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during dynamic webpage extraction for {webpage_url}: {e}"
        )
        raise Exception(f"Unexpected error: {e}")
    finally:
        if driver:
            driver.quit()
            logger.info("Firefox WebDriver quit.")


# --- Example Usage (for testing the module) ---
# if __name__ == "__main__":
#     # --- YouTube API Example ---
#     print("\n--- Testing YouTube Transcript API Extraction (No Key Needed) ---")
#     youtube_test_url_api = "https://www.youtube.com/watch?v=QIFmJ1Pg73w"  # Example: A video with transcript
#     try:
#         api_transcript = extract_transcript_youtube_api(youtube_test_url_api)
#         print(f"\nYouTube Transcript API (first 500 chars):\n{api_transcript[:500]}...")
#         print(f"Total length: {len(api_transcript)} chars.")
#     except Exception as e:
#         print(f"Error with YouTube Transcript API: {e}")

#     # --- YouTube Tactiq Example ---
#     print("\n--- Testing YouTube Tactiq Transcript Extraction ---")
#     youtube_test_url_tactiq = "https://www.youtube.com/watch?v=QIFmJ1Pg73w"  # Example from previous discussion
#     try:
#         tactiq_transcript = extract_transcript_youtube_tactiq(youtube_test_url_tactiq)
#         print(f"\nTactiq Transcript (first 500 chars):\n{tactiq_transcript[:500]}...")
#         print(f"Total length: {len(tactiq_transcript)} chars.")
#     except Exception as e:
#         print(f"Error with Tactiq: {e}")

#     # --- Static Webpage (BeautifulSoup) Example ---
#     print("\n--- Testing Static Webpage Extraction (BeautifulSoup) ---")
#     static_webpage_url = "https://thinkbrics.substack.com/p/visions-about-the-brics-electricity"  # Pride and Prejudice
#     try:
#         bs4_content = extract_content_webpage_bs4(static_webpage_url)
#         print(f"\nBeautifulSoup Content (first 500 chars):\n{bs4_content[:500]}...")
#         print(f"Total length: {len(bs4_content)} chars.")
#     except Exception as e:
#         print(f"Error with BeautifulSoup: {e}")

#     # --- Dynamic Webpage (Selenium + BeautifulSoup) Example ---
#     print("\n--- Testing Dynamic Webpage Extraction (Selenium + BeautifulSoup) ---")
#     # A simple dynamic page (e.g., one that loads content via JS)
#     # Note: Many modern sites use complex JS, so this might need specific waits for complex cases.
#     dynamic_webpage_url = (
#         "https://thinkbrics.substack.com/p/visions-about-the-brics-electricity"
#     )
#     try:
#         selenium_bs4_content = extract_content_webpage_selenium_bs4(dynamic_webpage_url)
#         print(
#             f"\nSelenium + BeautifulSoup Content (first 500 chars):\n{selenium_bs4_content[:500]}..."
#         )
#         print(f"Total length: {len(selenium_bs4_content)} chars.")
#     except Exception as e:
#         print(f"Error with Selenium + BeautifulSoup: {e}")
