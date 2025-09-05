# extract_summarise_youtube_transcript
This new script fetches the transcript as before, but then passes it to your local Llama 3 model via LangChain to generate the summary.

### `summarize_with_ollama.py`

```python
import sys
from urllib.parse import urlparse, parse_qs

# --- Setup and Configuration ---

# 1. Install Required Python Libraries:
#    pip install youtube-transcript-api
#    pip install langchain langchain_community

# 2. Install and Run Ollama:
#    - Download and install Ollama from https://ollama.com
#    - In your terminal, pull the Llama 3 model by running:
#      ollama run llama3
#    - IMPORTANT: Ollama must be running in the background for this script to work.

try:
    from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
except ImportError:
    print("Error: The 'youtube-transcript-api' library is not installed.", file=sys.stderr)
    print("Please install it by running: pip install youtube-transcript-api", file=sys.stderr)
    sys.exit(1)

try:
    from langchain_community.llms import Ollama
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
except ImportError:
    print("Error: LangChain libraries are not installed.", file=sys.stderr)
    print("Please install them by running: pip install langchain langchain_community", file=sys.stderr)
    sys.exit(1)


# --- Core Functions ---

def get_youtube_transcript(video_url: str) -> str | None:
    """
    Extracts the full, clean transcript from a YouTube video URL.
    """
    video_id = None
    try:
        parsed_url = urlparse(video_url)
        if "youtube.com" in parsed_url.hostname:
            video_id = parse_qs(parsed_url.query).get("v", [None])[0]
        elif "youtu.be" in parsed_url.hostname:
            video_id = parsed_url.path.lstrip('/')

        if not video_id:
            print(f"Error: Could not extract video ID from URL: {video_url}", file=sys.stderr)
            return None

        ytt_api = YouTubeTranscriptApi()
        transcript_data = ytt_api.fetch(video_id)
        text_segments = [snippet.text for snippet in transcript_data]
        return " ".join(text_segments)

    except (TranscriptsDisabled, NoTranscriptFound) as e:
        print(f"Could not retrieve transcript for {video_url}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching transcript for ID '{video_id}': {e}", file=sys.stderr)
        return None

def summarize_transcript_with_ollama(transcript: str, llm_chain) -> str:
    """
    Summarizes a transcript using a LangChain chain connected to a local Ollama model.
    """
    # Avoid summarizing very short transcripts
    if len(transcript.split()) < 120:
        return "Transcript is too short to provide a meaningful summary."

    try:
        # The invoke method runs the chain. The input must be a dictionary
        # where the key matches the input variable in the prompt template.
        result = llm_chain.invoke({"transcript": transcript})

        # The output from the chain is a dictionary, with the response under the 'text' key.
        return result['text'].strip()
    except Exception as e:
        # This error often happens if Ollama isn't running.
        print(f"\nAn error occurred during summarization: {e}", file=sys.stderr)
        return "Summary could not be generated. Is the Ollama application running?"


# --- Test Script Execution ---

if __name__ == "__main__":
    print("--- Starting YouTube Transcript Fetch and Summarize Test (with Ollama) ---")

    # --- Initialize LangChain and Ollama ---
    # This setup is done once to be reused for all videos in the test run.
    try:
        # Define the prompt template with clear instructions for the model
        prompt_template = """
You are an expert summarizer. Your task is to provide a concise, neutral summary of the following video transcript.
The summary should be approximately 100 words and capture the main points and arguments.
Provide only the summary text, without any introductory phrases like "Here is the summary:".

TRANSCRIPT:
"{transcript}"

SUMMARY:
"""
        # Create a PromptTemplate object
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["transcript"]
        )

        # Initialize the connection to the local Ollama model (e.g., Llama 3)
        llm = Ollama(model="llama3")

        # Create the LLMChain, which combines the prompt and the model
        llm_chain = LLMChain(prompt=prompt, llm=llm)

    except Exception as e:
        print(f"\nFatal Error: Could not initialize LangChain with Ollama.", file=sys.stderr)
        print(f"Error details: {e}", file=sys.stderr)
        print("\nPlease ensure Ollama is installed, running, and you have pulled a model (e.g., 'ollama run llama3').", file=sys.stderr)
        sys.exit(1)
    # -----------------------------------------

    print("\nLangChain and Ollama initialized successfully.\n")

    # A list of example YouTube video URLs to test the script
    test_video_urls = [
        "https://www.youtube.com/watch?v=ulvxk3tWhuM",  # Breakthrough News on AMLO's policies
        "https://www.youtube.com/watch?v=sVhU_q1ZYjQ",  # Second Thought on Neoliberalism
        "https://www.youtube.com/watch?v=non_existent_video_id", # An invalid URL to test error handling
    ]

    # Loop through each test URL
    for i, url in enumerate(test_video_urls):
        print(f"--- Test Case {i + 1}: Processing URL: {url} ---")

        # 1. Fetch the transcript
        transcript = get_youtube_transcript(url)

        # 2. If successful, summarize it
        if transcript:
            print("\n>>> Transcript Fetched Successfully.")
            print(">>> Generating Summary (~100 words) with Ollama Llama 3...")

            summary = summarize_transcript_with_ollama(transcript, llm_chain)

            print("\n✅ FINAL SUMMARY:")
            print(summary)
        else:
            print("\n❌ FAILED to retrieve transcript. Cannot generate summary.")

        print("\n" + "="*70 + "\n")

    print("--- Test Complete ---")
```

### How to Use and Run the Script

1.  **Install Ollama**: Go to [ollama.com](https://ollama.com), download, and install the application for your operating system.

2.  **Download a Model**: Open your terminal and run the following command to download and run Llama 3. This makes the model available to the script.
    ```bash
    ollama run llama3
    ```
    You can close the chat interface after it loads, but **you must leave the Ollama application running** in the background (usually as an icon in your menu bar or system tray).

3.  **Install Python Libraries**: Install all the necessary packages for this script.
    ```bash
    pip install youtube-transcript-api langchain langchain_community
    ```

4.  **Save and Run**: Save the code above into a file named `summarize_with_ollama.py` and execute it from your terminal.
    ```bash
    python summarize_with_ollama.py
    ```

### How It Works

1.  **`get_youtube_transcript`**: This function remains the same and is responsible for fetching the raw text from the YouTube video.
2.  **LangChain Setup (in `main`)**:
    *   `Ollama(model="llama3")`: This object from `langchain_community` acts as the bridge to your locally running Ollama instance, telling it to use the `llama3` model.
    *   `PromptTemplate`: We design a specific set of instructions for the AI. This is crucial for getting a good summary. We explicitly ask for a ~100-word summary and tell it to avoid conversational filler.
    *   `LLMChain`: This chain links the `prompt` and the `llm` (Ollama) together. When you give it a transcript, it automatically formats the full prompt and sends it to the model.
3.  **`summarize_transcript_with_ollama`**:
    *   This function takes the transcript and the pre-built `llm_chain` as input.
    *   `llm_chain.invoke(...)` is the command that sends the data through the chain. LangChain handles the API call to your local Ollama server.
    *   It then extracts and returns the clean text response from the model. The error handling specifically checks for connection issues, which is the most common problem if Ollama isn't running.
