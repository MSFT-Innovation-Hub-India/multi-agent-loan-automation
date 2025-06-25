from azure.ai.projects.models import AzureAISearchTool
from azure.ai.projects import AIProjectClient
from config import *
import os

def get_income_instructions():
    dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(dir_path, 'instructions', 'income_instructions.txt'), 'r', encoding='utf-8') as f:
        return f.read()

def create_income_agent(client: AIProjectClient, conn_id: str, index_name: str):
    # Define Azure AI Search tool
    tool = AzureAISearchTool(
        index_connection_id=conn_id,
        index_name=index_name
    )

    # Create the income verification agent
    agent = client.agents.create_agent(
        model="gpt-4o",
        name="income_checker",
        instructions=get_income_instructions(),
        tools=tool.definitions,
        tool_resources=tool.resources
    )

    return agent