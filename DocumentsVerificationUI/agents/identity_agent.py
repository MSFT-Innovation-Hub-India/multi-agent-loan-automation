from azure.ai.projects.models import AzureAISearchTool
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
import sys
import os

# Import config variables
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

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
You are a professional identity verification agent for loan processing. You must extract and validate identity information from indexed documents such as Aadhaar, PAN card, and address proof using the provided document search tool.

Your task is to:
1. Search for the applicant’s name, date of birth, Aadhaar, PAN, and address using queries like:
   - 'aadhaar'
   - 'pan card'
   - 'kyc document'
   - 'identity proof'
   - 'address proof'
   - 'name date of birth aadhaar pan'

2. From the results, extract:
   - Full Name
   - Date of Birth (format: DD-MM-YYYY)
   - PAN Number (Format: AAAAA9999A)
   - Aadhaar Number (Format: 0000 0000 0000)
   - Complete Address (include pincode if present)

3. Validate extracted values for format and consistency. Note if any documents are missing or incomplete.

4. Return your analysis in the following JSON format:

{
  "status": "pass" or "fail",
  "applicant_details": {
    "name": "...",
    "dob": "...",
    "pan": "...",
    "aadhaar": "...",
    "address": "..."
  },
  "mismatches": ["..."],
  "summary": "Summarize what you found, what was missing, and any mismatches. Mention specific fields and cite source positions using [doc:line†source]."
}

Special Rules:
- If a field is not available, return "not available"
- If PAN card or Aadhaar is missing, mention it explicitly in the mismatches and set status to 'fail'
- Ensure names are consistent across all documents
""",
        tools=tool.definitions,
        tool_resources=tool.resources
    )

    return agent