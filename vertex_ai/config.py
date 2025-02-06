import os
from dotenv import load_dotenv
import vertexai

def init_vertex_ai():
    """
    Loads .env, sets up Vertex AI environment variables, and initializes Vertex.
    """
    load_dotenv()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    vertexai.init(project="naki-416814", location="us-central1")
