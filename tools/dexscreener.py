import json
import logging
from typing import List, Dict

import requests


class DexscreenerToolkit():
    """
    DexscreenerToolkit provides methods to interact with the Dexscreener API.
    It supports searching for token pairs by token symbol or by token contract address.
    """

    def __init__(self):
        """
        Initialize the Dexscreener Toolkit.
        """
        self.base_url = "https://api.dexscreener.com/latest/dex/search"

    def _request(self, url: str) -> str:
        """
        Internal method to make a GET request to the specified URL.

        Args:
            url (str): The URL to which the GET request is sent.

        Returns:
            str: The response text from the GET request if successful.
                 In case of an error, returns a JSON string with an error message.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            return response.text
        except Exception as e:
            logging.error(f"Error in DexscreenerToolkit _request: {e}")
            return json.dumps({"error": str(e)})

    def search_by_token(self, token_symbol: str) -> str:
        """
        Search for token pairs on Dexscreener by token symbol.
        The method queries the API with the provided token symbol and then iterates
        over the returned list of pairs. It checks each pair’s base token and returns
        those where the base token's symbol (in lowercase) exactly matches the input.

        Args:
            token_symbol (str): The symbol of the token to search for (e.g., "SOL").

        Returns:
            str: A JSON-formatted string containing a list of matching token pair information.
                 If no matching pairs are found, returns an empty list.
        """
        try:
            # Construct the API URL. Note: The API expects a query parameter "q".
            # Since the Dexscreener API usually expects a query like "TOKEN/QUOTE",
            # here we simply pass the token_symbol and then filter the results.
            url = f"{self.base_url}?q={token_symbol}"
            response_text = self._request(url)
            data = json.loads(response_text)

            pairs: List[Dict] = data.get("pairs", [])
            for pair in pairs:
                base_token = pair.get("baseToken", {})
                if base_token.get("symbol", "").lower() == token_symbol.lower():
                    return json.dumps(pair)
            return json.dumps([])
        
        except Exception as e:
            logging.error(f"Error in search_by_token: {e}")
            return json.dumps({"error": str(e)})

    def search_by_address(self, token_address: str) -> str:
        """
        Search for token pairs on Dexscreener by token contract address.
        The method queries the API and iterates over the returned list of pairs.
        It checks each pair’s base token and returns those where the base token's address
        (converted to lowercase) exactly matches the provided address (also in lowercase).

        Args:
            token_address (str): The contract address of the token to search for.

        Returns:
            str: A JSON-formatted string containing a list of matching token pair information.
                 If no matching pairs are found, returns an empty list.
        """
        try:
            # Construct the API URL using the token_address as the query.
            # Depending on the API behavior, you might need to adjust the query string.
            url = f"{self.base_url}?q={token_address}"
            response_text = self._request(url)
            data = json.loads(response_text)

            pairs: List[Dict] = data.get("pairs", [])
            for pair in pairs:
                base_token = pair.get("baseToken", {})
                if base_token.get("address", "").lower() == token_address.lower():
                    return pair
            return {}
        
        except Exception as e:
            logging.error(f"Error in search_by_address: {e}")
            return json.dumps({"error": str(e)})
