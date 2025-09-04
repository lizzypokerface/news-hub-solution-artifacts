import re
import time
from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser
from urllib.parse import urljoin

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

# BeautifulSoup for cleaning the HTML after Selenium gets it
from bs4 import BeautifulSoup

# LangChain and Ollama imports
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate


def _normalize_date(date_string):
    """
    Normalizes various date strings into a datetime object.
    Returns datetime_object or None if parsing fails.
    """
    now = datetime.now(timezone.utc)  # Use UTC for consistency

    # Handle relative dates first
    date_string_lower = date_string.lower()
    if "today" in date_string_lower:
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif "yesterday" in date_string_lower:
        return (now - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif "ago" in date_string_lower:
        try:
            parts = date_string_lower.split()
            if len(parts) >= 2 and parts[0].isdigit():
                value = int(parts[0])
                unit = parts[1]
                if "day" in unit:
                    return (now - timedelta(days=value)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                elif "week" in unit:
                    return (now - timedelta(weeks=value)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                elif "month" in unit:
                    # Approximation for months/years ago
                    return (now - timedelta(days=value * 30)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                elif "year" in unit:
                    return (now - timedelta(days=value * 365)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
        except Exception:
            pass  # Fall through to absolute date parsing
        # Handle absolute dates
    try:
        # dateutil.parser.parse is robust for many formats
        dt_obj = date_parser.parse(date_string)
        # Ensure timezone awareness if not already present
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=timezone.utc)
        return dt_obj
    except Exception as e:
        print(f"    -  Could not parse date string '{date_string}': {e}")
        return None


def _fetch_and_prepare_text_with_links(url):
    """
    Fetches HTML content using Selenium, extracts plain text,
    and appends all found unique, absolute links at the end.
    """
    options = Options()
    options.add_argument("--headless")  # Run in headless mode (no visible browser UI)
    options.add_argument("--disable-gpu")  # Recommended for headless on Windows/WSL
    options.add_argument(
        "--no-sandbox"
    )  # Bypass OS security model, required for some environments
    options.add_argument(
        "--disable-dev-shm-usage"
    )  # Overcome limited resource problems
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )  # Mimic a real user agent

    driver = None  # Initialize driver to None for proper cleanup
    try:
        driver = webdriver.Chrome(options=options)

        print(f"    -  Navigating to {url} with Selenium...")
        driver.get(url)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        html_content = driver.page_source
        soup = BeautifulSoup(html_content, "html.parser")

        # --- 1. Get clean plain text ---
        # Remove script and style tags before getting text
        for script_or_style in soup(["script", "style"]):
            script_or_style.extract()

        plain_text = soup.get_text()
        plain_text = re.sub(
            r"\n\s*\n", "\n", plain_text
        )  # Replace multiple newlines with a single one
        plain_text = "\n".join(
            [line.strip() for line in plain_text.splitlines()]
        )  # Remove leading/trailing whitespace
        plain_text = re.sub(
            r" +", " ", plain_text
        )  # Replace multiple spaces with a single space

        # --- 2. Extract all unique, absolute links ---
        extracted_urls = set()  # Use a set to store unique URLs
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]

            # Resolve relative URLs to absolute URLs
            absolute_href = urljoin(url, href)

            # Filter out common non-content links (e.g., mailto, javascript, empty fragment)
            if (
                absolute_href
                and not absolute_href.startswith(("mailto:", "javascript:", "#"))
                and absolute_href != url
            ):
                extracted_urls.add(absolute_href)

        # --- 3. Append links to the plain text ---
        if extracted_urls:
            # Sort for consistent output, though not strictly necessary for LLM
            sorted_urls = sorted(list(extracted_urls))
            plain_text += "\n\n--- ALL LINKS ---\n"
            plain_text += "\n".join(sorted_urls)

        return plain_text
    except TimeoutException:
        print(f"    -  Timeout while loading {url}. Content might not have loaded.")
        return None
    except WebDriverException as e:
        print(
            f"    -  Selenium WebDriver error for {url}: {e}. Ensure Chrome browser is installed and compatible ChromeDriver is available in PATH."
        )
        return None
    except Exception as e:
        print(f"    -  An unexpected error occurred for {url}: {e}")
        return None
    finally:
        if driver:
            driver.quit()  # Ensure browser is closed


def _extract_articles_with_llm(plain_text_with_links, llm_model="llama3.1"):
    """
    Uses an Ollama LLM to extract article titles, URLs, and raw dates from plain text
    that includes appended raw URLs.
    This function now simply returns the raw string response from the LLM.
    """
    llm = Ollama(
        model=llm_model, temperature=0.1
    )  # Low temperature for more predictable output

    # The prompt now explicitly tells the LLM about the appended raw URLs section
    extraction_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert web content extractor. Your task is to identify articles or posts from the provided text content.
        The text content contains the main body of the webpage, followed by a section titled "--- ALL LINKS ---" which lists all unique, absolute URLs found on the page, one per line.

        For each article, extract its title, its full URL, and its publication date string.
        The publication date can be in various formats (e.g., "2 days ago", "Yesterday", "September 1, 2023", "2023-09-01", "Published: 2023-08-10").

        **Crucially, when extracting the URL for an article, you MUST find it from the "--- ALL LINKS ---" section.** Match the title or context of the article to the most relevant URL provided in that section. Do NOT try to infer URLs directly from the main text or create them. If an article cannot be confidently matched to a URL in the list, do not include it.

        Return the results as a JSON array of objects. Each object must have 'title', 'url', and 'raw_date' fields.
        If no articles are found, return an empty JSON array [].
        Limit your extraction to the first 10 distinct articles you find.

        Example Output Format:
        [
          {{
            "title": "How to Use Ollama Locally",
            "url": "https://ollama.com/blog/local-ollama-guide",
            "raw_date": "2023-10-26"
          }},
          {{
            "title": "New Features in Llama 3.1",
            "url": "https://ollama.com/blog/llama3.1-features",
            "raw_date": "1 day ago"
          }}
        ]
        """,
            ),
            (
                "user",
                "Extract article details from this content:\n\nContent:\n{plain_text_with_links}",
            ),
        ]
    )

    # The chain now directly returns the LLM's string output, no parsing
    extraction_chain = extraction_prompt | llm

    try:
        # Invoke the chain and return the raw string response
        return extraction_chain.invoke({"plain_text_with_links": plain_text_with_links})
    except Exception as e:
        print(f"    -  Error during LLM extraction: {e}")
        return None  # Return None on error


# --- Main Function for Web Articles ---


def fetch_web_articles(source, llm_model="llama3.1"):
    """
    Fetches articles from a webpage using Selenium and Ollama LLM.
    Returns the raw string output from the LLM.
    """
    print(
        f"    -  Fetching and preparing text with links for {source['name']} ({source['url']})"
    )
    plain_text_with_links = _fetch_and_prepare_text_with_links(source["url"])

    if not plain_text_with_links:
        return None  # Return None if content fetching failed

    print(f"    -  Extracting articles from {source['name']} using LLM ({llm_model})")
    # This now returns the raw string from the LLM
    llm_raw_output = _extract_articles_with_llm(plain_text_with_links, llm_model)

    return llm_raw_output


# --- Main Execution Block (simplified for text file output) ---

if __name__ == "__main__":
    # Ensure Ollama is running and you have the model pulled (e.g., ollama pull llama3.1)
    OLLAMA_MODEL = "llama3.1"  # Or "mistral", "gemma3", etc.
    OUTPUT_FILENAME = "llm_extracted_articles.txt"

    # Define the web pages you want to fetch articles from
    web_sources_to_fetch = [
        {
            "name": "Think BRICs",
            "url": "https://thinkbrics.substack.com/archive",
        },
        {
            "name": "Progressive International",
            "url": "https://progressive.international",
        },
    ]

    print(f"Fetching web articles and saving raw LLM output to '{OUTPUT_FILENAME}'...")

    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as outfile:
        for web_source in web_sources_to_fetch:
            print(
                f"\nProcessing web source: {web_source['name']} ({web_source['url']})"
            )

            # fetch_web_articles now returns the raw LLM string
            llm_output = fetch_web_articles(web_source, llm_model=OLLAMA_MODEL)

            outfile.write(f"Source({web_source['url']}):\n")
            if llm_output:
                outfile.write(llm_output)
            else:
                outfile.write("No LLM output or an error occurred.\n")
            outfile.write("\n---\n\n")  # Separator between sources

            time.sleep(2)  # Be polite and wait between requests

    print(f"\nProcessing complete. Raw LLM outputs saved to '{OUTPUT_FILENAME}'.")
