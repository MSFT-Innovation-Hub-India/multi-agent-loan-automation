from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ConnectedAgentTool
from azure.identity import DefaultAzureCredential
from config import *

def create_controller_agent(client, identity_agent, income_agent, guarantor_agent, valuation_agent):
    connected_tools = [
        ConnectedAgentTool(
            id=identity_agent.id,
            name="identity_checker",
            description="Validates identity documents and extracts key information from them"
        ),
        ConnectedAgentTool(
            id=income_agent.id,
            name="income_checker",
            description="Analyzes income documents and validates financial eligibility"
        ),
        ConnectedAgentTool(
            id=guarantor_agent.id,
            name="guarantor_evaluator",
            description="Evaluates guarantor information and their eligibility"
        ),
        ConnectedAgentTool(
            id=valuation_agent.id,
            name="valuation_agent",
            description="Assesses property valuation and provides property analysis"
        )
    ]

    controller = client.agents.create_agent(
        model="gpt-4o",
        name="master_orchestrator",
        instructions=(
            "You are a master controller for loan processing. Call agents as needed:\n"
            "- First call identity_checker to validate identity documents\n"
            "- If identity check passes, call income_checker to assess financial eligibility\n"
            "- Then call guarantor_evaluator to evaluate guarantor information\n"
            "- Finally call valuation_agent to assess property value\n"
            "Summarize all findings and return final decision JSON: {overall_status, observations}."
        ),
        tools=connected_tools
    )
    return controller