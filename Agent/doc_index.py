# === Imports ===
import os
import time
import base64
from datetime import datetime, timedelta, timezone

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchFieldDataType,
    SearchField,
)

load_dotenv()

# Azure Blob Storage
STORAGE_ACCOUNT_NAME = os.getenv("STORAGE_ACCOUNT_NAME")
STORAGE_ACCOUNT_KEY = os.getenv("STORAGE_ACCOUNT_KEY")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

# Azure Document Intelligence
DOC_INTEL_ENDPOINT = os.getenv("DOC_INTEL_ENDPOINT")
DOC_INTEL_KEY = os.getenv("DOC_INTEL_KEY")

# Azure OpenAI
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
OPENAI_SUBSCRIPTION_KEY = os.getenv("OPENAI_SUBSCRIPTION_KEY")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")
OPENAI_DEPLOYMENT_NAME = os.getenv("OPENAI_DEPLOYMENT_NAME")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")

# Azure AI Search
SEARCH_SERVICE_ENDPOINT = os.getenv("SEARCH_SERVICE_ENDPOINT")
SEARCH_SERVICE_KEY = os.getenv("SEARCH_SERVICE_KEY")
SEARCH_INDEX_NAME = os.getenv("SEARCH_INDEX_NAME")

# === Initialize Clients ===
document_client = DocumentIntelligenceClient(
    endpoint=doc_intel_endpoint,
    credential=AzureKeyCredential(doc_intel_key)
)

openai_client = AzureOpenAI(
    api_version=openai_api_version,
    azure_endpoint=openai_endpoint,
    api_key=openai_subscription_key,
)

search_credential = AzureKeyCredential(search_service_key)
search_index_client = SearchIndexClient(endpoint=search_service_endpoint, credential=search_credential)
search_client = SearchClient(endpoint=search_service_endpoint, index_name=search_index_name, credential=search_credential)

# === Helper Functions ===
def clean_filename_for_key(filename):
    clean = filename.replace('.', '_').replace('-', '_').replace(' ', '_')
    if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-=' for c in clean):
        clean = base64.urlsafe_b64encode(filename.encode()).decode()
    return clean

def get_all_blobs_from_container():
    connect_str = f"DefaultEndpointsProtocol=https;AccountName={storage_account_name};AccountKey={storage_account_key};EndpointSuffix=core.windows.net"
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client(container_name)

    blobs = container_client.list_blobs()
    return [blob.name for blob in blobs]

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
    return blob_url

def analyze_document_from_url(blob_url):
    try:
        poller = document_client.begin_analyze_document("prebuilt-layout", {"urlSource": blob_url})
        result = poller.result()
        return result
    except Exception as e:
        print(f"❌ Error analyzing document: {e}")
        return None

def extract_text_from_result(result):
    all_text = ""
    if result and hasattr(result, 'pages'):
        for page in result.pages:
            if hasattr(page, 'lines'):
                for line in page.lines:
                    all_text += line.content + " "
    return all_text.strip()

def chunk_text(text, max_tokens=500):
    sentences = text.split('. ')
    chunks, chunk = [], ""
    for sentence in sentences:
        if len(chunk) + len(sentence) < max_tokens:
            chunk += sentence + '. '
        else:
            chunks.append(chunk.strip())
            chunk = sentence + '. '
    if chunk:
        chunks.append(chunk.strip())
    return chunks

def get_embedding(text):
    response = openai_client.embeddings.create(
        input=[text],
        model=embedding_model_name
    )
    return np.array(response.data[0].embedding)

def create_search_index():
    try:
        search_index_client.get_index(search_index_name)
        print(f"✅ Search index '{search_index_name}' already exists. Deleting to recreate...")
        search_index_client.delete_index(search_index_name)
        print("🗑️ Old index deleted.")
    except:
        print(f"ℹ️ Creating new search index '{search_index_name}'...")

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchField(name="content", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="file_name", type=SearchFieldDataType.String, filterable=True, searchable=True),
        SimpleField(name="embedding_str", type=SearchFieldDataType.String)
    ]
    
    index = SearchIndex(name=search_index_name, fields=fields)
    search_index_client.create_or_update_index(index)
    print(f"✅ Index '{search_index_name}' created.")

def upload_to_search_index(chunks, embeddings, file_name):
    clean_file_name = clean_filename_for_key(file_name)
    documents = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        embedding_str = ','.join(map(str, embedding.tolist()))
        doc = {
            "id": f"{clean_file_name}_{i}",
            "content": chunk,
            "file_name": file_name,
            "embedding_str": embedding_str
        }
        documents.append(doc)

    try:
        batch_size = 10
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            search_client.upload_documents(batch)
        print(f"📥 Uploaded {len(documents)} chunks from '{file_name}' to search index.")
    except Exception as e:
        print(f"❌ Upload failed: {e}")

# === Main Function ===
def main():
    print("📦 Fetching all documents from the existing container...")
    file_names = get_all_blobs_from_container()

    if not file_names:
        print("❌ No files found in the container.")
        return

    create_search_index()

    for file_name in file_names:
        print(f"\n📄 Processing: {file_name}")
        blob_url = generate_sas_url(file_name)
        result = analyze_document_from_url(blob_url)
        extracted_text = extract_text_from_result(result)

        if not extracted_text.strip():
            print(f"⚠️ No text extracted from '{file_name}'. Skipping.")
            continue

        chunks = chunk_text(extracted_text)
        embeddings = [get_embedding(chunk) for chunk in chunks]
        tagged_chunks = [f"[{file_name}]\n{chunk}" for chunk in chunks]

        upload_to_search_index(tagged_chunks, embeddings, file_name)

    print("\n✅ Document processing and search indexing complete.")

if __name__ == "__main__":
    main()
