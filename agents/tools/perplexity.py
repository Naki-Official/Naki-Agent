from typing import Optional

from agno.tools import Toolkit

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("`openai` not installed. Please install using `pip install openai`.")


class PerplexityTools(Toolkit):
    """
    PerplexityTools is a toolkit for performing internet searches via
    the Perplexity API, mainly focused on crypto research tasks such as
    discovering token symbols, retrieving project information, and more.
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = "https://api.perplexity.ai",
        model: str = "llama-3.1-sonar-small-128k-online"
    ):
        """
        Initialize the PerplexityTools with an API key and relevant settings.

        Args:
            api_key (str): The API key for the Perplexity API.
            base_url (Optional[str]): The endpoint for the Perplexity API.
            model (Optional[str]): The model to use when querying Perplexity.
        """
        super().__init__(name="perplexity")

        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

        # Register the methods so they can be called through the toolkit interface.
        self.register(self.search_internet)
        self.register(self.get_token_information)

    def search_internet(self, query: str) -> str:
        """
        Perform a general internet search through the Perplexity API.

        Args:
            query (str): Any keyword or question to be searched.

        Returns:
            str: The text output from Perplexity.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that searches the internet "
                    "and provides concise, relevant information to the user."
                ),
            },
            {
                "role": "user",
                "content": query,
            },
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content

    def get_token_information(self, token_symbol: str) -> str:
        """
        Gather comprehensive details about a token using its symbol. This may include:
        - Project origin and sector (DeFi, NFT, L2, AI, Meme, etc.)
        - Price or market cap
        - Exchanges where it's listed
        - Additional insights such as team, roadmap, and community updates.

        Args:
            token_symbol (str): The token symbol (e.g., "ETH", "ABC").

        Returns:
            str: A textual summary of the token's key information.
        """
        prompt = (
            f"Collect all important information for the token '{token_symbol}'. "
            "Include details about its origin, market cap, sector, listing on exchanges, "
            "notable team members, and any relevant events."
        )

        return self.search_internet(prompt)