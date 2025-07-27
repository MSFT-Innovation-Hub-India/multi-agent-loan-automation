import os
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
RESOURCE_GROUP = os.getenv("AZURE_AI_RESOURCE_GROUP")
SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
PROJECT_NAME = os.getenv("AZURE_PROJECT_NAME")