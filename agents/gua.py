from azure.ai.projects.models import AzureAISearchTool
from azure.ai.projects import AIProjectClient
from config import *
import os

def get_gua_instructions():
    dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(dir_path, 'instructions', 'gua_instructions.txt'), 'r', encoding='utf-8') as f:
        return f.read()

def create_guarantor_agent(client: AIProjectClient, conn_id: str, index_name: str):
    tool = AzureAISearchTool(
        index_connection_id=conn_id,
        index_name=index_name
    )

    agent = client.agents.create_agent(
        model="gpt-4o",
        name="guarantor_evaluator",
        instructions=get_gua_instructions(),
        tools=tool.definitions,
        tool_resources=tool.resources
    )
    return agent