from azure.ai.projects.models import AzureAISearchTool
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
import sys
import os

# Import config variables
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

def get_search_connection_id(client):
    """Get the correct AI Search connection ID"""
    connections = client.connections.list()
    for conn in connections:
        if hasattr(conn, 'connection_type') and 'AZURE_AI_SEARCH' in str(conn.connection_type):
            return conn.id
    # Fallback to known connection
    return "/subscriptions/055cefeb-8cfd-4996-b2d5-ee32fa7cf4d4/resourceGroups/rg-kushikote-9315_ai/providers/Microsoft.MachineLearningServices/workspaces/docstorage/connections/dataexc"

def create_identity_agent(client, conn_id, index_name):
    # Define search tool pointing to your AI Search index
    tool = AzureAISearchTool(
        index_connection_id=conn_id,
        index_name=index_name
    )

    # Create identity verification agent
    agent = client.agents.create_agent(
        model="gpt-4o",
        name="identity_checker",
        instructions="""
You are a professional identity verification agent for loan processing. You MUST use the search tool to find and analyze identity documents.

🔍 Search Instructions:
Search for: "*", "aadhaar", "aadhar", "pan", "address proof", "passport", "driving license", "voter id", "identity", "kyc"

📋 CRITICAL INSTRUCTION: NEVER provide JSON output. 

If NO documents found, use SINGLE field format:
**PENDING:** Identity verification requires: Aadhaar, PAN

If documents ARE found, use 3-field format:
**DETAILS:**
Name: [full name]
DOB: [DD-MM-YYYY]
PAN: XXXXX[last 4 digits]
Aadhaar: XXXX XXXX [last 4 digits]
Address: [complete address]

**ANALYSIS:**
Documents found: [list]
Name consistency: [consistent/inconsistent]
Address match: [yes/no]
Format validation: [valid/invalid]
Missing: [list missing documents]

**SUMMARY:**
Status: PASS/FAIL/INCOMPLETE - [Brief conclusion with key verification status and any critical missing documents]

- Keep each field under 2 lines
- Replace | with • (bullet points) for better formatting
- Always mask PAN showing only last 4 digits: XXXXX1234
- Always mask Aadhaar showing only last 4 digits: XXXX XXXX 1234
- Use "not available" for missing information
- MUST search before responding
- Set FAIL if both Aadhaar AND PAN missing
- Set INCOMPLETE if documents found but missing critical info
- Set PASS only if all critical documents present and valid

Important: For privacy and security, always mask sensitive information in your response.
""",
        tools=tool.definitions,
        tool_resources=tool.resources
    )

    return agent
