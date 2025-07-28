"""
Agent creation function for LoanStatusCheckAgent
Enhanced audit and loan application status tracking agent
"""

import json
import os
from azure.ai.agents.models import OpenApiAnonymousAuthDetails, OpenApiTool
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

def get_agent_instructions():
    """Load agent instructions from external instructions file"""
    instructions_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        "instructions", 
        "loan_status_check_agent_instructions.txt"
    )
    try:
        with open(instructions_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Instructions file not found at {instructions_path}")
        return "You are a Loan Status Check Agent for tracking loan application status."


async def create_loan_status_check_agent(client):
    """
    Create an enhanced LoanStatusCheckAgent for comprehensive loan application tracking.
    
    This agent provides:
    - Username-first workflow: Ask for customer name, search by name to get customer_id
    - Clean status responses without stage numbers or technical jargon
    - Comprehensive loan application status summaries
    - Journey tracking across all stages (Prequalification → Approval)  
    - Simple failure analysis with brief reasons
    - Real-time status monitoring
    - Issue identification with minimal detail
    - Integration with both customer updates and audit APIs
    
    Features:
    - Uses audit API /api/users/search to find customer_id by name
    - Uses customer_updates API /logs/{customer_id} to get audit history
    - Provides clean, user-friendly status responses
    - No stage numbers mentioned to users
    - Brief failure summaries only when asked
    
    Args:
        client: Azure AI Agent client
        
    Returns:
        AzureAIAgent: Configured loan status check agent with dual API access
    """
    
    # Agent configuration
    AGENT_NAME = "LoanStatusCheckAgent"
    
    # Load instructions from external file
    AGENT_INSTRUCTIONS = get_agent_instructions()

    try:
        # Get current directory and construct paths to API spec files
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        customer_updates_json_path = os.path.join(current_dir, "customerupadtes.json")
        audit_agent_json_path = os.path.join(current_dir, "audit_agent.json")
        
        # Load OpenAPI specs for both APIs
        with open(customer_updates_json_path, "r") as f:
            customer_updates_api_spec = json.load(f)
            
        with open(audit_agent_json_path, "r") as f:
            audit_agent_api_spec = json.load(f)

        # Create OpenAPI tools for both APIs
        auth = OpenApiAnonymousAuthDetails()
        
        customer_updates_api_tool = OpenApiTool(
            name="customer_updates_processing_api",
            spec=customer_updates_api_spec,
            description="Customer Updates API for audit history retrieval using /logs/{customer_id} endpoint only",
            auth=auth,
        )
        
        audit_agent_api_tool = OpenApiTool(
            name="audit_agent_processing_api", 
            spec=audit_agent_api_spec,
            description="Audit Agent API for customer search by name using /api/users/search endpoint only",
            auth=auth,
        )

        # Initialize agent settings
        ai_agent_settings = AzureAIAgentSettings()

        # Create agent definition with both OpenAPI tools
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
            tools=customer_updates_api_tool.definitions + audit_agent_api_tool.definitions,
        )

        # Create the AzureAI Agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        print(f"✅ {AGENT_NAME} created successfully with dual API processing capabilities!")
        print("   🔍 Audit API: Customer search by name")
        print("   📋 Customer Updates API: Audit history retrieval")
        return agent

    except Exception as e:
        print(f"❌ Error creating {AGENT_NAME}: {str(e)}")
        raise e
