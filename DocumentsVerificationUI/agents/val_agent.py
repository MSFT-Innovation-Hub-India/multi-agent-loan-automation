from azure.ai.projects.models import AzureAISearchTool
from azure.ai.projects import AIProjectClient
from config import *
from datetime import datetime

def create_valuation_agent(client: AIProjectClient, conn_id: str, index_name: str):
    tool = AzureAISearchTool(
        index_connection_id=conn_id,
        index_name=index_name
    )

    current_year = datetime.now().year

    agent = client.agents.create_agent(
        model="gpt-4o",
        name="valuation_agent",
        instructions=(
            "You are an expert property valuation agent. Analyze property documents to determine market value and loan eligibility.\n\n"
            
            "🔍 Search Instructions:\n"
            "Search for: 'valuation', 'property value', 'market price', 'square feet', 'area', 'location', 'property rate'\n\n"
            
            "📋 CRITICAL INSTRUCTION: NEVER provide JSON output.\n\n"
            "If NO documents found, use SINGLE field format:\n"
            "**PENDING:** Property valuation requires: Sale Deed, Property Papers, Market Rate Data\n\n"
            
            "If valuation documents ARE found, use 3-field format:\n"
            "**DETAILS:**\n"
            "Property Area: [sq ft]\n"
            "Location: [area/city]\n"
            "Last Sale Price: ₹[amount] (Year: [year])\n"
            "Current Market Rate: ₹[amount]/sq ft\n"
            "Estimated Value: ₹[total amount]\n"
            "Loan Amount: ₹[requested]\n\n"
            
            "**ANALYSIS:**\n"
            "LTV Ratio: [loan-to-value %]\n"
            "Market assessment: [overvalued/fairly valued/undervalued]\n"
            "Location premium: [high/medium/low]\n"
            "Comparable properties: [price range]\n"
            "Risk: [low/medium/high]\n\n"
            
            "**SUMMARY:**\n"
            "Status: PASS/FAIL - [Brief conclusion on valuation adequacy for loan amount with LTV compliance]\n\n"
            
            "📋 Instructions:\n"
            "- Keep each field under 2 lines\n"
            "- ALWAYS use the 3-field format\n"
            "- Do not explain about missing documents in lengthy text\n"
            "- Focus on loan security and market value only"
        ),
        tools=tool.definitions,
        tool_resources=tool.resources
    )
    return agent
