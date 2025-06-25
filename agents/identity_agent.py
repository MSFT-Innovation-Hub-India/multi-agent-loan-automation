from azure.ai.projects.models import AzureAISearchTool
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
import sys
import os

# Import config variables
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

def get_identity_instructions():
    dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(dir_path, 'instructions', 'identity_instructions.txt'), 'r', encoding='utf-8') as f:
        return f.read()

def create_identity_agent(client, conn_id, index_name):
    # Define search tool pointing to your AI Search index
    tool = AzureAISearchTool(
        index_connection_id=conn_id,
        index_name=index_name
    )

    # Create identity verification agent
    agent = client.agents.create_agent(
        model="gpt-4o",
        name="identity_checker",
        instructions=get_identity_instructions(),
        tools=tool.definitions,
        tool_resources=tool.resources
    )

    return agent