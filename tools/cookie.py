import json
import logging
import numpy as np
from typing import List, Tuple, Optional
import urllib.parse
import cloudscraper
import requests
from pycoingecko import CoinGeckoAPI

from utils.util import safe_ratio, compute_ratio_score, log_robust_normalize, robust_normalize

# Initialize CoinGecko API client
cg = CoinGeckoAPI()

def _format_token_data(token: dict) -> dict:
    """
    Helper function to format token data into a human-readable summary.
    """
    symbol = token.get("symbol", "").upper()
    name = token.get("name", "")
    categories = token.get("categories", [])
    twitter_acc = token.get("links", {}).get("twitter_screen_name", "N/A")
    sentiment_votes_up = token.get("sentiment_votes_up_percentage", "N/A")
    sentiment_votes_down = token.get("sentiment_votes_down_percentage", "N/A")
    watchlist_users = token.get("watchlist_portfolio_users", "N/A")
    market_cap_rank = token.get("market_cap_rank", "N/A")
    description = token.get("description", {}).get("en", "N/A")

    market_data = token.get("market_data", {})
    current_price = market_data.get("current_price", {}).get("usd", "N/A")
    ath = market_data.get("ath", {}).get("usd", "N/A")
    ath_change_percentage = market_data.get("ath_change_percentage", {}).get("usd", "N/A")
    atl = market_data.get("atl", {}).get("usd", "N/A")
    atl_change_percentage = market_data.get("atl_change_percentage", {}).get("usd", "N/A")
    market_cap = market_data.get("market_cap", {}).get("usd", "N/A")
    total_volume = market_data.get("total_volume", {}).get("usd", "N/A")
    high_24h = market_data.get("high_24h", {}).get("usd", "N/A")
    low_24h = market_data.get("low_24h", {}).get("usd", "N/A")
    price_change_24h = market_data.get("price_change_24h", "N/A")
    price_change_percentage_24h = market_data.get("price_change_percentage_24h", "N/A")
    price_change_percentage_7d = market_data.get("price_change_percentage_7d", "N/A")
    price_change_percentage_14d = market_data.get("price_change_percentage_14d", "N/A")
    price_change_percentage_30d = market_data.get("price_change_percentage_30d", "N/A")
    price_change_percentage_60d = market_data.get("price_change_percentage_60d", "N/A")

    return {
        "symbol": symbol,
        "name": name,
        "categories": categories,
        "twitter_acc": twitter_acc,
        "sentiment_votes_up": sentiment_votes_up,
        "sentiment_votes_down": sentiment_votes_down,
        "watchlist_users": watchlist_users,
        "market_cap_rank": market_cap_rank,
        "description": description,
        "current_price": current_price,
        "ath": ath,
        "ath_change_percentage": ath_change_percentage,
        "atl": atl,
        "atl_change_percentage": atl_change_percentage,
        "market_cap": market_cap,
        "total_volume": total_volume,
        "high_24h": high_24h,
        "low_24h": low_24h,
        "price_change_24h": price_change_24h,
        "price_change_percentage_24h": price_change_percentage_24h,
        "price_change_percentage_7d": price_change_percentage_7d,
        "price_change_percentage_14d": price_change_percentage_14d,
        "price_change_percentage_30d": price_change_percentage_30d,
        "price_change_percentage_60d": price_change_percentage_60d,
    }

def search_by_address(token_address: str) -> Optional[dict]:
    """
    Search for a token by contract address using CoinGecko's search_v2 API.
    If no token is found, returns None.
    """
    try:
        url = f"https://www.coingecko.com/en/search_v2?query={token_address}&vs_currency=usd"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        coins = data.get("coins", [])
        if not coins:
            return None
        
        coin_id = coins[0].get("id")
        if not coin_id:
            return None
        
        token_data = cg.get_coin_by_id(coin_id)
        return _format_token_data(token_data)
    except Exception as e:
        logging.error(f"Error in search_by_address: {e}")
        return None

class CookieToolkit():
    """
    The CookieToolkit class provides methods to interact with the Cookie APIs.
    It offers endpoints to retrieve agent details, fetch a paged list of agents, and search for tweets.
    """
    def _request_full_url(self, url: str) -> str:
        """
        Perform a GET request with a full URL using cloudscraper to bypass Cloudflare.
        """
        try:
            print(f"Requesting URL: {url}")
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return json.dumps({"ok": data, "success": True, "error": None})
                elif isinstance(data, dict) and data.get("success") is True:
                    return json.dumps({"ok": data.get("ok"), "success": True, "error": None})
                else:
                    error_msg = data.get("error") if isinstance(data, dict) else "Invalid response format"
                    return json.dumps({"ok": None, "success": False, "error": error_msg})
            else:
                print(response.text)
                raise Exception(response.text)
        except Exception as e:
            logging.error(f"Error in _request_full_url: {e}")
            return json.dumps({"ok": None, "success": False, "error": str(e)})
    
    def get_agents_table_details(self, page: int = 1, limit: int = 50) -> List[dict]:
        """
        Retrieve detailed agent data from the new endpoint.
        """
        payload = {
            "0": {
                "json": {
                    "page": page,
                    "limit": limit,
                    "orderColumn": "TwitterMindshareDelta",
                    "orderByAscending": False,
                    "orderDataPoint": "_3DaysAgo",
                    "tags": [],
                    "projectsFilter": {
                        "blockchainFilter": {"chains": []},
                        "categoriesFilter": {"values": []},
                        "creationDateFilter": None,
                        "frameworkFilter": {"values": []},
                        "metricFilters": [],
                        "projectTypeFilter": {"values": []},
                        "searchFilter": "",
                        "tagsFilter": {"values": []}
                    },
                    "isWatchlist": False
                }
            }
        }
        input_param = urllib.parse.quote(json.dumps(payload))
        url = f"https://www.cookie.fun/api/trpc/agents.getAgentsTableDetails?batch=1&input={input_param}"
        response_str = self._request_full_url(url)
        response_json = json.loads(response_str)
        if response_json.get("success") is not True:
            return []
        try:
            projects = response_json["ok"][0]["result"]["data"]["json"]["projects"]
            return projects
        except Exception as e:
            logging.error(f"Error parsing agents table details: {e}")
            return []
    
    def get_top_agents_by_mindshare(self, k: int) -> List[dict]:
        """
        Retrieve the top k agents based on finalScore.
        First, compute finalScore for all agents using on-chain and social data.
        Then, iterate through agents sorted by finalScore descending and call the CoinGecko API
        to fetch token info—appending token info only when a token is found.
        Stop once k tokens have been collected.
        The entryPrice and takeProfit are determined based on CoinGecko price, volatility,
        and the average normalized ratio score.
        """
        # Phase 1: Compute finalScore for all agents without calling CoinGecko.
        projects = self.get_agents_table_details(page=1, limit=50)
        agents = []
        for proj in projects:
            try:
                agent = {}
                details = proj.get("agentDetails", {})
                agent["name"] = details.get("name")
                agent["slug"] = details.get("slug")
                agent["ticker"] = proj.get("ticker")
                agent["creationDate"] = proj.get("creationDate")
                agent["profileImageUrl"] = proj.get("profileImageUrl")
                contracts = details.get("contracts", [])
                agent["contractAddress"] = contracts[0].get("contractAddress") if contracts else None
                # On-chain stats ("Now")
                on_chain = proj.get("onChainStats", {}).get("dataPoints", {}).get("Now", {})
                agent["marketCap"] = on_chain.get("tokenMarketCap", {}).get("value", 0)
                agent["holdersCount"] = on_chain.get("tokenHoldersCount", {}).get("value", 0)
                token_price_now = on_chain.get("tokenPrice", {}).get("value", 0)
                agent["tokenPrice"] = token_price_now
                # Historical token price ("_3DaysAgo")
                on_chain_3days = proj.get("onChainStats", {}).get("dataPoints", {}).get("_3DaysAgo", {})
                token_price_3days = on_chain_3days.get("tokenPrice", {}).get("value", 0)
                agent["tokenPrice3DaysAgo"] = token_price_3days
                if token_price_3days > 0:
                    agent["tokenPriceChangePercent"] = (token_price_now - token_price_3days) / token_price_3days * 100
                else:
                    agent["tokenPriceChangePercent"] = 0
                # Twitter stats
                twitter_now = proj.get("twitterStats", {}).get("dataPoints", {}).get("Now", {})
                agent["smartFollowersCount"] = twitter_now.get("smartFollowersCount", {}).get("value", 0)
                twitter_3days = proj.get("twitterStats", {}).get("dataPoints", {}).get("_3DaysAgo", {})
                mindshare_info = twitter_3days.get("mindshare", {})
                current_mindshare = mindshare_info.get("value", 0)
                previous_mindshare = mindshare_info.get("previousValue", 0)
                agent["mindshare"] = current_mindshare
                agent["mindsharePrevious"] = previous_mindshare
                if previous_mindshare and previous_mindshare > 0:
                    agent["mindshareDelta"] = current_mindshare - previous_mindshare
                    agent["mindshareDeltaPercent"] = (current_mindshare - previous_mindshare) / previous_mindshare * 100
                else:
                    agent["mindshareDelta"] = 0
                    agent["mindshareDeltaPercent"] = 0
                agent["volume24HoursDeltaPercent"] = 0
                agents.append(agent)
            except Exception as e:
                logging.error(f"Error processing project data: {e}")
                continue
        
        # Filter out agents with too small market cap.
        agents = [agent for agent in agents if agent.get("marketCap", 0) > 100000]
        
        # Compute scoring metrics.
        avg_mindshare_ratio, avg_smart_followers_ratio, avg_holders_ratio = self._compute_average_ratios(agents)
        self._compute_raw_scores(agents, avg_mindshare_ratio, avg_smart_followers_ratio, avg_holders_ratio)
        self._normalize_agent_scores(agents)
        
        agents_sorted = sorted(agents, key=lambda x: x.get("finalScore", 0), reverse=True)
        
        # Phase 2: Iterate over sorted agents and call CoinGecko API until we have k tokens.
        result_tokens = []
        for agent in agents_sorted:
            if not agent.get("contractAddress"):
                continue
            token_data = search_by_address(agent["contractAddress"])
            if not token_data:
                continue  # Skip if no CoinGecko data is found.
            
            # Use CoinGecko data for current price and volatility.
            cg_price = token_data.get("current_price", agent.get("tokenPrice", 0))
            volatility = token_data.get("price_change_percentage_24h", 0) / 100.0
            # Compute average normalized ratio score using norm_ms_ratio, norm_sf_ratio, norm_hc_ratio.
            total_ratio_score = (
                agent.get("norm_ms_ratio_score", 0) +
                agent.get("norm_sf_ratio_score", 0) +
                agent.get("norm_hc_ratio_score", 0)
            ) / 3
            # Compute discount and profit target.
            base_discount = 0.05       # 5% baseline discount.
            base_profit_target = 0.15    # 15% baseline profit target.
            discount = base_discount + volatility * 1.0  # Do not use ratio score for discount.
            profit_target = base_profit_target + volatility * 2.0 + total_ratio_score * 0.02
            # Clamp discount to [1%, 10%] and profit target to [50%, 300%].
            discount = max(0.01, min(discount, 0.10))
            profit_target = max(0.50, min(profit_target, 3.00))
            entry_price = cg_price * (1 - discount)
            take_profit = cg_price * (1 + profit_target)
            
            token_info = {
                "name": agent.get("name"),
                "slug": agent.get("slug"),
                "ticker": agent.get("ticker"),
                "creationDate": agent.get("creationDate"),
                "profileImageUrl": agent.get("profileImageUrl"),
                "contractAddress": agent.get("contractAddress"),
                "marketCap": agent.get("marketCap"),
                "holdersCount": agent.get("holdersCount"),
                "tokenPrice": agent.get("tokenPrice"),
                "tokenPrice3DaysAgo": agent.get("tokenPrice3DaysAgo"),
                "tokenPriceChangePercent": agent.get("tokenPriceChangePercent"),
                "smartFollowersCount": agent.get("smartFollowersCount"),
                "mindshare": agent.get("mindshare"),
                "mindsharePrevious": agent.get("mindsharePrevious"),
                "mindshareDelta": agent.get("mindshareDelta"),
                "mindshareDeltaPercent": agent.get("mindshareDeltaPercent"),
                "volume24HoursDeltaPercent": agent.get("volume24HoursDeltaPercent"),
                "entryPrice": entry_price,
                "takeProfit": take_profit,
                "coinGeckoData": token_data
            }
            formatted_agent = {
                "finalScore": agent.get("finalScore"),
                "token": token_info
            }
            result_tokens.append(formatted_agent)
            if len(result_tokens) >= k:
                break
        
        return result_tokens

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
            if "mindshareDeltaPercent" not in agent:
                prev = agent.get("mindsharePrevious", 0)
                if prev > 0:
                    agent["mindshareDeltaPercent"] = (agent.get("mindshare", 0) - prev) / prev * 100
                else:
                    agent["mindshareDeltaPercent"] = 0
            
            delta_ms = agent.get("mindshareDeltaPercent", 0)
            delta_vol = agent.get("volume24HoursDeltaPercent", 0)
            score_delta = delta_ms + delta_vol
            market_cap = agent.get("marketCap", 0)
            mindshare = agent.get("mindshare", 0)
    
            ms_score = compute_ratio_score(avg_mindshare_ratio, mindshare, market_cap)
            sf_score = compute_ratio_score(avg_smart_followers_ratio, agent.get("smartFollowersCount", 0), market_cap)
            hc_score = compute_ratio_score(avg_holders_ratio, agent.get("holdersCount", 0), market_cap)
    
            agent["ms_ratio_score"] = ms_score if ms_score is not None else 0
            agent["sf_ratio_score"] = sf_score if sf_score is not None else 0
            agent["hc_ratio_score"] = hc_score if hc_score is not None else 0
    
            agent["avg_mindshare_ratio"] = avg_mindshare_ratio
            if mindshare > 0:
                agent["mindshare_ratio"] = market_cap / mindshare
            else:
                agent["mindshare_ratio"] = 0
                
            available_scores = [score for score in (ms_score, sf_score, hc_score) if score is not None]
            pe_adjustment_score = sum(available_scores) / len(available_scores) if available_scores else 0
    
            agent["score_delta"] = score_delta
            agent["pe_adjustment_score"] = pe_adjustment_score
            agent["raw_final_score"] = score_delta + pe_adjustment_score
    
    def _normalize_agent_scores(self, agents: List[dict]) -> None:
        mindshare_deltas = [agent.get("mindshareDeltaPercent", 0) for agent in agents]
        volume_deltas = [agent.get("volume24HoursDeltaPercent", 0) for agent in agents]
        ms_scores = [agent.get("ms_ratio_score", 0) for agent in agents]
        sf_scores = [agent.get("sf_ratio_score", 0) for agent in agents]
        hc_scores = [agent.get("hc_ratio_score", 0) for agent in agents]
        mindshares = [agent.get("mindshare", 0) for agent in agents]
    
        for agent in agents:
            norm_mindshare = robust_normalize(agent.get("mindshareDeltaPercent", 0), mindshare_deltas)
            norm_volume = robust_normalize(agent.get("volume24HoursDeltaPercent", 0), volume_deltas)
            norm_ms_ratio = log_robust_normalize(agent.get("ms_ratio_score", 0), ms_scores)
            norm_sf_ratio = log_robust_normalize(agent.get("sf_ratio_score", 0), sf_scores)
            norm_hc_ratio = log_robust_normalize(agent.get("hc_ratio_score", 0), hc_scores)
            norm_ms = log_robust_normalize(agent.get("mindshare", 0), mindshares)
    
            agent["norm_mindshareDeltaPercent"] = norm_mindshare
            agent["norm_volume24HoursDeltaPercent"] = norm_volume
            agent["norm_ms_ratio_score"] = norm_ms_ratio
            agent["norm_sf_ratio_score"] = norm_sf_ratio
            agent["norm_hc_ratio_score"] = norm_hc_ratio
            agent["norm_ms"] = norm_ms
    
            tech_score = norm_ms + norm_mindshare + norm_volume * 0.3 + norm_ms_ratio + norm_sf_ratio * 0.5 + norm_hc_ratio * 0.2 
            agent["finalScore"] = tech_score
