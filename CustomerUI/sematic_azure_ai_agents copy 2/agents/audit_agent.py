"""
Audit Agent creation function for Azure AI Semantic Kernel agents
"""

import json
import os
from azure.ai.agents.models import OpenApiAnonymousAuthDetails, OpenApiTool
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Agent Configuration
AGENT_NAME = "AuditAgent"

def get_agent_instructions():
    """Load agent instructions from external instructions file"""
    instructions_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        "instructions", 
        "audit_agent_instructions.txt"
    )
    try:
        with open(instructions_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Instructions file not found at {instructions_path}")
        return "You are an Audit Agent for managing loan processing audit records."


async def create_audit_agent(client):
    """Create an Azure AI Audit Agent with SQL-based audit capabilities."""
    
    try:
        # Load instructions from external file
        instructions = get_agent_instructions()
        
        # Load OpenAPI spec for audit API
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        audit_spec_path = os.path.join(current_dir, "audit_agent.json")
        
        with open(audit_spec_path, "r") as f:
            audit_api_spec = json.load(f)

        # Create OpenAPI tool for audit processing
        auth = OpenApiAnonymousAuthDetails()
        audit_api_tool = OpenApiTool(
            name="sql_audit_api",
            spec=audit_api_spec,
            description="SQL-based audit API for creating and retrieving loan processing audit records",
            auth=auth,
        )

        # Get agent settings
        ai_agent_settings = AzureAIAgentSettings()

        # Create agent definition with OpenAPI tools
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name=AGENT_NAME,
            instructions=instructions,
            tools=audit_api_tool.definitions,
        )

        # Create the AzureAI Agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        print(f"✅ {AGENT_NAME} created successfully!")
        return agent

    except Exception as e:
        print(f"❌ Error creating AuditAgent: {e}")
        return None
