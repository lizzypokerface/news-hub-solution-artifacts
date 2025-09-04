# fetch_articles_via_llm

### `README.md`

```markdown
# Web Article Extractor with Selenium and Ollama

This script automates fetching content from web pages, cleaning the text, and using a locally-run Large Language Model (LLM) via Ollama to identify and extract article details. The raw, unprocessed JSON output from the language model is then saved to a text file.

## How It Works

The script performs the following steps for each URL you provide:

1.  **Automated Browsing**: It launches a headless (invisible) Google Chrome browser and navigates to the specified URL. This ensures that all content, including text loaded dynamically with JavaScript, is available for processing.
2.  **Content Cleaning**: The full HTML of the page is parsed. All non-essential elements like scripts, styles, and ads are stripped away to isolate the core text content.
3.  **Link Extraction**: Every unique link (`<a>` tag) on the page is identified and collected into a list of absolute URLs.
4.  **AI Prompting**: The cleaned text and the list of all extracted links are combined into a single document. This document is sent to your local Ollama LLM with a carefully crafted prompt, instructing it to find articles within the text and match them to their correct URLs from the provided link list.
5.  **Data Extraction**: The LLM processes the information and returns a JSON-formatted string containing the `title`, `url`, and `raw_date` for each article it identifies.
6.  **Saving the Output**: The script takes the raw text response directly from the LLM and saves it to `llm_extracted_articles.txt`. No further validation or parsing is done by the script, giving you the model's direct interpretation.

## Setup Requirements

Follow these steps carefully to set up your environment.

### 1. Python

You need Python installed on your system. This script is compatible with **Python 3.9 or newer**.

*   **Why?** While the script may work on older versions, Python 3.8 has reached its end-of-life and no longer receives security updates. [5, 10] Using a modern, supported version ensures better library compatibility and security. The latest stable version is Python 3.13. [1, 2]
*   **How?** Download and install Python from the [official Python website](https://www.python.org/downloads/).

### 2. Required Python Libraries

Install the necessary libraries using `pip`, Python's package installer. Open your terminal or command prompt and run:

```bash
pip install selenium beautifulsoup4 langchain-community langchain-core python-dateutil
```

*   `selenium`: Automates the web browser.
*   `beautifulsoup4`: Parses and cleans the HTML content.
*   `langchain-community` & `langchain-core`: Used to communicate with the Ollama language model.
*   `python-dateutil`: A powerful tool for parsing dates, used by an internal helper function.

### 3. Google Chrome and ChromeDriver

This script requires Google Chrome and its corresponding WebDriver.

*   **Install Google Chrome**: If you don't already have it, [download and install Google Chrome](https://www.google.com/chrome/).
*   **Install ChromeDriver**: This is a separate executable that `selenium` uses to control Chrome.
    *   **Crucial**: The version of ChromeDriver **must** match your installed version of Google Chrome.
    *   Go to the [**ChromeDriver Downloads**](https://developer.chrome.com/docs/chromedriver/downloads) page.
    *   The page will guide you to the correct download for your Chrome version. For Chrome 115 and newer, you will use the "Chrome for Testing availability dashboard" to get the right version.
    *   Download and extract the `chromedriver` executable.
    *   **Move the executable to a directory in your system's PATH**. This allows the script to find it automatically.
        *   **macOS/Linux**: A common location is `/usr/local/bin`.
        *   **Windows**: You can create a folder like `C:\WebDriver` and add it to your system's "Path" Environment Variable.

### 4. Ollama

The script uses a locally running Ollama instance to power the AI-based extraction.

1.  **Install Ollama**: [Download and install Ollama for your operating system](https://ollama.com/download).
2.  **Run Ollama**: Ensure the Ollama application is running in the background.
3.  **Pull a Model**: The script defaults to using the `llama3.1` model. Open your terminal and pull it by running:
    ```bash
    ollama pull llama3.1
    ```
    You can choose a different model (e.g., `mistral`, `gemma`) by pulling it and changing the `OLLAMA_MODEL` variable in the script.

## How to Run the Script

1.  **Save the Code**: Save the Python code below into a file named `article_extractor.py`.

2.  **Configure Sources**: Open `article_extractor.py` in an editor. Find the `web_sources_to_fetch` list near the bottom of the file and modify it to include the websites you want to process.

    ```python
    web_sources_to_fetch = [
        {
            "name": "Ollama Blog",
            "url": "https://ollama.com/blog",
        },
        {
            "name": "Another News Site",
            "url": "https://www.example-news.com/tech",
        },
    ]
    ```

3.  **Execute the Script**: Open your terminal, navigate to the directory where you saved the file, and run:

    ```bash
    python article_extractor.py
    ```

4.  **Check the Output**: The script will print its progress in the terminal. Once finished, a file named `llm_extracted_articles.txt` will be created in the same directory.

## Understanding the Output

The output file `llm_extracted_articles.txt` will contain the **raw text** returned by the language model for each source URL.

**Example Output:**
```
Source(https://ollama.com/blog):
[
  {
    "title": "Running Llama 3.1 on your local machine",
    "url": "https://ollama.com/blog/llama-3-1",
    "raw_date": "July 24, 2024"
  },
  {
    "title": "Meetups in your city",
    "url": "https://ollama.com/blog/meetups",
    "raw_date": "June 13, 2024"
  }
]

---

Source(https://www.example-news.com/tech):
No LLM output or an error occurred.

---
```

**Important**: The script saves the LLM's response directly. If the JSON is malformed, or the extracted data is inaccurate, it reflects the model's performance on the given task, not a bug in the script itself.

## Special Note for WSL2 (Windows Subsystem for Linux) Users

If you are running this script within a WSL2 environment on Windows, follow these setup points for Chrome:

1.  **Install Chrome inside WSL2**: You must install the browser within your Linux distribution. For Debian/Ubuntu-based distros, run:
    ```bash
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    sudo dpkg -i google-chrome-stable_current_amd64.deb
    sudo apt-get install -f # Install dependencies
    ```
2.  **Headless Operation**: The script runs Chrome in headless mode by default, so you do not need a graphical user interface or X-server running. The browser will operate in the background.
```

***

### `article_extractor.py`

```python
import re
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

import dateutil.parser as date_parser
# BeautifulSoup for parsing and cleaning HTML
from bs4 import BeautifulSoup
# LangChain and Ollama imports
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
# Selenium imports
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# --- Helper Functions ---

def _normalize_date(date_string):
    """
    Normalizes various date strings into a datetime object.
    Returns datetime_object or None if parsing fails.
    """
    if not date_string:
        return None
    now = datetime.now(timezone.utc)  # Use UTC for consistency

    # Handle relative dates first
    date_string_lower = date_string.lower()
    if "today" in date_string_lower:
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif "yesterday" in date_string_lower:
        return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif "ago" in date_string_lower:
        try:
            parts = date_string_lower.split()
            if len(parts) >= 2 and parts[0].isdigit():
                value = int(parts[0])
                unit = parts[1]
                if "day" in unit:
                    return (now - timedelta(days=value)).replace(hour=0, minute=0, second=0, microsecond=0)
                elif "week" in unit:
                    return (now - timedelta(weeks=value)).replace(hour=0, minute=0, second=0, microsecond=0)
                elif "month" in unit:
                    # Approximation for months
                    return (now - timedelta(days=value * 30)).replace(hour=0, minute=0, second=0, microsecond=0)
                elif "year" in unit:
                    return (now - timedelta(days=value * 365)).replace(hour=0, minute=0, second=0, microsecond=0)
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
    options.add_argument("--no-sandbox")  # Bypass OS security model, required for some environments
    options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")  # Mimic a real user agent

    driver = None  # Initialize driver to None for proper cleanup
    try:
        driver = webdriver.Chrome(options=options)

        print(f"    -  Navigating to {url} with Selenium...")
        driver.get(url)

        # Wait for the body tag to be present, indicating the page has started loading
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        # --- 1. Get clean plain text ---
        # Remove script and style tags before getting text
        for script_or_style in soup(['script', 'style']):
            script_or_style.extract()

        plain_text = soup.get_text()
        # Replace multiple newlines with a single one
        plain_text = re.sub(r'\n\s*\n', '\n', plain_text)
        # Remove leading/trailing whitespace from each line
        plain_text = '\n'.join([line.strip() for line in plain_text.splitlines()])
        # Replace multiple spaces with a single space
        plain_text = re.sub(r' +', ' ', plain_text)

        # --- 2. Extract all unique, absolute links ---
        extracted_urls = set()  # Use a set to store unique URLs
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']

            # Resolve relative URLs to absolute URLs
            absolute_href = urljoin(url, href)

            # Filter out common non-content links
            if absolute_href and not absolute_href.startswith(('mailto:', 'javascript:', '#')) and absolute_href != url:
                extracted_urls.add(absolute_href)

        # --- 3. Append links to the plain text ---
        if extracted_urls:
            # Sort for consistent output
            sorted_urls = sorted(list(extracted_urls))
            plain_text += "\n\n--- ALL LINKS ---\n"
            plain_text += "\n".join(sorted_urls)

        return plain_text
    except TimeoutException:
        print(f"    -  Timeout while loading {url}. Content might not have loaded.")
        return None
    except WebDriverException as e:
        print(
            f"    -  Selenium WebDriver error for {url}: {e}. Ensure Chrome browser is installed and compatible ChromeDriver is available in PATH.")
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
    This function returns the raw string response from the LLM.
    """
    llm = Ollama(model=llm_model, temperature=0.1)  # Low temperature for more predictable output

    # The prompt explicitly tells the LLM about the appended raw URLs section
    extraction_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert web content extractor. Your task is to identify articles or posts from the provided text content.
        The text contains the main body of a webpage, followed by a section titled "--- ALL LINKS ---" which lists all unique, absolute URLs found on that page.

        For each article you find, you must extract its title, its full URL, and its publication date string.
        The publication date can be in various formats (e.g., "2 days ago", "Yesterday", "September 1, 2023", "2023-09-01").

        **Crucially, you MUST find the URL for each article in the "--- ALL LINKS ---" section.** Match the article's title or context to the most relevant URL from that list. Do not invent URLs or infer them from the main text. If an article cannot be confidently matched to a URL in the list, do not include it.

        Return your findings as a JSON array of objects. Each object must have 'title', 'url', and 'raw_date' fields.
        If you find no articles, return an empty JSON array [].

        Example Output Format:
        [
          {
            "title": "How to Use Ollama Locally",
            "url": "https://ollama.com/blog/local-ollama-guide",
            "raw_date": "2023-10-26"
          },
          {
            "title": "New Features in Llama 3.1",
            "url": "https://ollama.com/blog/llama3.1-features",
            "raw_date": "1 day ago"
          }
        ]
        """),
        ("user", "Extract article details from this content:\n\n{plain_text_with_links}")
    ])

    # The chain directly returns the LLM's string output, with no parsing
    extraction_chain = extraction_prompt | llm

    try:
        # Invoke the chain and return the raw string response
        print("    -  Sending content to LLM for extraction...")
        return extraction_chain.invoke({"plain_text_with_links": plain_text_with_links})
    except Exception as e:
        print(f"    -  Error during LLM extraction: {e}")
        return None  # Return None on error


# --- Main Orchestration Function ---

def fetch_web_articles(source, llm_model="llama3.1"):
    """
    Orchestrates fetching articles from a webpage using Selenium and an Ollama LLM.
    Returns the raw string output from the LLM.
    """
    print(f"    -  Fetching and preparing text with links for {source['name']} ({source['url']})")
    plain_text_with_links = _fetch_and_prepare_text_with_links(source["url"])

    if not plain_text_with_links:
        return None  # Return None if content fetching failed

    llm_raw_output = _extract_articles_with_llm(plain_text_with_links, llm_model)

    return llm_raw_output


# --- Main Execution Block ---

if __name__ == "__main__":
    # Ensure Ollama is running and you have the model pulled (e.g., ollama pull llama3.1)
    OLLAMA_MODEL = "llama3.1"  # Or "mistral", "gemma", etc.
    OUTPUT_FILENAME = "llm_extracted_articles.txt"

    # --- CONFIGURE YOUR SOURCES HERE ---
    # Define the web pages you want to fetch articles from
    web_sources_to_fetch = [
        {
            "name": "Ollama Blog",
            "url": "https://ollama.com/blog",
        },
        {
            "name": "The Verge Tech",
            "url": "https://www.theverge.com/tech",
        },
        # Add more sources here
        # {
        #     "name": "Example News",
        #     "url": "https://www.example.com/news",
        # },
    ]

    print(f"Fetching web articles and saving raw LLM output to '{OUTPUT_FILENAME}'...")

    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as outfile:
        for web_source in web_sources_to_fetch:
            print(f"\nProcessing web source: {web_source['name']} ({web_source['url']})")

            # fetch_web_articles now returns the raw LLM string
            llm_output = fetch_web_articles(web_source, llm_model=OLLAMA_MODEL)

            outfile.write(f"Source({web_source['url']}):\n")
            if llm_output:
                outfile.write(llm_output.strip())
            else:
                outfile.write("No LLM output or an error occurred.")
            outfile.write("\n\n---\n\n")  # Separator between sources

            time.sleep(2)  # Be polite and wait between requests to different servers

    print(f"\nProcessing complete. Raw LLM outputs saved to '{OUTPUT_FILENAME}'.")
```

---

Related searches:
+ [latest stable python version](https://www.google.com/search?q=latest+stable+python+version&client=app-vertex-grounding-quora-poe)
+ [python 3.13 release date](https://www.google.com/search?q=python+3.13+release+date&client=app-vertex-grounding-quora-poe)
