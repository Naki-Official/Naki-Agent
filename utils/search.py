import os
from dotenv import load_dotenv
# Load the environment variables
load_dotenv()


# Set the environment variable for the Google Cloud credentials
os.environ["GOOGLE_API_KEY"] = os.getenv('GOOGLE_API_KEY')
os.environ["GOOGLE_CSE_ID"] = os.getenv('GOOGLE_CSE_ID')

from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_core.tools import Tool

gg_search = GoogleSearchAPIWrapper()

tool = Tool(
    name="google_search",
    description="Search Google for recent results.",
    func=gg_search.run,
)

def search(keyword_search):
    result = tool.run(keyword_search)
    return result