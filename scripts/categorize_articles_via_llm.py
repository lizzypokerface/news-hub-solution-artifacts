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

    # Create a prompt template that instructs the LLM on its task.
    # The instructions are very specific to ensure the output is clean.
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
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
         """,
            ),
            ("user", 'Title: "{title}"\nSource: "{source}"\n\nCategory:'),
        ]
    )

    # Initialize the Ollama LLM
    try:
        llm = Ollama(model=OLLAMA_MODEL, temperature=0.0)
    except Exception as e:
        # This helps diagnose if Ollama is not running
        print(
            f"Error: Could not connect to Ollama. Is the Ollama application running? Details: {e}",
            file=sys.stderr,
        )
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
            "title": "US attacks blow back, uniting China, India, Russia, Iran; encouraging dedollarization",
            "source": "Geopolitical Economy Report",
        },
        {
            "title": "Inside BRICS' Push for AI Independence",
            "source": "Think BRICS - YouTube",
        },
        {
            "title": "Putin: Russia and China are united in our vision of building a just, multipolar world order",
            "source": "Friends of Socialist China",
        },
        {
            "title": "Xi, Modi & Putin Present a United Front: SCO Summit Review",
            "source": "The China-Global South Project",
        },
        {
            "title": "The message of the Victory Day parade: justice will prevail, peace will prevail and the people will prevail",
            "source": "Friends of Socialist China",
        },
        {
            "title": "What is behind China’s successful leadership in tackling the climate crisis?",
            "source": "Friends of Socialist China",
        },
        {
            "title": "China and DPRK jointly celebrate the 80th anniversary of victory over Japanese imperialism",
            "source": "Friends of Socialist China",
        },
        {
            "title": "China Challenges Japan Over Billions Spent to Rewrite Its “Comfort Women” History",
            "source": "The China Academy",
        },
        {
            "title": "History will likely be harsh in its judgement of Israel's actions in Gaza: Shanmugam",
            "source": "Channel News Asia",
        },
        {
            "title": "Singapore unveils initiatives to help workers become AI bilinguals",
            "source": "Channel News Asia",
        },
        {
            "title": "In Philippines, Indigenous peoples and advocates launch Defend Mindoro campaign against state abuses",
            "source": "Progressive International",
        },
        {
            "title": "What’s fuelling protests in Indonesia and why now?",
            "source": "South China Morning Post",
        },
        {
            "title": "Friendship with Pakistan is cornerstone of China’s regional diplomacy",
            "source": "Friends of Socialist China",
        },
        {
            "title": "Why Putin Made Zelensky an Offer, Knowing It Would Be Rejected",
            "source": "The China Academy",
        },
        {
            "title": "Journalist: Israel Killed My Colleagues and Reuters Justified It — So I Quit.",
            "source": "Breakthrough News",
        },
        {
            "title": "Settler Violence in the West Bank: Daily Attacks and Israel’s Annexation Plans",
            "source": "Middle East Eye",
        },
        {
            "title": "‘US Propaganda Against China Is Not Working in Africa’ w/ Zambia’s Dr. Fred M’membe",
            "source": "Breakthrough News",
        },
        {
            "title": "Why Jeremy Corbyn’s New Left-Wing Party Is Shaking Britain w/ Dr. Ashok Kumar",
            "source": "Breakthrough News",
        },
        {
            "title": "How President AMLO’s Policies Lifted 13.4 Million Mexicans Out of Poverty",
            "source": "Breakthrough News",
        },
        {
            "title": "Trump’s Police State: Why Aren’t Democrats Stopping Him?",
            "source": "Breakthrough News",
        },
    ]

    # Loop through each test article, categorize it, and print the result
    for i, article in enumerate(test_articles):
        title = article["title"]
        source = article["source"]

        print(f"--- Test Case {i + 1} ---")
        print(f'  Input Title: "{title}"')
        print(f'  Input Source: "{source}"')

        # Call the categorization function
        result_category = categorize_article_headline(title, source)

        print(f"  => LLM Output Category: {result_category}\n")

    print("--- Test Complete ---")
