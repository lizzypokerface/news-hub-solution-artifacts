# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options as FirefoxOptions # Import FirefoxOptions
from selenium.common.exceptions import TimeoutException, WebDriverException
import re # Import the regular expression module


def get_youtube_transcript_from_tactiq(youtube_video_url: str) -> str:
    """
    Navigates to Tactiq's YouTube transcript generator, enters a YouTube URL,
    clicks the button, waits for the transcript page to load, and extracts
    the full transcript text, removing timestamps.

    Args:
        youtube_video_url (str): The URL of the YouTube video to transcribe.

    Returns:
        str: The extracted transcript as a compact string, with timestamps removed.

    Raises:
        Exception: If the transcript fails to load or any other error occurs
                   during the Selenium automation.
    """
    tactiq_base_url = "https://tactiq.io/tools/youtube-transcript"

    # Configure Firefox options for headless browsing
    # Headless mode runs the browser without a visible UI, which is good for automation.
    options = FirefoxOptions() # Use FirefoxOptions
    options.add_argument("--headless")  # Run in headless mode (no visible browser UI)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
    ) # Mimic a real user agent for Firefox

    driver = None  # Initialize driver to None for proper cleanup
    try:
        # Initialize the Firefox WebDriver
        # Ensure you have geckodriver installed and accessible in your PATH.
        # If not, you might need to specify its path:
        # driver = webdriver.Firefox(executable_path='/path/to/geckodriver', options=options)
        driver = webdriver.Firefox(options=options) # Use Firefox WebDriver
        print(f"    - Navigating to {tactiq_base_url} with Selenium (Firefox)...")
        driver.get(tactiq_base_url)

        # 1. Locate and interact with the input field
        url_input_field = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, "yt-2"))
        )
        print(f"    - Entering YouTube URL: {youtube_video_url}")
        url_input_field.send_keys(youtube_video_url)

        # 2. Locate and click the "Get Video Transcript" button
        get_transcript_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//input[@value='Get Video Transcript']")
            )
        )
        print("    - Clicking 'Get Video Transcript' button...")
        get_transcript_button.click()

        # 3. Wait for the new page to load
        WebDriverWait(driver, 20).until(EC.url_contains("run/youtube_transcript"))
        print("    - New transcript page loaded.")

        # 4. Wait for the transcript content to become visible and extract it
        transcript_container = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "transcript"))
        )

        # Additionally, wait until the text content of this container is not empty
        WebDriverWait(driver, 10).until(
            lambda d: transcript_container.text.strip() != ""
        )

        # Extract the full text from the container
        raw_transcript_text = transcript_container.text
        print("    - Raw transcript content found.")

        # 5. Remove timestamps from the transcript
        # The regex matches "HH:MM:SS.mmm" followed by any whitespace (including newlines)
        # and replaces them with an empty string.
        timestamp_pattern = r"\d{2}:\d{2}:\d{2}\.\d{3}\s*"
        cleaned_transcript_text = re.sub(timestamp_pattern, "", raw_transcript_text)
        print("    - Timestamps removed from transcript.")

        return cleaned_transcript_text.strip()

    except TimeoutException as e:
        raise Exception(
            f"Timeout occurred while waiting for element or page to load on Tactiq: {e}"
        )
    except WebDriverException as e:
        raise Exception(
            f"Selenium WebDriver error during Tactiq transcript extraction: {e}"
        )
    except Exception as e:
        raise Exception(
            f"An unexpected error occurred during Tactiq transcript extraction: {e}"
        )
    finally:
        if driver:
            print("    - Quitting Selenium WebDriver.")
            driver.quit()


# Example Usage
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

        # Verify the start and end phrases as requested (adjusting for timestamp removal)
        # The expected start and end phrases should now *not* include timestamps.
        # Based on your example:
        # 00:00:00.540
        # [Music]
        # 00:00:05.759
        # At some point around the 60s, we stopped
        # ...
        # models suck?
        # [Music]
        # So, the start should be "[Music]\nAt some point..."
        # and the end should be "models suck?\n[Music]"
        # Note: The exact newline handling might vary slightly, but this is a good approximation.
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

            # print("="*20)
            # print(transcript)
            # print("=" * 20)

    except Exception as e:
        print(f"Error extracting transcript: {e}")
