import os
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MessageRole
from config import *
from instructions.prompts import (
    IDENTITY_CHECK_PROMPT,
    INCOME_CHECK_PROMPT,
    GUARANTOR_CHECK_PROMPT,
    COLLATERAL_INSPECTION_PROMPT,
    VALUATION_CHECK_PROMPT
)

from agents.identity_agent import create_identity_agent
from agents.income_agent import create_income_agent
from agents.gua import create_guarantor_agent
from agents.val_agent import create_valuation_agent
from agents.insp import create_collateral_inspection_agent


# Import project configuration
from main_config import ENDPOINT, RESOURCE_GROUP, SUBSCRIPTION_ID, PROJECT_NAME

# Initialize AI Project Client
project_client = AIProjectClient(
    endpoint=ENDPOINT,
    resource_group_name=RESOURCE_GROUP,
    subscription_id=SUBSCRIPTION_ID,
    project_name=PROJECT_NAME,
    credential=DefaultAzureCredential()
)

# Get Azure Cognitive Search Connection ID
conn_id = next(conn.id for conn in project_client.connections.list() if conn.connection_type == "CognitiveSearch")

# Create Agents
print("Creating agents...")
identity_agent = create_identity_agent(project_client, conn_id, "identityindex")
income_agent = create_income_agent(project_client, conn_id, "rag-1749535545848")
inspection_agent = create_collateral_inspection_agent(project_client, conn_id, "hou")
guarantor_agent = create_guarantor_agent(project_client, conn_id, "gua")
valuation_agent = create_valuation_agent(project_client, conn_id, "rag-1750155157603")
print("All agents created.\n")

def run_agent_check(agent, prompt: str, name: str):
    print(f"Running {name}...")
    thread = project_client.agents.create_thread()
    _ = project_client.agents.create_message(
        thread_id=thread.id,
        role=MessageRole.USER,
        content=prompt
    )
    run = project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)
    if run.status == "failed":
        print(f"❌ {name} failed. Halting process.")
        return None
    response = project_client.agents.list_messages(thread_id=thread.id).get_last_message_by_role(MessageRole.AGENT)
    if response:
        print(f"✅ {name} Result:")
        for msg in response.text_messages:
            print(msg.text.value)
    return True

# Identity Check
if not run_agent_check(identity_agent, IDENTITY_CHECK_PROMPT, "Identity Check"):
    exit()

# Income Check
if not run_agent_check(income_agent, INCOME_CHECK_PROMPT, "Income Check"):
    exit()

# Guarantor Check
if not run_agent_check(guarantor_agent, GUARANTOR_CHECK_PROMPT, "Guarantor Check"):
    exit()

# Collateral Inspection
if not run_agent_check(inspection_agent, COLLATERAL_INSPECTION_PROMPT, "Collateral Inspection Check"):
    exit()

# Property Valuation
if not run_agent_check(valuation_agent, VALUATION_CHECK_PROMPT, "Valuation Check"):
    exit()

print("\n✅ All checks passed successfully!")

# Cleanup
print("\nCleaning up agents...")
project_client.agents.delete_agent(identity_agent.id)
project_client.agents.delete_agent(income_agent.id)
project_client.agents.delete_agent(guarantor_agent.id)
project_client.agents.delete_agent(inspection_agent.id)
project_client.agents.delete_agent(valuation_agent.id)
print("All agents deleted.")