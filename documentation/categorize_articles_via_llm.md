# categorize_articles_via_llm

### `categorize_articles_test.py`

```python
import sys
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- Setup and Configuration ---

# 1. Install Required Libraries:
#    Open your terminal and run the following command:
#    pip install langchain-community langchain-core

# 2. Install and Run Ollama:
#    - Download and install Ollama from https://ollama.com
#    - Ensure the Ollama application is running in the background.

# 3. Pull a Language Model:
#    - This script defaults to 'llama3.1'. You can change it below.
#    - Open your terminal and run:
#      ollama pull llama3.1
#    - If you use a different model, update the OLLAMA_MODEL variable.

OLLAMA_MODEL = "llama3.1"


# --- Core Categorization Function ---

def categorize_article_headline(title: str, source: str) -> str:
    """
    Categorizes a news article into a predefined geographic category using an Ollama LLM.

    Args:
        title: The headline of the news article.
        source: The source of the news article (e.g., 'Reuters', 'Al Mayadeen English').

    Returns:
        A string representing the single most appropriate category.
    """
    # Define the list of valid categories for the LLM
    categories = [
        "Global", "China", "East Asia", "Singapore", "Southeast Asia",
        "South Asia", "Central Asia", "Russia", "Oceania",
        "West Asia (Middle East)", "Africa", "Europe", "Latin America & Caribbean",
        "North America", "Unknown"
    ]

    # Create a prompt template that instructs the LLM on its task.
    # The instructions are very specific to ensure the output is clean.
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         f"""You are an expert news editor with deep geopolitical knowledge. Your task is to categorize a news article based ONLY on its title and source.

         You MUST choose exactly one category from the following list:
         {', '.join(categories)}

         - 'Global': Use for articles involving multiple distinct regions (e.g., a US-China summit, a UN resolution).
         - 'Singapore': Use ONLY for articles specifically about Singapore.
         - 'West Asia (Middle East)': For countries like Lebanon, Iran, Saudi Arabia, Palestine, etc.
         - 'East Asia': For Japan, South Korea, North Korea.
         - 'Southeast Asia': For countries like Vietnam, Thailand, Indonesia, Malaysia, Philippines.
         - 'South Asia': For India, Pakistan, Bangladesh, Sri Lanka.
         - 'Central Asia': For Kazakhstan, Uzbekistan, etc.
         - 'Oceania': For Australia, New Zealand, Pacific Islands.
         - 'Unknown': Use ONLY if you cannot determine the region with confidence.

         Analyze the geographic entities (countries, cities, regions) mentioned in the title. The source can also be a strong clue.

         Your response MUST BE ONLY the category name and nothing else. Do not add explanations or any extra text.
         """),
        ("user", "Title: \"{title}\"\nSource: \"{source}\"\n\nCategory:")
    ])

    # Initialize the Ollama LLM
    try:
        llm = Ollama(model=OLLAMA_MODEL, temperature=0.0)
    except Exception as e:
        # This helps diagnose if Ollama is not running
        print(f"Error: Could not connect to Ollama. Is the Ollama application running? Details: {e}", file=sys.stderr)
        return "Error: Ollama connection failed"

    # Create a simple chain that pipes the prompt to the LLM and then to a string parser
    chain = prompt | llm | StrOutputParser()

    # Invoke the chain with the article details
    try:
        category = chain.invoke({"title": title, "source": source})
        # Clean up any potential whitespace issues from the model's output
        return category.strip()
    except Exception as e:
        print(f"An error occurred during LLM invocation: {e}", file=sys.stderr)
        return "Error: LLM invocation failed"


# --- Test Script Execution ---

if __name__ == "__main__":
    print("--- Starting News Article Categorization Test ---")
    print(f"Using Ollama Model: {OLLAMA_MODEL}\n")

    # A list of test cases with varied titles and sources to test the LLM's reasoning
    test_articles = [
        {
            "title": "We withdrew to protest army plan discussion: Lebanese labor minister",
            "source": "Al Mayadeen English"
        },
        {
            "title": "China's BYD launches its first pickup truck in Mexico",
            "source": "Reuters"
        },
        {
            "title": "Singapore's core inflation eases to 3.1% in April",
            "source": "Channel News Asia"
        },
        {
            "title": "G7 leaders to gather in Italy for crucial summit on global economy",
            "source": "Associated Press"
        },
        {
            "title": "Russia launches massive drone attack on Ukrainian energy infrastructure",
            "source": "Kyiv Independent"
        },
        {
            "title": "Floods in Brazil's south leave thousands homeless",
            "source": "BBC News"
        },
        {
            "title": "Japan and South Korea agree to strengthen security ties amid regional tensions",
            "source": "Nikkei Asia"
        },
        {
            "title": "Elections in India enter final phase",
            "source": "The Hindu"
        },
        {
            "title": "New Zealand announces new trade deal with the European Union",
            "source": "Radio New Zealand"
        },
        {
            "title": "Scientists Discover New Species of Deep-Sea Fish",
            "source": "National Geographic"
        },
    ]

    # Loop through each test article, categorize it, and print the result
    for i, article in enumerate(test_articles):
        title = article["title"]
        source = article["source"]

        print(f"--- Test Case {i + 1} ---")
        print(f"  Input Title: \"{title}\"")
        print(f"  Input Source: \"{source}\"")

        # Call the categorization function
        result_category = categorize_article_headline(title, source)

        print(f"  => LLM Output Category: {result_category}\n")

    print("--- Test Complete ---")
```

### How to Run the Test Script

1.  **Save the Code**: Save the code above into a file named `categorize_articles_test.py`.
2.  **Ensure Setup is Complete**: Make sure you have installed the required libraries and that the Ollama application is running with the necessary model pulled.
3.  **Execute from Terminal**: Open your terminal or command prompt, navigate to the directory where you saved the file, and run the following command:
    ```bash
    python categorize_articles_test.py
    ```

### Expected Output

When you run the script, you will see an output similar to the following. The exact categories may vary slightly based on the model's reasoning, but this demonstrates the expected format and likely results.

```
--- Starting News Article Categorization Test ---
Using Ollama Model: llama3.1

--- Test Case 1 ---
  Input Title: "We withdrew to protest army plan discussion: Lebanese labor minister"
  Input Source: "Al Mayadeen English"
  => LLM Output Category: West Asia (Middle East)

--- Test Case 2 ---
  Input Title: "China's BYD launches its first pickup truck in Mexico"
  Input Source: "Reuters"
  => LLM Output Category: Global

--- Test Case 3 ---
  Input Title: "Singapore's core inflation eases to 3.1% in April"
  Input Source: "Channel News Asia"
  => LLM Output Category: Singapore

--- Test Case 4 ---
  Input Title: "G7 leaders to gather in Italy for crucial summit on global economy"
  Input Source: "Associated Press"
  => LLM Output Category: Global

--- Test Case 5 ---
  Input Title: "Russia launches massive drone attack on Ukrainian energy infrastructure"
  Input Source: "Kyiv Independent"
  => LLM Output Category: Russia

--- Test Case 6 ---
  Input Title: "Floods in Brazil's south leave thousands homeless"
  Input Source: "BBC News"
  => LLM Output Category: Latin America & Caribbean

--- Test Case 7 ---
  Input Title: "Japan and South Korea agree to strengthen security ties amid regional tensions"
  Input Source: "Nikkei Asia"
  => LLM Output Category: East Asia

--- Test Case 8 ---
  Input Title: "Elections in India enter final phase"
  Input Source: "The Hindu"
  => LLM Output Category: South Asia

--- Test Case 9 ---
  Input Title: "New Zealand announces new trade deal with the European Union"
  Input Source: "Radio New Zealand"
  => LLM Output Category: Global

--- Test Case 10 ---
  Input Title: "Scientists Discover New Species of Deep-Sea Fish"
  Input Source: "National Geographic"
  => LLM Output Category: Unknown

--- Test Complete ---
```
