"""
Custom Agent Tools Module for Loan Application Processing

This module contains tool definitions that can be used by the AI agent to perform
specific operations related to loan applications, such as submitting new applications
and checking application status through Logic Apps.

Each tool has:
1. A clear schema definition that describes required parameters
2. Instructions for the agent on when and how to use the tool
3. A reference to the actual function implementation that performs the work
"""

from azure.ai.projects.models import ToolDefinition
from typing import Dict, Any, List
from custom_agent_functions import submit_loan_application, check_loan_status, trigger_logic_app_workflow, reduce_interest_rate

def create_submit_loan_application_tool() -> Dict[str, Any]:
    """
    Create a tool definition for submitting a new loan application.
    
    This tool should be used when a customer wants to apply for a new loan.
    The agent should collect all required parameters before invoking this tool.
    
    Returns:
        Dict[str, Any]: The tool definition in the format expected by the Azure AI Projects SDK
    """
    
    # Create a tool definition using JSON schema format with clear instructions
    tool_definition = {
        "type": "function",
        "function": {
            "name": "submit_loan_application",
            "description": """Submit a new loan application through the bank's system.
            ONLY use this tool when the user explicitly wants to apply for a new loan.
            You MUST collect all required parameters (applicant_name, loan_amount, loan_type, 
            credit_score, contact_email) before calling this tool. If the user doesn't provide all 
            required information, ask for the missing details before proceeding.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "applicant_name": {
                        "type": "string",
                        "description": "The full name of the loan applicant (required)"
                    },
                    "loan_amount": {
                        "type": "number",
                        "description": "The requested loan amount in dollars (required)"
                    },
                    "loan_type": {
                        "type": "string",
                        "description": "The type of loan (e.g., 'mortgage', 'personal', 'auto', 'education') (required)",
                        "enum": ["mortgage", "personal", "auto", "education", "business", "other"]
                    },
                    "credit_score": {
                        "type": "integer",
                        "description": "The applicant's credit score (typically between 300-850) (required)",
                        "minimum": 300,
                        "maximum": 850
                    },
                    "contact_email": {
                        "type": "string",
                        "description": "The email address for communications about the loan (required)",
                        "format": "email"
                    }
                },
                "required": ["applicant_name", "loan_amount", "loan_type", "credit_score", "contact_email"]
            }
        }
    }
    
    return tool_definition

def create_check_loan_status_tool() -> Dict[str, Any]:
    """
    Create a tool definition for checking the status of an existing loan application.
    
    This tool should be used when a customer wants to check the status of their loan application.
    The agent should collect all required parameters before invoking this tool.
    
    Returns:
        Dict[str, Any]: The tool definition in the format expected by the Azure AI Projects SDK
    """
    
    # Create a tool definition using JSON schema format with clear instructions
    tool_definition = {
        "type": "function",
        "function": {
            "name": "check_loan_status",
            "description": """Check the status of an existing loan application.
            ONLY use this tool when the user explicitly asks about the status of their existing loan application.
            You MUST collect both required parameters (application_id and applicant_name) before calling this tool.
            If the user doesn't provide this information, ask for it specifically before proceeding.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "application_id": {
                        "type": "string",
                        "description": "The unique identifier for the loan application (required)"
                    },
                    "applicant_name": {
                        "type": "string",
                        "description": "The name of the applicant for verification (required)"
                    }
                },
                "required": ["application_id", "applicant_name"]
            }
        }
    }
    
    return tool_definition

def create_logic_app_trigger_tool() -> Dict[str, Any]:
    """
    Create a tool definition for triggering any configured Logic App workflow.
    
    This is a general-purpose tool that allows the agent to trigger different Logic App 
    workflows based on user needs. The agent should select the appropriate workflow and 
    collect all required data before invoking this tool.
    
    Returns:
        Dict[str, Any]: The tool definition in the format expected by the Azure AI Projects SDK
    """
    
    # Create a tool definition using JSON schema format with clear instructions
    tool_definition = {
        "type": "function",
        "function": {
            "name": "trigger_logic_app_workflow",
            "description": """Trigger a specific Azure Logic App workflow with input data.
            This is a general-purpose tool to interact with various bank services through Logic Apps.
            ONLY use this tool when a user explicitly requests an action that matches one of the supported workflows.
            You MUST select the appropriate workflow_name from the supported list and provide all required input data.
            Available workflows:
            - 'loan_approval': For processing loan approval requests
            - 'account_creation': For creating new bank accounts
            - 'document_processing': For processing and validating submitted documents
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "workflow_name": {
                        "type": "string",
                        "description": "The name of the Logic App workflow to trigger (required)",
                        "enum": ["loan_approval", "account_creation", "document_processing"]
                    },
                    "input_data": {
                        "type": "object",
                        "description": "The input data to send to the Logic App workflow as a JSON object (required)"
                    }
                },
                "required": ["workflow_name", "input_data"]
            }
        }
    }
    
    return tool_definition

def create_interest_rate_reduction_tool() -> Dict[str, Any]:
    """
    Create a tool definition for reducing the interest rate on an existing loan.
    
    This tool should be used when a customer explicitly requests an interest rate 
    reduction for their existing loan. The agent should collect all required parameters
    before invoking this tool.
    
    Returns:
        Dict[str, Any]: The tool definition in the format expected by the Azure AI Projects SDK
    """
    
    # Create a tool definition using JSON schema format with clear instructions
    tool_definition = {
        "type": "function",
        "function": {
            "name": "reduce_interest_rate",
            "description": """Process an interest rate reduction request for an existing loan.
            ONLY use this tool when the user explicitly asks to reduce their loan interest rate.
            You MUST collect all required parameters (customer_id, loan_id, and credit_score)
            before calling this tool. If the user doesn't provide any of these details, 
            ask for them specifically before proceeding.
            The system will automatically set the reason as 'reduce_interest_rate' when processing.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The customer ID (required)"
                    },
                    "loan_id": {
                        "type": "string",
                        "description": "The loan ID for which interest rate reduction is requested (required)"
                    },
                    "credit_score": {
                        "type": "integer",
                        "description": "The customer's current credit score (required)",
                        "minimum": 300,
                        "maximum": 850
                    }
                },
                "required": ["customer_id", "loan_id", "credit_score"]
            }
        }
    }
    
    return tool_definition

def get_all_custom_agent_tools() -> List[Dict[str, Any]]:
    """
    Returns all available custom tool definitions for the agent.
    
    This function should be used to get the complete list of custom tools that
    will be registered with the agent during conversation.
    
    Returns:
        List[Dict[str, Any]]: A list of all available custom tool definitions
    """
    return [
        create_submit_loan_application_tool(),
        create_check_loan_status_tool(),
        create_logic_app_trigger_tool(),
        create_interest_rate_reduction_tool()
    ]