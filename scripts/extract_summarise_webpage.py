import sys
import requests
from bs4 import BeautifulSoup

# --- Setup and Configuration ---

# 1. Install Required Python Libraries:
#    pip install requests beautifulsoup4 langchain langchain_community

# 2. Install and Run Ollama:
#    - Download and install Ollama from https://ollama.com
#    - In your terminal, pull the Llama 3 model:
#      ollama run llama3
#    - IMPORTANT: The Ollama application must be running in the background.

try:
    from langchain_community.llms import Ollama
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
except ImportError:
    print("Error: LangChain libraries are not installed.", file=sys.stderr)
    print(
        "Please install them by running: pip install langchain langchain_community",
        file=sys.stderr,
    )
    sys.exit(1)


# --- Core Functions ---


def extract_text_from_url(url: str) -> str | None:
    """
    Fetches content from a URL, removes HTML tags using BeautifulSoup,
    and returns clean, compact text.
    """
    try:
        # Set a user-agent header to mimic a browser and avoid being blocked
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        # Use BeautifulSoup to parse the HTML content
        soup = BeautifulSoup(response.content, "html.parser")

        # Remove script and style elements which don't contain useful text
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # Get the text, use a space as a separator, and strip leading/trailing whitespace
        # This creates a single, compact block of text from the webpage.
        compact_text = soup.get_text(separator=" ", strip=True)
        return compact_text

    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(
            f"An unexpected error occurred during text extraction: {e}", file=sys.stderr
        )
        return None


def summarize_text_with_ollama(text: str, llm_chain) -> str:
    """
    Summarizes text using a LangChain chain connected to a local Ollama model.
    """
    # Truncate the text to a reasonable length to fit within the model's context window
    # 15,000 characters is a safe starting point for many articles.
    truncated_text = text[:15000]

    try:
        # Invoke the chain with the extracted text
        result = llm_chain.invoke({"webpage_text": truncated_text})
        return result["text"].strip()
    except Exception as e:
        print(f"\nAn error occurred during summarization: {e}", file=sys.stderr)
        return "Summary could not be generated. Is the Ollama application running?"


# --- Test Script Execution ---

if __name__ == "__main__":
    print("--- Starting Webpage Fetch and Summarize Test (with Ollama) ---")

    # --- Initialize LangChain and Ollama ---
    try:
        # A prompt template designed for summarizing web articles
        prompt_template = """
You are an expert content summarizer. Your task is to provide a concise, neutral summary of the following webpage text.
The summary should be approximately 100 words and capture the main topic, key points, and conclusions.
Ignore any irrelevant text like navigation menus, ads, or cookie notices that may have been included.
Provide only the summary text, without any introductory phrases.

WEBPAGE TEXT:
"{webpage_text}"

SUMMARY:
"""
        prompt = PromptTemplate(
            template=prompt_template, input_variables=["webpage_text"]
        )

        llm = Ollama(model="llama3.1")
        llm_chain = LLMChain(prompt=prompt, llm=llm)

    except Exception as e:
        print(
            "\nFatal Error: Could not initialize LangChain with Ollama.",
            file=sys.stderr,
        )
        print(f"Error details: {e}", file=sys.stderr)
        print(
            "\nPlease ensure Ollama is installed, running, and you have pulled a model (e.g., 'ollama run llama3').",
            file=sys.stderr,
        )
        sys.exit(1)
    # -----------------------------------------

    print("\nLangChain and Ollama initialized successfully.\n")

    # A list of example article URLs to test the script
    test_urls = [
        "https://www.aljazeera.com/",
        "https://progressive.international/",
        "https://non-existent-url-12345.com",  # An invalid URL to test error handling
    ]

    # Loop through each test URL
    for i, url in enumerate(test_urls):
        print(f"--- Test Case {i + 1}: Processing URL: {url} ---")

        # 1. Extract clean text from the webpage
        extracted_text = extract_text_from_url(url)

        # 2. If successful, summarize it
        if extracted_text:
            print("\n>>> Webpage Text Extracted Successfully.")
            print(">>> Generating Summary (~100 words) with Ollama Llama 3...")

            summary = summarize_text_with_ollama(extracted_text, llm_chain)

            print("\n✅ FINAL SUMMARY:")
            print(summary)
        else:
            print("\n❌ FAILED to extract text. Cannot generate summary.")

        print("\n" + "=" * 70 + "\n")

    print("--- Test Complete ---")
