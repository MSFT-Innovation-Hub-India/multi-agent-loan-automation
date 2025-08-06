"""
Application Assist Agent Creation Function for Semantic Kernel Azure AI Agents
"""

import json
import os
from azure.ai.agents.models import OpenApiAnonymousAuthDetails, OpenApiTool
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Agent Configuration
AGENT_NAME = "ApplicationAssistAgent"

def get_agent_instructions():
    """Load agent instructions from external instructions file"""
    instructions_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        "instructions", 
        "application_assist_agent_instructions.txt"
    )
    try:
        with open(instructions_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Instructions file not found at {instructions_path}")
        return "You are an Application Assist Agent for loan processing."


async def create_application_assist_agent(client):
    """Create an Application Assist Agent with OpenAPI tools"""
    
    # Load instructions from external file
    instructions = get_agent_instructions()
    
    # Get agent settings
    ai_agent_settings = AzureAIAgentSettings()
    
    # Load OpenAPI tools
    tools = []
    
    # Load loan processing API
    swagger_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app_swagger.json")
    if os.path.exists(swagger_path):
        with open(swagger_path, "r") as f:
            application_spec = json.load(f)
        
        auth = OpenApiAnonymousAuthDetails()
        application_tool = OpenApiTool(
            name="loan_processing_api",
            spec=application_spec,
            description="API for loan processing including personal details, employment details, and loan information",
            auth=auth,
        )
        tools = tools + application_tool.definitions
    
    # Load audit logging API
    audit_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "customerupadtes.json")
    if os.path.exists(audit_path):
        with open(audit_path, "r") as f:
            audit_spec = json.load(f)
        
        auth = OpenApiAnonymousAuthDetails()
        audit_tool = OpenApiTool(
            name="audit_logging_api",
            spec=audit_spec,
            description="API for creating audit logs and tracking agent activities",
            auth=auth,
        )
        tools = tools + audit_tool.definitions
    
    # Load customer updates API
    customer_updates_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "customerupadtes.json")
    if os.path.exists(customer_updates_path):
        with open(customer_updates_path, "r") as f:
            customer_updates_spec = json.load(f)
        
        auth = OpenApiAnonymousAuthDetails()
        customer_updates_tool = OpenApiTool(
            name="customer_updates_api",
            spec=customer_updates_spec,
            description="API for updating customer progress and agent completion status throughout the loan process",
            auth=auth,
        )
        tools = tools + customer_updates_tool.definitions
    
    # Load audit agent API for customer search by name
    audit_agent_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audit_agent.json")
    if os.path.exists(audit_agent_path):
        with open(audit_agent_path, "r") as f:
            audit_agent_spec = json.load(f)
        
        auth = OpenApiAnonymousAuthDetails()
        audit_agent_tool = OpenApiTool(
            name="audit_agent_api",
            spec=audit_agent_spec,
            description="API for customer search by name using /api/users/search endpoint",
            auth=auth,
        )
        tools = tools + audit_agent_tool.definitions
    
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
