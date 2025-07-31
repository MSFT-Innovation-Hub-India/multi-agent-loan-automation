import os
from dotenv import load_dotenv

load_dotenv()

# Azure AI endpoints and keys
AZURE_AI_ENDPOINT = os.getenv("AZURE_AI_ENDPOINT")
AZURE_AI_API_VERSION = os.getenv("AZURE_AI_API_VERSION", "2023-05-15")
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("SEARCH_KEY")
INDEX_NAME = os.getenv("INDEX_NAME", "default-index")

# Validate required environment variables
required_env_vars = ["AZURE_AI_ENDPOINT", "SEARCH_ENDPOINT", "SEARCH_KEY"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    import sys
    print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    print("Please check your .env file and ensure all required variables are set.")
    print("Copy .env.example to .env and fill in your Azure credentials.")
    sys.exit(1)
