import json
import logging
import numpy as np
from typing import List, Tuple, Optional

import requests
from agno.tools import Toolkit

from agents.utils.util import safe_ratio, compute_ratio_score, log_robust_normalize, robust_normalize


class CookieToolkit(Toolkit):
    """
    The CookieToolkit class provides methods to interact with the Cookie APIs.
    It offers endpoints to retrieve agent details by Twitter username or contract address,
    fetch a paged list of agents, and search for tweets by a query within a specified date range.
    
    All requests require an API key which is passed in the header as 'x-api-key'.
    If the API call is successful, the function returns a JSON string containing
    {"ok": <data>, "success": true, "error": null}. Otherwise, it returns an error.
    """

    def __init__(self, api_key: str):
        """
        Initialize the Cookie Toolkit.

        Args:
            api_key (str): The API key for accessing the Cookie endpoints.
        """
        super().__init__(name="cookie")
        self.api_key = api_key
        # Define the base URL for the Cookie API.
        # Update this value if the actual API domain is different.
        self.base_url = "https://api.cookie.fun"

        # Register toolkit functions
        self.register(self.get_agent_by_twitter_username)
        self.register(self.get_agent_by_contract_address)
        self.register(self.get_agents_paged)
        self.register(self.search_tweets)
        self.register(self.get_all_agents)

    def _request(self, url: str) -> str:
        """
        Internal method to make a GET request to the specified URL with the required headers.
        If the request is successful and the returned JSON contains "success": true,
        only the data within the "ok" field is returned.

        Args:
            url (str): The fully constructed URL to which the GET request will be sent.

        Returns:
            str: A JSON-formatted string with keys "ok", "success", and "error".
        """
        try:
            headers = {
                "accept": "application/json",
                "x-api-key": self.api_key,
            }
            print(f"Requesting URL: {url}")
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") is True:
                    return json.dumps({"ok": data.get("ok"), "success": True, "error": None})
                else:
                    return json.dumps({"ok": None, "success": False, "error": data.get("error")})
            else:
                raise Exception(response.text)
        except Exception as e:
            logging.error(f"Error in CookieToolkit _request: {e}")
            return json.dumps({"ok": None, "success": False, "error": str(e)})

    def get_agent_by_twitter_username(self, twitter_username: str, interval: str) -> str:
        """
        Retrieve agent details for a specific Twitter username over a given interval.

        Args:
            twitter_username (str): The Twitter username of the agent (case insensitive).
            interval (str): The interval for Twitter stats and deltas (e.g., _3Days, _7Days).

        Returns:
            str: A JSON-formatted string containing the agent details in the "ok" field if successful.
        """
        endpoint = f"/v2/agents/twitterUsername/{twitter_username}?interval={interval}"
        url = self.base_url + endpoint
        return self._request(url)

    def get_agent_by_contract_address(self, contract_address: str, interval: str) -> str:
        """
        Retrieve agent details for an agent identified by one of its token's contract addresses over a given interval.

        Args:
            contract_address (str): The contract address of one of the agent's token contracts (case insensitive).
            interval (str): The interval for Twitter stats and deltas (e.g., _3Days, _7Days).

        Returns:
            str: A JSON-formatted string containing the agent details in the "ok" field if successful.
        """
        endpoint = f"/v2/agents/contractAddress/{contract_address}?interval={interval}"
        url = self.base_url + endpoint
        return self._request(url)

    def get_agents_paged(self, interval: str, page: int, page_size: int) -> str:
        """
        Retrieve a paged list of agent details for a specified interval, ordered by mindshare (7 days, descending).

        Args:
            interval (str): The interval for Twitter stats and deltas (e.g., _3Days, _7Days).
            page (int): The page number to retrieve (starts at 1).
            page_size (int): The number of agents per page (between 1 and 25).

        Returns:
            str: A JSON-formatted string containing the paged agent details in the "ok" field if successful.
        """
        endpoint = f"/v2/agents/agentsPaged?interval={interval}&page={page}&pageSize={page_size}"
        url = self.base_url + endpoint
        return self._request(url)

    def search_tweets(self, search_query: str, from_date: str, to_date: str) -> str:
        """
        Retrieve popular tweet content matching a search query, filtered by a creation date range.

        Args:
            search_query (str): The word or phrase to search for in tweet text.
            from_date (str): The start date (YYYY-MM-DD) - only consider content created after this date.
            to_date (str): The end date (YYYY-MM-DD) - only consider content created before this date.

        Returns:
            str: A JSON-formatted string containing the tweet search results in the "ok" field if successful.
        """
        endpoint = f"/v1/hackathon/search/{search_query}?from={from_date}&to={to_date}"
        url = self.base_url + endpoint
        return self._request(url)

    def get_all_agents(self, interval: str) -> list:
        """
        Retrieve all agents by iterating through all pages using a page size of 25.
        This minimizes the number of pages to iterate through. It collects the data from each page
        (which is found under the "data" field of the "ok" object returned by get_agents_paged)
        and then returns a consolidated list of all agents.

        Args:
            interval (str): The interval for Twitter stats and deltas (e.g., _3Days, _7Days).

        Returns:
            list: A list of all agents retrieved from the API.
        """
        all_agents = []
        page = 1
        page_size = 25

        while True:
            # Get the paged data
            response_str = self.get_agents_paged(interval, page, page_size)
            response_json = json.loads(response_str)

            # If the call was not successful, return the error immediately.
            if not response_json.get("success"):
                return []

            ok_data = response_json.get("ok", {})
            page_agents = ok_data.get("data", [])
            all_agents.extend(page_agents)

            total_pages = ok_data.get("totalPages", 1)

            # Break if we have reached the last page or mindshare in first agent is 0
            if page >= total_pages or not page_agents or page_agents[0].get("mindshare", 0) == 0:
                break
            page += 1

        return all_agents

    def get_top_agents(self, interval: str, k: int) -> List[dict]:
        agents = self.get_all_agents(interval)
        if not agents:
            return []
        
        # fillter agents with marketCap > 100000
        agents = [agent for agent in agents if agent.get("marketCap", 0) > 100000]
        
        avg_mindshare_ratio, avg_smart_followers_ratio, avg_holders_ratio = self._compute_average_ratios(agents)
        self._compute_raw_scores(agents, avg_mindshare_ratio, avg_smart_followers_ratio, avg_holders_ratio)
        self._normalize_agent_scores(agents)
        
        agents_sorted = sorted(agents, key=lambda x: x.get("finalScore", 0), reverse=True)
        return agents_sorted[:k]
    
    def _compute_average_ratios(self, agents: List[dict]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        mindshare_ratios = [safe_ratio(agent, "mindshare") for agent in agents if safe_ratio(agent, "mindshare") is not None]
        smart_followers_ratios = [safe_ratio(agent, "smartFollowersCount") for agent in agents if safe_ratio(agent, "smartFollowersCount") is not None]
        holders_ratios = [safe_ratio(agent, "holdersCount") for agent in agents if safe_ratio(agent, "holdersCount") is not None]
    
        avg_mindshare_ratio = sum(mindshare_ratios) / len(mindshare_ratios) if mindshare_ratios else None
        avg_smart_followers_ratio = sum(smart_followers_ratios) / len(smart_followers_ratios) if smart_followers_ratios else None
        avg_holders_ratio = sum(holders_ratios) / len(holders_ratios) if holders_ratios else None
    
        return avg_mindshare_ratio, avg_smart_followers_ratio, avg_holders_ratio
    
    def _compute_raw_scores(self, agents: List[dict],
                            avg_mindshare_ratio: Optional[float],
                            avg_smart_followers_ratio: Optional[float],
                            avg_holders_ratio: Optional[float]) -> None:
        for agent in agents:
            delta_ms = agent.get("mindshareDeltaPercent", 0)
            delta_vol = agent.get("volume24HoursDeltaPercent", 0)
            score_delta = delta_ms + delta_vol
            market_cap = agent.get("marketCap", 0)
    
            ms_score = compute_ratio_score(avg_mindshare_ratio, agent.get("mindshare", 0), market_cap)
            sf_score = compute_ratio_score(avg_smart_followers_ratio, agent.get("smartFollowersCount", 0), market_cap)
            hc_score = compute_ratio_score(avg_holders_ratio, agent.get("holdersCount", 0), market_cap)
    
            agent["ms_ratio_score"] = ms_score if ms_score is not None else 0
            agent["sf_ratio_score"] = sf_score if sf_score is not None else 0
            agent["hc_ratio_score"] = hc_score if hc_score is not None else 0
    
            available_scores = [score for score in (ms_score, sf_score, hc_score) if score is not None]
            pe_adjustment_score = sum(available_scores) / len(available_scores) if available_scores else 0
    
            agent["score_delta"] = score_delta
            agent["pe_adjustment_score"] = pe_adjustment_score
            agent["raw_final_score"] = score_delta + pe_adjustment_score
    
    def _normalize_agent_scores(self, agents: List[dict]) -> None:
        # Build lists for each component across all agents.
        mindshare_deltas = [agent.get("mindshareDeltaPercent", 0) for agent in agents]
        volume_deltas = [agent.get("volume24HoursDeltaPercent", 0) for agent in agents]
        ms_scores = [agent.get("ms_ratio_score", 0) for agent in agents]
        sf_scores = [agent.get("sf_ratio_score", 0) for agent in agents]
        hc_scores = [agent.get("hc_ratio_score", 0) for agent in agents]

        # Build a list for market cap values transformed by log (to compress range)
        market_caps_log = [np.log(agent.get("marketCap", 1)) for agent in agents]

        # Use your existing robust_normalize for delta components.
        for agent in agents:
            norm_mindshare = robust_normalize(agent.get("mindshareDeltaPercent", 0), mindshare_deltas)
            norm_volume = robust_normalize(agent.get("volume24HoursDeltaPercent", 0), volume_deltas)
            # Apply the log robust normalization for ratio scores.
            norm_ms = log_robust_normalize(agent.get("ms_ratio_score", 0), ms_scores)
            norm_sf = log_robust_normalize(agent.get("sf_ratio_score", 0), sf_scores)
            norm_hc = log_robust_normalize(agent.get("hc_ratio_score", 0), hc_scores)
            
            # Store normalized components.
            agent["norm_mindshareDeltaPercent"] = norm_mindshare
            agent["norm_volume24HoursDeltaPercent"] = norm_volume
            agent["norm_ms_ratio_score"] = norm_ms
            agent["norm_sf_ratio_score"] = norm_sf
            agent["norm_hc_ratio_score"] = norm_hc

            # Normalize market cap: using the logarithm ensures a more balanced scale.
            agent_market_cap_log = np.log(agent.get("marketCap", 1))
            norm_market_cap = robust_normalize(agent_market_cap_log, market_caps_log)*0.2

            # Compute the combined technical indicator score.
            tech_score = (norm_mindshare + norm_volume * 0.3 + norm_ms + norm_sf * 0.5 + norm_hc * 0.2 + norm_market_cap)/3
            agent["finalScore"] = tech_score 