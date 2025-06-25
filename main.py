import os
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ConnectedAgentTool, MessageRole, AzureAISearchTool
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

def get_controller_instructions():
    dir_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(dir_path, 'instructions', 'controller_instructions.txt'), 'r', encoding='utf-8') as f:
        return f.read()


# Import project configuration
from main_config import ENDPOINT, RESOURCE_GROUP, SUBSCRIPTION_ID, PROJECT_NAME, INDEX_NAME

# Initialize the project client
project_client = AIProjectClient(
    endpoint=ENDPOINT,
    resource_group_name=RESOURCE_GROUP,
    subscription_id=SUBSCRIPTION_ID,
    project_name=PROJECT_NAME,
    credential=DefaultAzureCredential()
)

# Get CognitiveSearch connection ID
conn_id = next(conn.id for conn in project_client.connections.list() if conn.connection_type == "CognitiveSearch")

print("Creating specialized agents...")
# Create individual agents
identity_agent = create_identity_agent(project_client, conn_id, "identityindex")
print(f"Created identity agent, ID: {identity_agent.id}")

income_agent = create_income_agent(project_client, conn_id, "rag-1749535545848")
print(f"Created income agent, ID: {income_agent.id}")

inspection_agent = create_collateral_inspection_agent(project_client, conn_id, "hou")
print(f"Created inspection agent, ID: {inspection_agent.id}")

guarantor_agent = create_guarantor_agent(project_client, conn_id, "gua")
print(f"Created guarantor agent, ID: {guarantor_agent.id}")

valuation_agent = create_valuation_agent(project_client, conn_id, "rag-1750155157603")
print(f"Created valuation agent, ID: {valuation_agent.id}")

# Create connected agent tools
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
        id=inspection_agent.id,
        name="collateral_inspection_agent",
        description="Analyzes property inspection video"
    ),
    ConnectedAgentTool(
        id=valuation_agent.id,
        name="valuation_agent",
        description="Assesses property valuation and provides property analysis"
    )
]

# Create the main controller agent
# Get the tool definitions and resources from the first tool
# (All connected tools share the same resources)
combined_tool = connected_tools[0]
for tool in connected_tools[1:]:
    combined_tool.definitions.extend(tool.definitions)

controller = project_client.agents.create_agent(
    model="gpt-4o",
    name="master_orchestrator",
    instructions=get_controller_instructions(),
    tools=combined_tool.definitions,
    tool_resources=combined_tool.resources
)
print(f"Created controller agent, ID: {controller.id}")

# Create a new thread
thread = project_client.agents.create_thread()
print(f"Created thread, ID: {thread.id}")

# Create message to start the evaluation
# Test identity agent
print("\nTesting Identity Agent...")
identity_thread = project_client.agents.create_thread()
identity_message = project_client.agents.create_message(
    thread_id=identity_thread.id,
    role=MessageRole.USER,
    content=IDENTITY_CHECK_PROMPT
)
identity_run = project_client.agents.create_and_process_run(thread_id=identity_thread.id, agent_id=identity_agent.id)
print(f"Identity check status: {identity_run.status}")
if identity_run.status != "failed":
    identity_response = project_client.agents.list_messages(thread_id=identity_thread.id).get_last_message_by_role(MessageRole.AGENT)
    if identity_response:
        print("Identity Check Result:")
        for msg in identity_response.text_messages:
            print(msg.text.value)

# Test income agent
print("\nTesting Income Agent...")
income_thread = project_client.agents.create_thread()
income_message = project_client.agents.create_message(
    thread_id=income_thread.id,
    role=MessageRole.USER,
    content=INCOME_CHECK_PROMPT
)
income_run = project_client.agents.create_and_process_run(thread_id=income_thread.id, agent_id=income_agent.id)
print(f"Income check status: {income_run.status}")
if income_run.status != "failed":
    income_response = project_client.agents.list_messages(thread_id=income_thread.id).get_last_message_by_role(MessageRole.AGENT)
    if income_response:
        print("Income Check Result:")
        for msg in income_response.text_messages:
            print(msg.text.value)

# Test guarantor agent
print("\nTesting Guarantor Agent...")
guarantor_thread = project_client.agents.create_thread()
guarantor_message = project_client.agents.create_message(
    thread_id=guarantor_thread.id,
    role=MessageRole.USER,
    content=GUARANTOR_CHECK_PROMPT
)
guarantor_run = project_client.agents.create_and_process_run(thread_id=guarantor_thread.id, agent_id=guarantor_agent.id)
print(f"Guarantor check status: {guarantor_run.status}")
if guarantor_run.status != "failed":
    guarantor_response = project_client.agents.list_messages(thread_id=guarantor_thread.id).get_last_message_by_role(MessageRole.AGENT)
    if guarantor_response:
        print("Guarantor Check Result:")
        for msg in guarantor_response.text_messages:
            print(msg.text.value)

# Test collateral inspection agent
print("\nTesting Collateral Inspection Agent...")
inspection_thread = project_client.agents.create_thread()
inspection_message = project_client.agents.create_message(
    thread_id=inspection_thread.id,
    role=MessageRole.USER,
    content=COLLATERAL_INSPECTION_PROMPT
)
inspection_run = project_client.agents.create_and_process_run(thread_id=inspection_thread.id, agent_id=inspection_agent.id)
print(f"Inspection check status: {inspection_run.status}")
if inspection_run.status != "failed":
    inspection_response = project_client.agents.list_messages(thread_id=inspection_thread.id).get_last_message_by_role(MessageRole.AGENT)
    if inspection_response:
        print("Inspection Check Result:")
        for msg in inspection_response.text_messages:
            print(msg.text.value)

# Test valuation agent
print("\nTesting Valuation Agent...")
valuation_thread = project_client.agents.create_thread()
valuation_message = project_client.agents.create_message(
    thread_id=valuation_thread.id,
    role=MessageRole.USER,
    content=VALUATION_CHECK_PROMPT
)
valuation_run = project_client.agents.create_and_process_run(thread_id=valuation_thread.id, agent_id=valuation_agent.id)
print(f"Valuation check status: {valuation_run.status}")
if valuation_run.status != "failed":
    valuation_response = project_client.agents.list_messages(thread_id=valuation_thread.id).get_last_message_by_role(MessageRole.AGENT)
    if valuation_response:
        print("Valuation Check Result:")
        for msg in valuation_response.text_messages:
            print(msg.text.value)

# If all individual checks pass, then test the controller
print("\nTesting Controller Agent...")
controller_thread = project_client.agents.create_thread()
controller_message = project_client.agents.create_message(
    thread_id=controller_thread.id,
    role=MessageRole.USER,
    content="Please evaluate the loan application documents. Check identity documents first, then income documents, guarantor information, and finally property valuation. Provide a complete assessment.",
)
print(f"Created message, ID: {controller_message.id}")

print("Processing loan evaluation...")
controller_run = project_client.agents.create_and_process_run(thread_id=controller_thread.id, agent_id=controller.id)
print(f"Run finished with status: {controller_run.status}")

if controller_run.status == "failed":
    print(f"Run failed: {controller_run.last_error}")
else:
    response_message = project_client.agents.list_messages(thread_id=controller_thread.id).get_last_message_by_role(MessageRole.AGENT)
    if response_message:
        print("\n📊 Final Evaluation Summary:")
        for text_message in response_message.text_messages:
            print(text_message.text.value)

# Debug: Create a test agent to list all documents
debug_tool = AzureAISearchTool(
    index_connection_id=conn_id,
    index_name=INDEX_NAME
)

debug_agent = project_client.agents.create_agent(
    model="gpt-4o",
    name="debug_agent",
    instructions="List all documents you can find. Use the search tool with an empty or '*' query to get everything.",
    tools=debug_tool.definitions,
    tool_resources=debug_tool.resources,
)

debug_thread = project_client.agents.create_thread()
debug_message = project_client.agents.create_message(
    thread_id=debug_thread.id,
    role=MessageRole.USER,
    content="Please list all documents you can find in the index with their types."
)

# Cleanup
print("\nCleaning up resources...")
project_client.agents.delete_agent(controller.id)
project_client.agents.delete_agent(identity_agent.id)
project_client.agents.delete_agent(income_agent.id)
project_client.agents.delete_agent(guarantor_agent.id)
project_client.agents.delete_agent(inspection_agent.id)
project_client.agents.delete_agent(valuation_agent.id)
print("All agents deleted successfully")