from azure.ai.projects.models import AzureAISearchTool
from azure.ai.projects import AIProjectClient
from config import *

def create_guarantor_agent(client: AIProjectClient, conn_id: str, index_name: str):
    tool = AzureAISearchTool(
        index_connection_id=conn_id,
        index_name=index_name
    )

    agent = client.agents.create_agent(
        model="gpt-4o",
        name="guarantor_evaluator",
        instructions=(
            "You are an expert guarantor verification agent. You MUST use the search tool to find and analyze call recordings.\n\n"
            
            "🔍 Search Instructions:\n"
            "Search for: 'call recording', 'guarantor', 'conversation', 'audio', 'phone call'\n\n"
            
            "📋 CRITICAL INSTRUCTION: You MUST ALWAYS respond in the specified format. NEVER explain about JSON format or provide error messages.\n\n"
            "If NO call recording found, use SINGLE field format:\n"
            "**PENDING:** Guarantor verification requires: Call Recording, Consent Documentation\n\n"
            
            "If call recording IS found, use 3-field format:\n"
            "**DETAILS:**\n"
            "Name: [guarantor name]\n"
            "Relationship: [to applicant]\n"
            "Contact: [phone/details]\n"
            "Call Found: [yes/no]\n\n"
            
            "**ANALYSIS:**\n"
            "Consent: [explicit/reluctant/unclear]\n"
            "Financial capability: [discussed/not discussed]\n"
            "Understanding: [clear/limited]\n"
            "Red flags: [list any concerns]\n"
            "Call quality: [clear/unclear]\n\n"
            
            "**SUMMARY:**\n"
            "Status: PASS/FAIL - [Brief conclusion about guarantor suitability and willingness to guarantee the loan]\n\n"
            
            "📋 Instructions:\n"
            "- MUST search before responding\n"
            "- NEVER explain about JSON format restrictions\n"
            "- ALWAYS use the PENDING format if no call recording found\n"
            "- Keep responses professional and concise\n"
            "- Focus on consent and capability only"
        ),
        tools=tool.definitions,
        tool_resources=tool.resources
    )
    return agent