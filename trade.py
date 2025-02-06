
"""
trade.py

This module orchestrates the pipeline for selecting top tokens,
filtering by recent tweet history, analyzing them, and generating
tweets for LONG or SHORT recommendations.
"""

import os
import logging
import schedule
import time
from datetime import datetime, timedelta

from dotenv import load_dotenv

# External imports (adjust your paths as needed)
from tools.cookie import CookieToolkit
from tools.dexscreener import DexscreenerToolkit
from analysis.ta import TechnicalAnalysis
from pipeline.token_summary import get_token_summary
from pipeline.tweet_generation import generate_tweet
from services.telebot import send_telegram_message

# Optional: If you use MongoDB for storing tweet records
from pymongo import MongoClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Adjust level to DEBUG, INFO, WARNING, etc.
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_mongo_collection() -> "Collection":
    """
    Connect to MongoDB and return a reference to the collection
    tracking tweets or tokens.

    Replace with your actual MongoDB URI, database, and collection.
    """
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    client = MongoClient(mongo_uri)
    db_name = os.getenv("MONGO_DB", "token_db")
    coll_name = os.getenv("MONGO_COLL", "tweet_history")
    db = client[db_name]
    return db[coll_name]


def has_recent_tweet(contract_address: str, recent_hours: int = 6) -> bool:
    """
    Check in MongoDB if this contract has been tweeted about in the last 'recent_hours'.
    """
    coll = get_mongo_collection()
    cutoff_time = datetime.utcnow() - timedelta(hours=recent_hours)
    record = coll.find_one({
        "contractAddress": contract_address,
        "tweetedAt": {"$gte": cutoff_time}
    })
    return record is not None


def record_tweet_in_db(contract_address: str, tweet_text: str):
    """
    Save the fact that we tweeted about this contractAddress at the current time.
    """
    coll = get_mongo_collection()
    coll.insert_one({
        "contractAddress": contract_address,
        "tweetedAt": datetime.utcnow(),
        "tweetText": tweet_text
    })


def run_trade_pipeline():
    """
    1) Fetch top 5 tokens from Cookie
    2) Filter out tokens that were tweeted about within the last 6 hours
    3) For each remaining token:
       a) Gather DexScreener info
       b) Perform TA
       c) If TA recommends LONG or SHORT:
          - Summarize token
          - Generate tweet
          - (Optional) Send tweet or store in DB
    """

    load_dotenv()
    COOKIE_API_KEY = os.getenv("COOKIE_API_KEY", "")
    COMPARE_CRYPTO_API_KEY = os.getenv("COMPARE_CRYPTO_API_KEY", "")

    # Initialize Cookie toolkit
    cookie_toolkit = CookieToolkit(api_key=COOKIE_API_KEY)
    # DexScreener
    dexscreener_toolkit = DexscreenerToolkit()
    # TA
    ta_toolkit = TechnicalAnalysis(COMPARE_CRYPTO_API_KEY=COMPARE_CRYPTO_API_KEY)

    # 1) Get top 20 agents from cookie
    top_agents = cookie_toolkit.get_top_agents("_3Days", k=20)
    logger.info(f"Top {len(top_agents)} agents fetched.")

    for agent in top_agents:
        try:
            # Extract a contract address (chain == -2)
            contract_address = ""
            token_contracts = agent.get("contracts", [])
            for c in token_contracts:
                if c.get("chain", "") == -2:
                    contract_address = c.get("contractAddress", "")
                    break

            # 2) Skip if we already tweeted about this contract in last 6 hours
            if not contract_address:
                logger.info("No relevant contractAddress found; skipping agent.")
                continue

            if has_recent_tweet(contract_address):
                logger.info(f"Skipping {contract_address}; recent tweet found.")
                continue

            logger.info(f"Processing contract {contract_address}...")

            # 3a) Gather DexScreener info
            token_info = dexscreener_toolkit.search_by_address(contract_address)
            # Optionally add additional searching logic if needed
            # e.g. Searching tweets from X, etc.

            # Merge cookie data + DexScreener data
            token_data = {**agent, **token_info}

            # 3b) Perform TA using the symbol from DexScreener (or fallback to agent name)
            base_token = token_info.get("baseToken", {})
            symbol = base_token.get("symbol", "") or agent.get("agentName", "N/A")
            analysis_report = ta_toolkit.comprehensive_ta_analysis(
                from_symbol=symbol,
                to_symbol="USDT"  # or "USD" depending on your data
            )

            if not analysis_report:
                logger.error(f"No TA analysis found for {symbol}; skipping.")
                continue

            recommendation = analysis_report.get("recommendation", "")
            logger.info(f"TA recommendation for {symbol} = {recommendation}")

            # 3c) Generate tweet only if LONG or SHORT
            if recommendation in ("LONG", "SHORT"):
                entry_price = analysis_report.get("suggested_trade", {}).get("entry", 0)
                token_price = token_info.get("priceUsd", 0)
                # convert to float
                entry_price = float(entry_price)
                token_price = float(token_price)
                if abs(entry_price - token_price) / token_price > 0.2:
                    logger.info(f"Entry price {entry_price} differs significantly from token price {token_price}; skipping.")
                    continue
                # Summarize token
                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                x_content = cookie_toolkit.search_tweets(token_data.get("baseToken", {}).get("name", ""), start_date, end_date)
                token_data["x_content"] = x_content
                token_summary = get_token_summary(token_data)
                token_data["token_summary"] = token_summary

                # Generate tweet
                tweet_text = generate_tweet(token_data, agent, analysis_report, recommendation)

                # Record or send the tweet
                logger.info(f"\nGenerated Tweet for {symbol}:\n{tweet_text}\n")

                # Save tweet in DB to avoid re-tweeting within 6h
                record_tweet_in_db(contract_address, tweet_text)

                # Send tweet to Telegram or other service
                send_telegram_message(tweet_text)

            else:
                logger.info(f"Recommendation is {recommendation}; skipping tweet generation.")
        except Exception as e:
            logger.error(f"Error processing agent {agent.get('agentName', 'N/A')}: {e}")

    logger.info("Trade pipeline completed.")


if __name__ == "__main__":
    print("Starting CoinDiscoveryScheduler...")
    schedule.every(10).minutes.do(run_trade_pipeline)
    # Optionally run an initial search immediately.
    run_trade_pipeline()
    while True:
        schedule.run_pending()
        time.sleep(1)
