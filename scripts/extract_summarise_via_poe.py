import sys
import os
from urllib.parse import urlparse, parse_qs
import re # Import re for sanitizing filenames

import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Import the openai library for Poe API interaction
import openai

# --- Existing Content Extraction Functions ---

def get_youtube_transcript(video_url: str) -> str | None:
    """
    Extracts the full, clean transcript from a YouTube video URL.
    Returns the transcript as a single string, or None if extraction fails.
    """
    video_id = None
    try:
        parsed_url = urlparse(video_url)
        if "youtube.com" in parsed_url.hostname:
            video_id = parse_qs(parsed_url.query).get("v", [None])[0]
        elif "youtu.be" in parsed_url.hostname:
            video_id = parsed_url.path.lstrip("/")

        if not video_id:
            return None

        ytt_api = YouTubeTranscriptApi()
        transcript_data = ytt_api.fetch(video_id)
        text_segments = [snippet['text'] for snippet in transcript_data]
        return " ".join(text_segments)

    except (TranscriptsDisabled, NoTranscriptFound) as e:
        # Transcript is disabled or not found for the video
        return None
    except Exception as e:
        # Catch any other unexpected errors during transcript fetching
        return None

def extract_text_from_url(url: str) -> str | None:
    """
    Fetches content from a URL, removes HTML tags using BeautifulSoup,
    and returns clean, compact text.
    Returns the extracted text as a single string, or None if extraction fails.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        compact_text = soup.get_text(separator=" ", strip=True)
        return compact_text

    except requests.RequestException as e:
        # Handle request-specific exceptions (e.g., connection errors, timeouts, HTTP errors)
        return None
    except Exception as e:
        # Catch any other unexpected errors during text extraction
        return None

def get_summarizable_content(url: str) -> str | None: # Changed return type to allow None
    """
    Fetches content from a given URL, either a YouTube transcript or webpage text.

    Args:
        url (str): The URL of the content to fetch.

    Returns:
        str | None: The extracted content (transcript or text) as a single string,
                    or None if content cannot be fetched.
    """
    parsed_url = urlparse(url)
    is_youtube = False

    if parsed_url.hostname in ("www.youtube.com", "youtube.com", "youtu.be"):
        is_youtube = True

    content = None
    if is_youtube:
        content = get_youtube_transcript(url)
    else:
        content = extract_text_from_url(url)

    return content

# --- New Summarization Function ---

def summarize_content_with_poe(content: str, poe_api_key: str, model: str = "Gemini-2.5-Flash") -> str:
    """
    Generates a summary of the provided content using the Poe API.

    Args:
        content (str): The text content to be summarized.
        poe_api_key (str): Your Poe API key.
        model (str): The Poe model to use for summarization (e.g., "Claude-Sonnet-4", "Grok-4").

    Returns:
        str: The generated summary.

    Raises:
        Exception: If the Poe API call fails or returns an error.
    """
    client = openai.OpenAI(
        api_key=poe_api_key,
        base_url="https://api.poe.com/v1",
    )

    # The prompt provided by the user
    prompt = f"""
## Prompt Start

**Role:** You are an intelligence analyst and news reporter.

**Task:** Your task is to create a detailed, journalistic summary of the provided document. The summary should be written as a news report or an intelligence briefing, designed to inform a reader about the current situation, key claims, and important figures involved.

**Audience:** The summary is for a well-informed reader who needs a quick but thorough understanding of the key events, claims, and dynamics discussed in the text.

**Key Requirements for Your Summary:**

1.  **Journalistic Style:** Begin the summary with a dateline (e.g., "**City, Country --**") and write in a clear, objective, and professional news style.
2.  **Strict Attribution:** Attribute all claims, opinions, and predictions directly to the speaker(s) mentioned in the text. Use phrases like "According to [Speaker's Name]," "[Speaker] stated that," or "[Speaker] claims." Never present an opinion from the text as an established fact.
3.  **Extract Key Facts:** Identify and include all critical factual information:
    -   **People:** Full names and their titles/roles (e.g., "Seyed Mohammad Marandi, a professor at Tehran University").
    -   **Organizations:** Names of government bodies, agencies, or groups (e.g., "IAEA," "Supreme National Security Council").
    -   **Locations:** Important cities, countries, or regions mentioned (e.g., "Gaza," "Tehran," "Beijing").
    -   **Specific Events:** Mention key events discussed, such as "US and Israeli strikes," "a military parade in Beijing," or "sanctions."
4.  **Summarize the Core Thesis:** Clearly state the central argument of the speaker. What is the main point they are trying to convey?
5.  **Include Supporting Evidence:** Mention the key pieces of evidence or examples the speaker uses to support their main points.
6.  **Capture Critical Statements:** Incorporate direct quotes or precise paraphrases of the most important statements, especially any warnings, policy shifts, or significant declarations.
7.  **Logical Structure:**
    -   Start with the most important information (the lead).
    -   Follow with supporting details, context, and evidence.
    -   Conclude with any forward-looking statements or final assessments made by the speaker.
8.  **Word Count:** Aim for a detailed summary of approximately 150-250 words. Omit timestamps.

---

### **Examples to Guide You:**

Let's use the provided transcript about Professor Marandi as our source text.

**Bad Example (What to AVOID):**

> "Professor Marandi talked about the situation in the Middle East. He said Iran wasn't really hurt by the attacks and that they are being ambiguous about their nuclear program now. He thinks Iran is stronger and has better friends, so they are more prepared for a war."
> -   **Why it's bad:** This summary is too generic. It lacks names, titles, specific evidence, attribution, and the professional tone of a news report.

**Good Example (What to AIM FOR):**

> "Tehran, Iran -- According to Seyed Mohammad Marandi, a professor at Tehran University, recent US and Israeli strikes failed to damage Iran's nuclear program, prompting Tehran to adopt a policy of 'strategic ambiguity.' Marandi claims key facilities are deep underground and that Iran retains a strong industrial base for producing advanced centrifuges. A major consequence, he stated, is Iran's decision to cease most cooperation with the IAEA. He highlighted a warning from Dr. Jani, head of Iran's Supreme National Security Council, that Iran's 'nuclear posture will change' if its existence is threatened. Marandi concluded that Iran's geopolitical position is strengthening through deeper ties with China and Russia, making it more prepared for any future conflict."
> -   **Why it's good:** It uses a dateline, attributes every claim, includes names and titles (Marandi, Dr. Jani), mentions key organizations (IAEA), quotes a critical warning, and follows a logical news structure.

---

**Now, using the rules and examples above, process the following document:**

`{content}`
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt.format(content=content)}],
            stream=False # Set to False to get the full response at once
        )
        # The response structure for non-streaming is different, access content directly
        summary = response.choices[0].message.content
        return summary
    except openai.APIError as e:
        raise Exception(f"Poe API Error: {e}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred during Poe summarization: {e}")

def sanitize_filename(url: str) -> str:
    """
    Sanitizes a URL to create a valid and somewhat descriptive filename.
    """
    # Replace non-alphanumeric characters with underscores, keep dots for extensions
    filename = re.sub(r'[^\w\s.-]', '_', url)
    # Replace spaces with underscores
    filename = re.sub(r'\s+', '_', filename)
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    # Trim to a reasonable length to avoid excessively long filenames
    if len(filename) > 100:
        filename = filename[:100] + "_truncated"
    return filename

# --- Main Execution Block ---

if __name__ == "__main__":
    # IMPORTANT: Replace "YOUR_POE_API_KEY" with your actual Poe API key
    # It's recommended to load this from an environment variable for security.
    poe_api_key = os.getenv("POE_API_KEY")
    #poe_api_key = "YOUR_POE_API_KEY" # Replace this!

    if poe_api_key == "YOUR_POE_API_KEY" or not poe_api_key:
        print("Error: Please set your POE_API_KEY in the script or as an environment variable.")
        sys.exit(1)

    # Example YouTube URLs
    youtube_urls = [
        "https://www.youtube.com/watch?v=zsaWFKKhChA",
        "https://www.youtube.com/watch?v=QIFmJ1Pg73w",
        "https://www.youtube.com/watch?v=UMgkvvu_pnU",
        "https://www.youtube.com/watch?v=nonexistentvideo123" # Example of a non-existent or transcript-disabled video
    ]

    # Example Webpage URLs
    webpage_urls = [
        "https://thinkbrics.substack.com/p/visions-about-the-brics-electricity",
        "https://www.tarikcyrilamar.com/p/germanys-annalena-baerbock-the-debility-c3a",
        "https://progressive.international/wire/2025-09-05-repatriated-venezuelans-denounce-abuse-and-torture-in-el-salvadors-cecot-mega-prison/en",
        "https://www.nonexistentwebsite12345.com" # Example of a non-existent website
    ]

    all_urls = youtube_urls + webpage_urls
    output_dir = "summaries"
    os.makedirs(output_dir, exist_ok=True) # Create output directory if it doesn't exist

    print("--- Starting Content Extraction and Summarization ---")

    for i, url in enumerate(all_urls):
        print(f"\nProcessing URL {i+1}/{len(all_urls)}: {url}")
        summary_filename = os.path.join(output_dir, f"summary_{i+1}_{sanitize_filename(url)}.md")
        content_to_summarize = None

        try:
            # Step 1: Attempt to get summarizable content automatically
            content_to_summarize = get_summarizable_content(url)
            if content_to_summarize:
                print(f"Content extracted automatically (first 100 chars): {content_to_summarize[:100]}...")
            else:
                print(f"Automatic content extraction failed for {url}.")
                # Fallback to manual input
                print("Please paste the content manually below (press Enter twice to finish, or just Enter if no content):")
                manual_content_lines = []
                while True:
                    line = input()
                    if not line and (not manual_content_lines or manual_content_lines[-1] == ""):
                        # If current line is empty AND (it's the first line OR the previous line was also empty)
                        break
                    manual_content_lines.append(line)
                
                manual_input_text = "\n".join(manual_content_lines).strip()
                
                if manual_input_text:
                    content_to_summarize = manual_input_text
                    print("Manual content received.")
                else:
                    print("No manual content provided. Skipping summarization for this URL.")

            # Step 2: If content is available (either auto-extracted or manual), summarize it
            if content_to_summarize:
                print("Generating summary with Poe API...")
                summary = summarize_content_with_poe(content_to_summarize, poe_api_key)
                print("Summary generated successfully.")

                # Step 3: Save the summary to a Markdown file
                with open(summary_filename, "w", encoding="utf-8") as f:
                    f.write(summary)
                print(f"Summary saved to: {summary_filename}")
            else:
                print(f"No content available for summarization for URL: {url}. No summary file created.")

        except Exception as e:
            print(f"An error occurred during processing for {url}: {e}")

    print("\n--- Processing Complete ---")