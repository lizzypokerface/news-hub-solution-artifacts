import logging
import sys
import time
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- Module Configuration ---

# Configure basic logging for the module.
# This will output log messages to the console.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

# Default model to use. Can be overridden in the function call.
OLLAMA_MODEL = "llama3.1"

# Define the list of valid categories.
# Defined once at the module level for efficiency.
CATEGORIES = [
    "Global",
    "China",
    "East Asia",
    "Singapore",
    "Southeast Asia",
    "South Asia",
    "Central Asia",
    "Russia",
    "Oceania",
    "West Asia (Middle East)",
    "Africa",
    "Europe",
    "Latin America & Caribbean",
    "North America",
    "Unknown",
]

# --- Core Prompt Template ---

# The prompt is created once and reused by the function.
PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            f"""You are an expert news editor with deep geopolitical knowledge. Your task is to categorize a news article based ONLY on its title and source.

        You MUST choose exactly one category from the following list:
        {', '.join(CATEGORIES)}

        - 'Global': Use for articles involving multiple distinct regions (e.g., a US-China summit, a UN resolution).
        - 'North America': For the United States and Canada.
        - 'Latin America & Caribbean': For countries in Central and South America, and the Caribbean.
        - 'Europe': For European countries, including the UK and the European Union as an entity.
        - 'Africa': For countries on the African continent.
        - 'Russia': For articles primarily about Russia.
        - 'West Asia (Middle East)': For countries like Lebanon, Iran, Saudi Arabia, Palestine, etc.
        - 'Central Asia': For Kazakhstan, Uzbekistan, etc.
        - 'South Asia': For India, Pakistan, Bangladesh, Sri Lanka.
        - 'Southeast Asia': For countries like Vietnam, Thailand, Indonesia, Malaysia, Philippines.
        - 'Singapore': Use ONLY for articles specifically about Singapore.
        - 'East Asia': For Japan, South Korea, North Korea.
        - 'China': For articles primarily about China.
        - 'Oceania': For Australia, New Zealand, Pacific Islands.
        - 'Unknown': Use ONLY if you cannot determine the region with confidence.

        Analyze the geographic entities (countries, cities, regions) mentioned in the title. The source can also be a strong clue.

        Your response MUST BE ONLY the category name and nothing else. Do not add explanations or any extra text.
        """,
        ),
        ("user", 'Title: "{title}"\nSource: "{source}"\n\nCategory:'),
    ]
)

# --- Callable Function ---


def categorize_article_region(
    title: str, source: str, model: str = OLLAMA_MODEL
) -> str:
    """
    Categorizes a news article into a predefined geographic category using an Ollama LLM.

    Args:
        title: The headline of the news article.
        source: The source of the news article (e.g., 'Reuters', 'Al Mayadeen English').
        model: The Ollama model to use (defaults to OLLAMA_MODEL).

    Returns:
        A string representing the single most appropriate category, or an error message
        if categorization fails.
    """
    logging.info(f"Categorizing article: '{title}' from source: '{source}'")

    try:
        llm = Ollama(model=model, temperature=0.0)
        chain = PROMPT_TEMPLATE | llm | StrOutputParser()
    except Exception as e:
        logging.error(
            f"Failed to connect to Ollama. Is the Ollama application running? Details: {e}",
            exc_info=True,
        )
        return "Error: Ollama connection failed"

    # Prepare input for invocation
    input_data = {"title": title, "source": source}

    # Log context size
    formatted_prompt = PROMPT_TEMPLATE.format(**input_data)
    context_size = len(formatted_prompt)
    logging.info(f"LLM context size: {context_size} characters.")

    try:
        # Time the LLM invocation
        start_time = time.time()
        category = chain.invoke(input_data)
        end_time = time.time()

        duration = end_time - start_time
        logging.info(f"LLM for '{title}' completed in {duration:.2f} seconds.")

        # Clean up any potential whitespace issues from the model's output
        cleaned_category = category.strip()
        if cleaned_category not in CATEGORIES:
            logging.warning(
                f"LLM returned an invalid category: '{cleaned_category}'. Defaulting to 'Unknown'."
            )
            return "Unknown"

        return cleaned_category

    except Exception as e:
        logging.error(
            f"An error occurred during LLM invocation for title '{title}': {e}",
            exc_info=True,
        )
        return "Error: LLM invocation failed"
