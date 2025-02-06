from tools.cookie import CookieToolkit
from datetime import datetime,timedelta
import os
from dotenv import load_dotenv
# Load the environment variables
load_dotenv()
COOKIE_API_KEY = os.getenv("COOKIE_API_KEY")

# Replace 'your_api_key_here' with your actual API key
cookie_toolkit = CookieToolkit(api_key=COOKIE_API_KEY)

# Example: Get top 20 promising agents based on the scoring system
top_agents_result = cookie_toolkit.get_top_agents("_3Days",3)
print("\nTop 20 Agents:")
# print top 20 agents with json beautify
import json
print(json.dumps(top_agents_result, indent=4, sort_keys=True))

top_1_agent = top_agents_result[0]
contract_address = ""
token_contracts = top_1_agent.get("contracts", [])
for contract in token_contracts:
    chain = contract.get("chain", "")
    if chain == -2:
        contract_address = contract.get("contractAddress", "")
        break
print("\nContract Address:")
print(contract_address)
token_data = top_1_agent

from tools.dexscreener import DexscreenerToolkit

# Initialize the Dexscreener Toolkit.
dexscreener_toolkit = DexscreenerToolkit()

# # Example: Search for token pairs by token symbol.
token_infor = dexscreener_toolkit.search_by_address(contract_address)
end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
x_content = cookie_toolkit.search_tweets(token_infor.get("baseToken", {}).get("name", ""), start_date, end_date)
token_infor["x_content"] = x_content
print(x_content)
print("\nSearch by Token:")
print(token_infor)
# merge token data
token_data = {**token_data, **token_infor}

token_symbol = token_infor.get("baseToken", {}).get("symbol", "")

from analysis.ta import TechnicalAnalysis

COMPARE_CRYPTO_API_KEY = os.getenv("COMPARE_CRYPTO_API_KEY")
# # Initialize the technical analysis toolkit.
ta_toolkit = TechnicalAnalysis(COMPARE_CRYPTO_API_KEY=COMPARE_CRYPTO_API_KEY)

analysis_report = ta_toolkit.comprehensive_ta_analysis(from_symbol=token_symbol, to_symbol="USDT")
print("Comprehensive TA Analysis Report:")
print(analysis_report)

recommendation = analysis_report.get("recommendation", "")

if recommendation == "LONG" or recommendation == "SHORT":
    print("\nRecommendation:")
    print(analysis_report.get("recommendation", ""))

from pipeline.token_summary import get_token_summary

# # Example: Get token summary

token_summary= get_token_summary(token_data)
print("\nToken Summary:")
print(token_summary)
token_data["token_summary"] = token_summary

from pipeline.tweet_generation import generate_tweet

# # Example: Generate a tweet
tweet = generate_tweet(token_data, top_1_agent, analysis_report,recommendation)
print("\nGenerated Tweet:")
print(tweet)

# send_telegram_message(result_str)



# from scheduler.coin_discovery_scheduler import CoinDiscoveryScheduler

# # Create an instance of the scheduler.
# scheduler = CoinDiscoveryScheduler(api_key=API_KEY, interval="_7Days", top_k=10)
# # Start the scheduling loop.
# scheduler.start()