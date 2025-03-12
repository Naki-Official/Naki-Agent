import json
import logging
import os
from fastapi import FastAPI, HTTPException, Header
from apscheduler.schedulers.background import BackgroundScheduler
import uvicorn

# Import your CookieToolkit from your project
from tools.cookie import CookieToolkit

# Pre-generated API key (adjust as needed)
API_KEY = "vFZMxMy2BdsBY37rVd404uIuZpre3Txeprk7uD6KzdSlG7EbCBBisxZjr9W1JEU7"

# File path to save the JSON result
OUTPUT_FILE = "top_agents.json"

# Initialize CookieToolkit instance
cookie_toolkit = CookieToolkit()

def scan_top_agents():
    """
    Fetch the top 10 agents using the CookieToolkit and write them to a JSON file.
    """
    try:
        top_agents = cookie_toolkit.get_top_agents_by_mindshare(k=10)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(top_agents, f, indent=4)
        print("Top agents updated successfully.")
    except Exception as e:
        print(f"Error scanning top agents: {e}")

# Set up the scheduler to run the scan job every 10 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(scan_top_agents, 'interval', minutes=15)

# Create FastAPI app instance.
app = FastAPI()

@app.get("/api/top-agents")
def read_top_agents(x_api_key: str = Header(...)):
    """
    GET endpoint to read the top agents saved in the JSON file.
    Requires a valid API key in the 'x-api-key' header.
    """
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if not os.path.exists(OUTPUT_FILE):
        raise HTTPException(status_code=404, detail="Data not available")
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logging.error(f"Error reading top agents file: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    scheduler.start()
    # Start the FastAPI server using uvicorn.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
