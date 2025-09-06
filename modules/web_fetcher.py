import re
import time
import json
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

# Logging imports
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more detailed output
    format="%(asctime)s - %(levelname)s - %(message)s",
)


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
        logging.error(f"Could not parse date string '{date_string}': {e}")
        return None


def _fetch_and_prepare_text_with_links(url):
    """
    Fetches HTML content using Selenium, extracts plain text,
    and appends all found unique, absolute links at the end.
    """
    options = Options()
    options.add_argument("--headless")  # Run in headless mode (no visible browser UI)
    options.add_argument("--disable-gpu")  # Recommended for headless on Windows/WSL
    options.add_argument("--no-sandbox")  # Bypass OS security model
    options.add_argument(
        "--disable-dev-shm-usage"
    )  # Overcome limited resource problems
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )  # Mimic a real user agent

    driver = None  # Initialize driver to None for proper cleanup
    try:
        driver = webdriver.Chrome(options=options)

        logging.info(f"Navigating to {url} with Selenium...")
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
        logging.warning(f"Timeout while loading {url}. Content might not have loaded.")
        return None
    except WebDriverException as e:
        logging.error(
            f"Selenium WebDriver error for {url}: {e}. Ensure Chrome browser is installed and compatible ChromeDriver is available in PATH."
        )
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred for {url}: {e}")
        return None
    finally:
        if driver:
            driver.quit()  # Ensure browser is closed


def _extract_articles_with_llm(
    source, plain_text_with_links, llm_model="llama3.1", limit=10
):
    """
    Uses an Ollama LLM to extract article titles, URLs, and raw dates from plain text
    that includes appended raw URLs.
    """
    llm = Ollama(model=llm_model, temperature=0.1)

    extraction_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert web content extractor. Your task is to identify articles or posts from the provided text content.
        The text content contains the main body of the webpage, followed by a section titled "--- ALL LINKS ---" which lists all unique, absolute URLs found on the page, one per line.

        For each article, extract its title, its full URL, and its publication date string.
        The publication date can be in various formats (e.g., "2 days ago", "Yesterday", "September 1, 2023", "2023-09-01", "Published: 2023-08-10").

        **Crucially, when extracting the URL for an article, you MUST find it from the "--- ALL LINKS ---" section.** Match the title or context of the article to the most relevant URL provided in that section. Do NOT try to infer URLs directly from the main text or create them. If an article cannot be confidently matched to a URL in the list, do not include it.

        Return the results as a JSON array of objects. Each object must have 'source', 'type', 'format', 'title', 'url', 'raw_date' fields.
        The source is {source_name}, the type is {source_type}, and the format is {source_format}.

        If no articles are found, return an empty JSON array [].
        Limit your extraction to the first {limit} distinct articles you find.

        Example Output Format:
        [
          {{
            "source": "{source_name}",
            "type": "{source_type}",
            "format": "{source_format}",
            "title": "How to Use Ollama Locally",
            "url": "https://ollama.com/blog/local-ollama-guide",
            "raw_date": "2023-10-26"
          }},
          {{
            "source": "{source_name}",
            "type": "{source_type}",
            "format": "{source_format}",
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

    chain = extraction_prompt | llm

    input_variables = {
        "plain_text_with_links": plain_text_with_links,
        "limit": limit,
        "source_name": source.get("name"),
        "source_type": source.get("type"),
        "source_format": source.get("format"),
    }

    source_name = source.get("name", "Unknown")
    context_size = len(input_variables.get("plain_text_with_links", ""))
    logging.info(f"Invoking LLM '{llm_model}' for source '{source_name}'.")
    logging.info(f"Context size: {context_size:,} characters.")

    # Log other variables at a DEBUG level to avoid cluttering standard logs
    printable_vars = {
        k: v for k, v in input_variables.items() if k != "plain_text_with_links"
    }
    logging.debug(f"LLM input variables: {json.dumps(printable_vars, indent=2)}")

    try:
        # Time the LLM invocation
        start_time = time.time()
        response = chain.invoke(input_variables)
        end_time = time.time()

        duration = end_time - start_time
        logging.info(f"LLM for '{source_name}' finished in {duration:.2f} seconds.")

        return response
    except Exception as e:
        # Log errors with traceback information
        logging.error(
            f"Error during LLM extraction for '{source_name}': {e}", exc_info=True
        )
        return None


# --- Main Function for Web Articles ---


def fetch_web_articles(source, llm_model="llama3.1"):
    """
    Fetches articles from a webpage using Selenium and Ollama LLM.
    Returns the raw string output from the LLM.
    """
    logging.info(
        f"Fetching and preparing text with links for {source['name']} ({source['url']})"
    )

    if source.get("format") != "webpage":
        logging.warning(
            f"Source '{source['name']}' has format '{source.get('format')}' and will be skipped. "
            "Only 'webpage' format is supported by this function."
        )
        return

    # Assuming _fetch_and_prepare_text_with_links is defined elsewhere
    plain_text_with_links = _fetch_and_prepare_text_with_links(source["url"])

    if not plain_text_with_links:
        logging.error(f"Content fetching failed for {source['name']}.")
        return None

    logging.info(f"Extracting articles from {source['name']} using LLM ({llm_model})")
    llm_raw_output = _extract_articles_with_llm(
        source, plain_text_with_links, llm_model, limit=10
    )

    return llm_raw_output
