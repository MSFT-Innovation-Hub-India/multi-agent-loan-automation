import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import AzureAISearchTool, Tool
# Load environment variables
load_dotenv()
# Azure Machine Learning Project Config
ENDPOINT = os.getenv("ENDPOINT")
RESOURCE_GROUP = os.getenv("RESOURCE_GROUP")
SUBSCRIPTION_ID = os.getenv("SUBSCRIPTION_ID")
PROJECT_NAME = os.getenv("PROJECT_NAME")
INDEX_NAME = os.getenv("INDEX_NAME")

# Step 2: Connect to your Azure AI Project
project_client = AIProjectClient(
    endpoint=ENDPOINT,
    resource_group_name=RESOURCE_GROUP,
    subscription_id=SUBSCRIPTION_ID,
    project_name=PROJECT_NAME,
    credential=DefaultAzureCredential()
)
# Step 3: Connect to Azure AI Search
conn_list = project_client.connections.list()
conn_id = ""
for conn in conn_list:
    if conn.connection_type == "CognitiveSearch":
        conn_id = conn.id
        print(f"✅ Found Azure AI Search connection: {conn_id}")

# Step 4: Define the AI Search tool
try:
    ai_search = AzureAISearchTool(
        index_connection_id=conn_id,
        index_name=INDEX_NAME,
        field_mappings={
            "content": "content",
            "title": "document_title",
            "source": "document_path",
            "image_ref": "bounding_box"
        }
    )
    
except TypeError:
    #print("⚠️ 'field_mappings' not supported by SDK. Proceeding without mappings.")
    ai_search = AzureAISearchTool(
        index_connection_id=conn_id,
        index_name=INDEX_NAME
    )

# Step 5: Define the Agent with updated instructions
search_agent = project_client.agents.create_agent(
    model="gpt-4o",
    name="docagent",
    instructions=(
        "You are a specialized agent helping analyze a single customer's documents. "
        "The documents include Aadhaar, bankstatements , and other personal files."
        "All documents in the index relate to the same customer and are to be treated as a unified corpus. "
        "When answering, always assume you're working with one customer's full documentation package. "
        "Use only indexed data; do not guess. Be concise, clear, and reference the data where possible."
    ),
    tools=ai_search.definitions,
    tool_resources=ai_search.resources,
)

# Step 6: Create a thread
thread = project_client.agents.create_thread()

print("\n💬 You can now ask questions about the indexed customer documents (type 'exit' to stop).")

# Step 7: Chat loop
while True:
    user_input = input("\n🔍 Your Question: ")
    if user_input.lower() in ["exit", "quit"]:
        break

    # Add message
    project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=user_input
    )

    # Run the agent
    run = project_client.agents.create_and_process_run(
        thread_id=thread.id,
        agent_id=search_agent.id
    )

    # Display output
    if run.status == "failed":
        print(f"❌ Agent failed: {run.last_error}")
    else:
        messages = project_client.agents.list_messages(thread_id=thread.id)
        last_msg = messages.get_last_text_message_by_role("assistant")
        print("\n🤖 Agent:", last_msg.text.value)

# Step 8: Clean up (optional)
delete = input("\n🧹 Do you want to delete the agent now? (y/n): ")
if delete.lower() == 'y':
    project_client.agents.delete_agent(search_agent.id)
    print("✅ Agent deleted.")
else:
    print("ℹ️ Agent retained for further use.")
