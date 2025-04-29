import os
import time
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from datetime import datetime, timedelta, timezone

# Load environment variables from .env
load_dotenv()

# ==== Configuration from .env ====
# Azure Blob Storage
storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
storage_account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")

# Azure Document Intelligence
doc_intel_endpoint = os.getenv("AZURE_DOC_INTEL_ENDPOINT")
doc_intel_key = os.getenv("AZURE_DOC_INTEL_KEY")

# Azure OpenAI
openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")

# ==== Initialize Clients ====
blob_service_client = BlobServiceClient.from_connection_string(
    f"DefaultEndpointsProtocol=https;AccountName={storage_account_name};AccountKey={storage_account_key};EndpointSuffix=core.windows.net"
)

doc_client = DocumentIntelligenceClient(
    endpoint=doc_intel_endpoint,
    credential=AzureKeyCredential(doc_intel_key)
)

chat_client = AzureOpenAI(
    azure_endpoint=openai_endpoint,
    api_key=openai_api_key,
    api_version=openai_api_version
)

# ==== Functions ====

def upload_file_to_blob(file_path):
    container_client = blob_service_client.get_container_client(container_name)
    try:
        container_client.get_container_properties()
    except Exception:
        container_client.create_container()

    file_name = os.path.basename(file_path)
    blob_client = container_client.get_blob_client(file_name)
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    print(f"✅ Uploaded '{file_name}' to blob.")
    return file_name

def generate_sas_url(file_name):
    sas_token = generate_blob_sas(
        account_name=storage_account_name,
        container_name=container_name,
        blob_name=file_name,
        account_key=storage_account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    blob_url = f"https://{storage_account_name}.blob.core.windows.net/{container_name}/{file_name}?{sas_token}"
    print(f"✅ Generated SAS URL for '{file_name}'.")
    return blob_url

def analyze_document_from_url(blob_url):
    try:
        poller = doc_client.begin_analyze_document(
            model_id="prebuilt-layout",
            body={"urlSource": blob_url}
        )
        print("⏳ Analyzing document...")
        result = poller.result()
        print("✅ Analysis completed.")
        return result
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None

def extract_text_from_analysis(result):
    extracted_text = ""
    if result and hasattr(result, 'pages'):
        for page in result.pages:
            for line in page.lines:
                extracted_text += line.content + " "
    return extracted_text.strip()

def loan_manager_chat(history, user_input):
    history.append({"role": "user", "content": user_input})

    response = chat_client.chat.completions.create( 
        model=openai_deployment,
        messages=[
            {"role": "system", "content": "You are an intelligent Loan Manager. Carefully analyze the provided documents. If the documents are insufficient to approve the loan, politely request additional documents. If the user cannot provide them, explain that the loan cannot be approved."},
            *history
        ],
        max_tokens=800,
        temperature=0.5,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )

    assistant_reply = response.choices[0].message.content
    history.append({"role": "assistant", "content": assistant_reply})
    return assistant_reply

# ==== Main Execution ====
def main():
    print("📂 Upload files for loan verification. (Enter multiple file paths separated by commas)")
    file_paths_input = input("Enter file paths: ").strip()
    file_paths = [p.strip() for p in file_paths_input.split(",") if p.strip()]
    
    if not file_paths:
        print("❌ No files provided. Exiting.")
        return
    
    all_extracted_text = ""
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            continue
        
        file_name = upload_file_to_blob(file_path)
        blob_url = generate_sas_url(file_name)
        analysis_result = analyze_document_from_url(blob_url)
        extracted_text = extract_text_from_analysis(analysis_result)
        all_extracted_text += extracted_text + "\n"

    if not all_extracted_text:
        print("❌ No text extracted from documents. Exiting.")
        return

    print("\n🤖 Loan Manager Agent is ready to talk to you.\n")

    chat_history = [{"role": "user", "content": f"Here are the details extracted from the applicant's documents:\n{all_extracted_text}"}]
    
    first_response = loan_manager_chat(chat_history, "Based on these documents, should we approve the loan?")
    print(f"🤖 Loan Manager: {first_response}\n")

    while True:
        user_message = input("👤 You: ")
        if user_message.lower() in ["exit", "quit"]:
            print("👋 Exiting. Goodbye!")
            break
        agent_response = loan_manager_chat(chat_history, user_message)
        print(f"🤖 Loan Manager: {agent_response}\n")

if __name__ == "__main__":
    main()
