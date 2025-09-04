import requests
from bs4 import BeautifulSoup  # Still useful for potential pre-processing of HTML
from datetime import datetime, timedelta, timezone
import json
import ollama  # Import the ollama client library

# --- Configuration for Ollama ---
OLLAMA_HOST = "http://localhost:11434"  # Default Ollama host
OLLAMA_MODEL = (
    "llama2"  # Or 'llama3', 'mistral', etc., depending on what you have pulled
)


# --- Helper to truncate HTML for LLM context window ---
def _truncate_html(html_content, max_chars=30000):
    """
    Truncates HTML content to a maximum number of characters.
    LLMs have token limits, and raw HTML can be very verbose.
    A more sophisticated approach might use BeautifulSoup to extract relevant sections.
    """
    if len(html_content) > max_chars:
        print(
            f"    -  Warning: HTML content is large ({len(html_content)} chars). Truncating to {max_chars} chars."
        )
        # Try to truncate at a natural break, like after a closing tag, if possible
        truncated = html_content[:max_chars]
        last_tag_end = truncated.rfind(">")
        if last_tag_end != -1:
            return truncated[: last_tag_end + 1]
        return truncated
    return html_content


def fetch_articles_via_llm(source):
    """
    Fetches articles using a local LLM (Ollama) to parse the HTML content.
    """
    results = []
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    try:
        # 1. Fetch the raw HTML content
        print(f"    -  Fetching HTML from {source['url']}")
        response = requests.get(source["url"])
        response.raise_for_status()
        html_content = response.text

        # 2. Pre-process HTML if too large for LLM context window
        processed_html = _truncate_html(html_content)

        # 3. Define the prompt for the LLM
        # This prompt is crucial for guiding the LLM to extract the correct info
        # Emphasize JSON output format for reliable parsing
        prompt_instructions = f"""
        You are an expert web scraper. Analyze the following HTML content from {source['name']}.
        Identify and extract information about recent articles or posts.
        For each article, extract its exact title, its full URL, and its publication date.
        Only include articles published within the last 7 days from today ({datetime.now().strftime('%Y-%m-%d')}).
        If a publication year is not explicitly mentioned, assume the current year.
        
        Output the results strictly as a JSON array of objects. Each object MUST have the keys:
        'title' (string): The title of the article.
        'url' (string): The full URL of the article.
        'date' (string): The publication date in YYYY-MM-DD format.
        
        If no relevant articles are found, return an empty JSON array `[]`.
        
        HTML Content for {source['url']}:
        {processed_html}
        """

        # 4. Call the local Ollama LLM
        print(f"    -  Calling Ollama model '{OLLAMA_MODEL}'...")
        client = ollama.Client(host=OLLAMA_HOST)

        llm_response = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts structured JSON data from HTML.",
                },
                {"role": "user", "content": prompt_instructions},
            ],
            # Adding format='json' (if supported by the model/ollama version) can help enforce JSON output
            # Some models might need it explicitly in the prompt.
            # options={'format': 'json'} # Uncomment if your Ollama version/model supports this
        )

        # Extract the content from the LLM's response
        llm_output_content = llm_response["message"]["content"]

        # Attempt to find the JSON part of the output, as LLMs can sometimes wrap it
        # This regex looks for the first JSON array or object
        json_match = re.search(r"\[.*\]|\{.*\}", llm_output_content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            print("    -  LLM response (JSON part found):")
            # print(json_str) # Uncomment to see the raw JSON from LLM
        else:
            raise ValueError("No JSON structure found in LLM response.")

        # 5. Parse the LLM's JSON response
        parsed_data = json.loads(json_str)

        if not isinstance(parsed_data, list):
            raise TypeError("LLM did not return a JSON array as expected.")

        for item in parsed_data:
            # Validate required keys
            if not all(k in item for k in ["title", "url", "date"]):
                print(
                    f"    -  Warning: LLM item missing required keys (title, url, date): {item}"
                )
                continue

            try:
                # Convert the date string from LLM into a datetime object
                article_date = datetime.strptime(item["date"], "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
                if article_date >= one_week_ago:
                    results.append(
                        {
                            "source": source["name"],
                            "title": item["title"],
                            "url": item["url"],
                            "date": article_date,
                        }
                    )
            except ValueError as e:
                print(
                    f"    -  Warning: Could not parse date '{item.get('date')}' for article '{item.get('title')}'. Error: {e}"
                )
            except Exception as e:
                print(f"    -  Warning: Error processing LLM item: {item}. Error: {e}")

    except requests.exceptions.RequestException as e:
        print(f"    -  HTTP error fetching {source['url']}: {e}")
    except json.JSONDecodeError as e:
        print(
            f"    -  LLM did not return valid JSON or JSON parsing failed for {source['name']}: {e}. Raw LLM output might be: {llm_output_content[:500]}..."
        )
    except ollama.ResponseError as e:
        print(
            f"    -  Ollama API error for {source['name']}: {e}. Is Ollama server running and model '{OLLAMA_MODEL}' pulled?"
        )
    except ValueError as e:
        print(f"    -  Data extraction error for {source['name']}: {e}")
    except Exception as e:
        print(f"    -  An unexpected error occurred for {source['name']}: {e}")

    return results


# --- Main Execution Block ---

if __name__ == "__main__":
    sources_to_fetch = [
        {
            "name": "Think BRICS Substack Archive",
            "url": "https://thinkbrics.substack.com/archive",
        },
        {
            "name": "The Socialist Program Patreon Posts",
            "url": "https://www.patreon.com/TheSocialistProgram/posts",
        },
        # Add other sources here. The beauty of LLMs is you don't need a new 'type'
        # for each site, as the LLM should adapt.
    ]

    print("Attempting to fetch recent articles using Ollama (Llama2)...")
    all_recent_articles = []
    for source_info in sources_to_fetch:
        print(f"\nProcessing source: {source_info['name']} ({source_info['url']})")
        articles = fetch_articles_via_llm(source_info)
        if articles:
            print(f"Found {len(articles)} recent articles for {source_info['name']}:")
            for article in articles:
                print(f"  - Title: {article['title']}")
                print(f"    URL: {article['url']}")
                print(
                    f"    Published: {article['date'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
                )
            all_recent_articles.extend(articles)
        else:
            print(
                f"No recent articles found for {source_info['name']} in the last 7 days, or an error occurred."
            )

    print("\n--- Summary of all recent articles ---")
    if all_recent_articles:
        all_recent_articles.sort(key=lambda x: x["date"], reverse=True)
        for article in all_recent_articles:
            print(
                f"[{article['source']}] {article['date'].strftime('%Y-%m-%d')} - {article['title']} ({article['url']})"
            )
    else:
        print("No recent articles found across all specified sources.")
