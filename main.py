import json
import logging
import os
from fastapi import FastAPI, HTTPException, Header
from apscheduler.schedulers.background import BackgroundScheduler
from tools.cookie import CookieToolkit  # Adjust path as needed

# Pre-generated authentication token (adjust as needed)
AUTH_TOKEN = "vFZMxMy2BdsBY37rVd404uIuZpre3Txeprk7uD6KzdSlG7EbCBBisxZjr9W1JEU7"

# File path to save the JSON result
OUTPUT_FILE = "top_agents.json"

# Initialize CookieToolkit instance
cookie_toolkit = CookieToolkit()

def scan_top_agents():
    """
    Runs the scanning process to fetch the top agents and writes the result into a JSON file.
    """
    try:
        # Fetch top 10 agents based on mindshare and other data
        top_agents = cookie_toolkit.get_top_agents_by_mindshare(k=10)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(top_agents, f, indent=4)
        logging.info("Top agents updated successfully.")
    except Exception as e:
        logging.error(f"Error scanning top agents: {e}")

# Set up the scheduler to run scan_top_agents() every 10 minutes.
scheduler = BackgroundScheduler()
scheduler.add_job(scan_top_agents, 'interval', minutes=10)
scheduler.start()

# Optionally run one scan at startup.
scan_top_agents()

# Create FastAPI app instance.
app = FastAPI()

@app.get("/top-agents")
def read_top_agents(token: str = Header(...)):
    """
    GET endpoint to read the top agents saved in the JSON file.
    Requires a valid token in the request header.
    """
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    if not os.path.exists(OUTPUT_FILE):
        raise HTTPException(status_code=404, detail="Data not available")
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logging.error(f"Error reading top agents file: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
