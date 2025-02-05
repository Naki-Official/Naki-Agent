import time
import schedule
from typing import List
from datetime import datetime


from agents.tools.cookie import CookieToolkit

class CoinDiscoveryScheduler:
    """
    A scheduler that periodically runs the coin discovery process.
    """
    def __init__(self, api_key: str, interval: str = "_3Days", top_k: int = 20):
        self.cookie_toolkit = CookieToolkit(api_key=api_key)
        self.interval = interval
        self.top_k = top_k

    def search_coins(self) -> List[dict]:
        """
        Perform the coin search using get_top_agents.
        """
        print("Searching for promising coins...")
        try:
            promising_coins = self.cookie_toolkit.get_top_agents(self.interval, self.top_k)
            print(f"Found {len(promising_coins)} promising coin(s).")
            return promising_coins
        except Exception as e:
            print("Error during coin search: %s", e)
            return []

    def run_coin_search(self):
        """
        This function is scheduled to run periodically (e.g., every minute).
        """
        print("Starting scheduled coin search at %s", datetime.now())
        result = self.search_coins()
        if result:
            print(f"Promising coins found: {result}")
        else:
            print("No coins found or an error occurred.")

    def start(self):
        """
        Schedule the coin search every minute and run indefinitely.
        """
        print("Starting CoinDiscoveryScheduler...")
        schedule.every(5).minutes.do(self.run_coin_search)
        
        # Optionally run an initial search immediately.
        self.run_coin_search()

        while True:
            schedule.run_pending()
            time.sleep(1)