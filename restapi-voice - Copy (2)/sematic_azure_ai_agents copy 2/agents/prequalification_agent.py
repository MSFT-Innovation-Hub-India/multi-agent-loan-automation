"""
Prequalification Agent Creation Function for Semantic Kernel Azure AI Agents
"""

import json
import os
from azure.ai.agents.models import OpenApiAnonymousAuthDetails, OpenApiTool
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Agent Configuration
AGENT_NAME = "PrequalificationAgent"

def get_agent_instructions():
    """Load agent instructions from external instructions file"""
    instructions_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        "instructions", 
        "prequalification_agent_instructions.txt"
    )
    try:
        with open(instructions_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Instructions file not found at {instructions_path}")
        return "You are a Prequalification Agent for checking loan eligibility."


async def create_prequalification_agent(client):
    """Create a Prequalification Agent with OpenAPI tools"""
    
    # Load instructions from external file
    instructions = get_agent_instructions()
    
    # Get agent settings
    ai_agent_settings = AzureAIAgentSettings()
    
    # Load OpenAPI tools
    tools = []
    swagger_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "swagger.json")
    if os.path.exists(swagger_path):
        with open(swagger_path, "r") as f:
            prequalification_spec = json.load(f)
        
        auth = OpenApiAnonymousAuthDetails()
        prequalification_tool = OpenApiTool(
            name="prequalification_api",
            spec=prequalification_spec,
            description="API for loan prequalification including customer search, eligibility check, and loan discovery",
            auth=auth,
        )
        tools = prequalification_tool.definitions
    
    # Create agent definition
    agent_definition = await client.agents.create_agent(
        model=ai_agent_settings.model_deployment_name,
        name=AGENT_NAME,
        instructions=instructions,
        tools=tools,
    )
    
    # Create the AzureAI Agent
    agent = AzureAIAgent(
        client=client,
        definition=agent_definition,
    )
    
    return agent
