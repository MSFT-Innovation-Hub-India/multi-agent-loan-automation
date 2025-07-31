import os
import sys
import json
import uuid
import logging
import base64
from io import BytesIO
from pathlib import Path
from datetime import datetime, timedelta, timezone
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType
)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Azure endpoints and keys
AZURE_AI_ENDPOINT = os.getenv("AZURE_AI_ENDPOINT")
AZURE_AI_API_VERSION = os.getenv("AZURE_AI_API_VERSION", "2024-12-01-preview")
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("SEARCH_KEY")

# Azure Blob Storage Configuration
STORAGE_ACCOUNT_NAME = os.getenv("STORAGE_ACCOUNT_NAME")
STORAGE_ACCOUNT_KEY = os.getenv("STORAGE_ACCOUNT_KEY")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

# Validate required environment variables
required_env_vars = [
    "AZURE_AI_ENDPOINT", "SEARCH_ENDPOINT", "SEARCH_KEY",
    "STORAGE_ACCOUNT_NAME", "STORAGE_ACCOUNT_KEY", "CONTAINER_NAME"
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    print("Please check your .env file and ensure all required variables are set.")
    sys.exit(1)

# Import CU client
sys.path.append(str(Path(__file__).parent.parent))
from python.content_understanding_client import AzureContentUnderstandingClient

credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")

client = AzureContentUnderstandingClient(
    endpoint=AZURE_AI_ENDPOINT,
    api_version=AZURE_AI_API_VERSION,
    token_provider=token_provider,
)


# === Blob Storage Helper Functions ===
def get_all_customer_documents():
    """
    Get all documents organized by customer ID and document type
    Only processes CUST*/DocumentType/ structure, ignores Documents/ folder
    """
    connect_str = f"DefaultEndpointsProtocol=https;AccountName={STORAGE_ACCOUNT_NAME};AccountKey={STORAGE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)

    # Get all blobs from the container
    blobs = container_client.list_blobs()
    
    customer_docs = {}
    for blob in blobs:
        # Skip folders (they end with '/')
        if blob.name.endswith('/'):
            continue
            
        # Only process Structure 1: CUST0001/Identity/file.jpg
        # Ignore Documents/ folder structure
        path_parts = blob.name.split('/')
        
        if len(path_parts) >= 3 and path_parts[0].startswith('CUST'):
            # Structure 1: CUST0001/Identity/file.jpg
            customer_id = path_parts[0]
            doc_type = path_parts[1]
            
            if customer_id not in customer_docs:
                customer_docs[customer_id] = {}
            if doc_type not in customer_docs[customer_id]:
                customer_docs[customer_id][doc_type] = []
                
            customer_docs[customer_id][doc_type].append(blob.name)
    
    return customer_docs


def get_blobs_from_customer_path(customer_id, document_type):
    """
    Retrieve blobs from specific customer and document type
    Only processes CUST*/DocumentType/ structure, ignores Documents/ folder
    """
    connect_str = f"DefaultEndpointsProtocol=https;AccountName={STORAGE_ACCOUNT_NAME};AccountKey={STORAGE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)

    # Get all blobs and filter for the specific customer and document type
    blobs = container_client.list_blobs()
    blob_list = []
    
    for blob in blobs:
        # Skip folders
        if blob.name.endswith('/'):
            continue
            
        path_parts = blob.name.split('/')
        
        # Only check Structure 1: CUST0001/Identity/file.jpg
        # Ignore Documents/ folder structure
        if len(path_parts) >= 3 and path_parts[0] == customer_id and path_parts[1] == document_type:
            blob_list.append(blob.name)
    
    return blob_list


def generate_sas_url(file_name):
    """Generate SAS URL for blob access"""
    sas_token = generate_blob_sas(
        account_name=STORAGE_ACCOUNT_NAME,
        container_name=CONTAINER_NAME,
        blob_name=file_name,
        account_key=STORAGE_ACCOUNT_KEY,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    blob_url = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/{file_name}?{sas_token}"
    return blob_url


def get_file_modality(file_name):
    """
    Determine the modality of a file based on its extension
    """
    extension = file_name.lower().split('.')[-1]
    
    if extension in ['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'tiff', 'bmp']:
        return 'document'
    elif extension in ['mp3', 'wav', 'aac', 'flac', 'm4a']:
        return 'audio'
    elif extension in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv']:
        return 'video'
    else:
        # Default to document for unknown types
        return 'document'


def list_available_customers_and_types():
    """
    Show available customers and document types in the container
    """
    print("\n🔍 Scanning available customers and document types...")
    customer_docs = get_all_customer_documents()
    
    if not customer_docs:
        print("❌ No customer documents found in data/ structure.")
        return
    
    print("\n📊 Available Customers and Document Types:")
    print("-" * 40)
    
    for customer_id, doc_types in customer_docs.items():
        print(f"👤 Customer: {customer_id}")
        for doc_type, files in doc_types.items():
            print(f"   📂 {doc_type} ({len(files)} files)")
        print()


def debug_container_contents():
    """
    Debug function to show ALL files in the container to understand the structure
    """
    print("\n🔧 DEBUG: Exploring container contents...")
    print("-" * 50)
    
    try:
        connect_str = f"DefaultEndpointsProtocol=https;AccountName={STORAGE_ACCOUNT_NAME};AccountKey={STORAGE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)

        # List all blobs
        blobs = container_client.list_blobs()
        blob_list = []
        
        for blob in blobs:
            blob_list.append(blob.name)
        
        if not blob_list:
            print("❌ No files found in the container at all!")
            print(f"   Container name: {CONTAINER_NAME}")
            print(f"   Storage account: {STORAGE_ACCOUNT_NAME}")
        else:
            print(f"✅ Found {len(blob_list)} files in container '{CONTAINER_NAME}':")
            print("\n📂 All files in container:")
            for i, blob_name in enumerate(blob_list[:20], 1):  # Show first 20 files
                print(f"   {i:2d}. {blob_name}")
            
            if len(blob_list) > 20:
                print(f"   ... and {len(blob_list) - 20} more files")
            
            # Analyze the structure
            print(f"\n📊 File structure analysis:")
            folders = set()
            for blob_name in blob_list:
                parts = blob_name.split('/')
                if len(parts) > 1:
                    folders.add('/'.join(parts[:-1]))
            
            if folders:
                print("   Detected folder structure:")
                for folder in sorted(folders):
                    print(f"     📁 {folder}/")
            else:
                print("   All files are in the root of the container")
                
    except Exception as e:
        print(f"❌ Error accessing container: {e}")
        print(f"   Please check your storage account credentials")


def save_image(image_id: str, analyze_response):
    try:
        raw_image = client.get_image_from_analyze_operation(
            analyze_response=analyze_response,
            image_id=image_id
        )
        if not raw_image:
            logging.warning(f"No image data returned for image ID {image_id}")
            return

        image = Image.open(BytesIO(raw_image))
        Path(".cache").mkdir(exist_ok=True)
        image.save(f".cache/{image_id}.jpg", "JPEG")
        logging.info(f"Saved image: .cache/{image_id}.jpg")
    except Exception as e:
        logging.warning(f"Could not fetch image {image_id}: {e}")


def create_search_index(index_name: str):
    try:
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="metadata", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="segmentDescription", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
        ]
        index = SearchIndex(name=index_name, fields=fields)
        index_client = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=AzureKeyCredential(SEARCH_KEY))
        index_client.create_index(index)
        print(f"Index '{index_name}' created.")
    except Exception as e:
        print(f"Index creation skipped or failed: {e}")


def process_and_index(modality_name, analyzer_template_path, file_blob_name, search_client):
    analyzer_id = f"{modality_name}-{uuid.uuid4()}"
    print(f"\nProcessing: {file_blob_name} with {analyzer_template_path}")

    # Generate SAS URL for the blob
    blob_url = generate_sas_url(file_blob_name)
    
    response = client.begin_create_analyzer(analyzer_id, analyzer_template_path=analyzer_template_path)
    client.poll_result(response)

    # Use the blob URL instead of local file path
    response = client.begin_analyze(analyzer_id, file_location=blob_url)
    result = client.poll_result(response)
    client.delete_analyzer(analyzer_id)

    print(json.dumps(result, indent=2))

    documents = []
    keyframe_ids = set()

    result_data = result.get("result", {})
    contents = result_data.get("contents", [])

    # Extract customer ID and document type from blob path
    customer_id = "unknown"
    doc_type = "unknown"
    path_parts = file_blob_name.split('/')
    if len(path_parts) >= 3 and path_parts[0].startswith('CUST'):
        customer_id = path_parts[0]
        doc_type = path_parts[1]

    for idx, item in enumerate(contents):
        content_text = item.get("text") or item.get("transcript") or item.get("markdown") or ""
        metadata = json.dumps(item.get("metadata", {}))
        segment_desc = ""

        # Extract segmentDescription from video results
        if modality_name == "video":
            fields = item.get("fields", {})
            segment_desc = fields.get("segmentDescription", {}).get("valueString", "")

            # Also collect keyframes if available
            media_info = item.get("metadata", {}).get("media", {})
            image_id = media_info.get("imageId")
            if image_id:
                keyframe_ids.add(image_id)

        documents.append({
            "id": f"{customer_id}-{doc_type}-{modality_name}-{uuid.uuid4()}",
            "content": content_text,
            "metadata": metadata,
            "segmentDescription": segment_desc
        })

    if documents:
        result_upload = search_client.upload_documents(documents=documents)
        print(f"Uploaded {len(documents)} documents from {modality_name} - {file_blob_name}")

    for keyframe_id in keyframe_ids:
        try:
            save_image(keyframe_id, result)
        except Exception as e:
            logging.warning(f"Failed to save keyframe image {keyframe_id}: {e}")


def get_files_from_blob_storage():
    """
    Get files from blob storage based on user selection
    """
    print("\n" + "="*50)
    print("📋 BLOB STORAGE FILE PROCESSING OPTIONS")
    print("="*50)
    
    choice = input("\nChoose processing mode:\n1. Process specific customer and document type\n2. Process all customer documents\nEnter choice (1 or 2): ").strip()
    
    files_with_modalities = []
    
    if choice == "1":
        print("\n📝 Enter Customer and Document Details:")
        customer_id = input("Customer ID (e.g., CUST0001): ").strip()
        
        if not customer_id:
            print("❌ Customer ID cannot be empty!")
            return []
        
        print("\n📂 Available document types typically include:")
        print("   - Identity")
        print("   - Income") 
        print("   - Collateral")
        print("   - Guarantor")
        print("   - Others...")
        
        document_type = input("\nDocument Type (e.g., Identity): ").strip()
        
        if not document_type:
            print("❌ Document type cannot be empty!")
            return []
        
        # Get files for specific customer and document type
        file_names = get_blobs_from_customer_path(customer_id, document_type)
        
        if not file_names:
            print(f"❌ No files found for customer {customer_id} with document type {document_type}.")
            return []
        
        print(f"\n✅ Found {len(file_names)} files:")
        for file_name in file_names:
            modality = get_file_modality(file_name)
            files_with_modalities.append((modality, file_name))
            print(f"   📄 {file_name} (modality: {modality})")
    
    elif choice == "2":
        print("\n🚀 Processing ALL customer documents...")
        customer_docs = get_all_customer_documents()
        
        if not customer_docs:
            print("❌ No customer documents found.")
            return []
        
        total_files = 0
        for customer_id, doc_types in customer_docs.items():
            for doc_type, file_names in doc_types.items():
                for file_name in file_names:
                    modality = get_file_modality(file_name)
                    files_with_modalities.append((modality, file_name))
                    total_files += 1
        
        print(f"✅ Found {total_files} files total across all customers.")
    
    else:
        print("❌ Invalid choice! Please enter 1 or 2.")
        return get_files_from_blob_storage()
    
    return files_with_modalities


def get_files_interactively():
    """
    Legacy function - now redirects to blob storage
    """
    print("⚠️  This function now uses blob storage instead of local files.")
    return get_files_from_blob_storage()


if __name__ == "__main__":
    # Show debug information first
    debug_container_contents()
    
    # Show available options
    list_available_customers_and_types()
    
    index_name = input("\nEnter the Azure AI Search index name to create/use: ").strip()
    if not index_name:
        print("Index name cannot be empty. Exiting.")
        sys.exit(1)

    create_search_index(index_name)

    search_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=index_name, credential=AzureKeyCredential(SEARCH_KEY))

    # Get files from blob storage instead of interactive input
    files_to_process = get_files_from_blob_storage()
    
    if not files_to_process:
        print("❌ No files to process. Exiting.")
        sys.exit(1)

    analyzer_templates = {
        "document": "./analyzer_templates/content_document.json",
        "audio": "./analyzer_templates/call_recording_analytics.json",
        "video": "./analyzer_templates/content_video.json"
    }

    print(f"\n🚀 Starting to process {len(files_to_process)} files...")
    
    for modality, file_blob_name in files_to_process:
        if modality not in analyzer_templates:
            print(f"No analyzer template found for modality '{modality}'. Skipping file {file_blob_name}.")
            continue
        analyzer_template_path = analyzer_templates[modality]
        process_and_index(modality, analyzer_template_path, file_blob_name, search_client)

    print("🎯 All content extracted and indexed successfully from blob storage.")