from azure.ai.projects.models import AzureAISearchTool
from azure.ai.projects import AIProjectClient
from orch_config import *
from datetime import datetime
import os

def get_valuation_agent_instructions():
    dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(dir_path, 'instructions', 'valuation_agent_instructions.txt'), 'r', encoding='utf-8') as f:
        return f.read()

def create_valuation_agent(client: AIProjectClient, conn_id: str, index_name: str):
    tool = AzureAISearchTool(
        index_connection_id=conn_id,
        index_name=index_name
    )

    current_year = datetime.now().year

    agent = client.agents.create_agent(
        model="gpt-4o",
        name="valuation_agent",
        instructions=get_valuation_agent_instructions(),
        tools=tool.definitions,
        tool_resources=tool.resources
    )
    return agent
