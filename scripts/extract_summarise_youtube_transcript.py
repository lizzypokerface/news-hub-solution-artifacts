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
    from youtube_transcript_api import (
        YouTubeTranscriptApi,
        TranscriptsDisabled,
        NoTranscriptFound,
    )
except ImportError:
    print(
        "Error: The 'youtube-transcript-api' library is not installed.", file=sys.stderr
    )
    print(
        "Please install it by running: pip install youtube-transcript-api",
        file=sys.stderr,
    )
    sys.exit(1)

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
            video_id = parsed_url.path.lstrip("/")

        if not video_id:
            print(
                f"Error: Could not extract video ID from URL: {video_url}",
                file=sys.stderr,
            )
            return None

        ytt_api = YouTubeTranscriptApi()
        transcript_data = ytt_api.fetch(video_id)
        text_segments = [snippet.text for snippet in transcript_data]
        return " ".join(text_segments)

    except (TranscriptsDisabled, NoTranscriptFound) as e:
        print(f"Could not retrieve transcript for {video_url}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(
            f"An unexpected error occurred while fetching transcript for ID '{video_id}': {e}",
            file=sys.stderr,
        )
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
        return result["text"].strip()
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
            template=prompt_template, input_variables=["transcript"]
        )

        # Initialize the connection to the local Ollama model (e.g., Llama 3)
        llm = Ollama(model="llama3.1")

        # Create the LLMChain, which combines the prompt and the model
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

    # A list of example YouTube video URLs to test the script
    test_video_urls = [
        "https://www.youtube.com/watch?v=ulvxk3tWhuM",  # Breakthrough News on AMLO's policies
        "https://www.youtube.com/watch?v=sVhU_q1ZYjQ",  # Second Thought on Neoliberalism
        "https://www.youtube.com/watch?v=non_existent_video_id",  # An invalid URL to test error handling
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

        print("\n" + "=" * 70 + "\n")

    print("--- Test Complete ---")
