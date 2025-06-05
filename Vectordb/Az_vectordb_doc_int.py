# === Imports ===
import os
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta, timezone

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceExistsError

# Load environment variables
load_dotenv()

# === Configuration Section ===
# Azure Blob Storage credentials
storage_account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
storage_account_key = os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
container_name = os.environ.get("AZURE_STORAGE_CONTAINER_NAME")

# Azure Document Intelligence credentials
doc_intel_endpoint = os.environ.get("AZURE_DOC_INTEL_ENDPOINT")
doc_intel_key = os.environ.get("AZURE_DOC_INTEL_KEY")

# Azure OpenAI credentials
openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
openai_subscription_key = os.environ.get("AZURE_OPENAI_KEY")
openai_api_version = os.environ.get("AZURE_OPENAI_API_VERSION")
openai_deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
embedding_model_name = os.environ.get("AZURE_OPENAI_EMBEDDING_MODEL")

# Azure Cosmos DB configuration
cosmos_endpoint = os.environ.get("AZURE_COSMOS_ENDPOINT")
cosmos_key = os.environ.get("AZURE_COSMOS_KEY")
cosmos_db_name = os.environ.get("AZURE_COSMOS_DB_NAME")
cosmos_container_name = os.environ.get("AZURE_COSMOS_CONTAINER_NAME")

# === Initialize Clients ===
# Initialize Document Intelligence Client
document_client = DocumentIntelligenceClient(
    endpoint=doc_intel_endpoint, 
    credential=AzureKeyCredential(doc_intel_key)
)

# Initialize Azure OpenAI Client
openai_client = AzureOpenAI(
    api_version=openai_api_version, 
    azure_endpoint=openai_endpoint, 
    api_key=openai_subscription_key
)

# Initialize Cosmos DB Client
cosmos_client = CosmosClient(cosmos_endpoint, credential=cosmos_key)
cosmos_db = cosmos_client.create_database_if_not_exists(id=cosmos_db_name)

# Fixed container initialization with proper error handling
try:
    # Get the container client
    cosmos_container = cosmos_db.get_container_client(cosmos_container_name)
    
    # Test if container exists by querying it with cross-partition enabled
    list(cosmos_container.query_items(
        query="SELECT TOP 1 * FROM c", 
        max_item_count=1,
        enable_cross_partition_query=True  # This is the key fix
    ))
    print(f"Container '{cosmos_container_name}' already exists.")
except Exception as e:
    # Check if the error message suggests the container doesn't exist
    if "Resource Not Found" in str(e):
        print(f"Creating container '{cosmos_container_name}'...")
        try:
            cosmos_container = cosmos_db.create_container(
                id=cosmos_container_name,
                partition_key=PartitionKey(path="/fileName")
            )
        except CosmosResourceExistsError:
            # If container was created between our check and creation attempt
            cosmos_container = cosmos_db.get_container_client(cosmos_container_name)
    else:
        # Log the error but continue - we'll try to create the container anyway
        print(f"Error accessing Cosmos DB container: {e}")
        try:
            print(f"Attempting to create container '{cosmos_container_name}'...")
            cosmos_container = cosmos_db.create_container(
                id=cosmos_container_name,
                partition_key=PartitionKey(path="/fileName")
            )
        except CosmosResourceExistsError:
            # If it already exists, get it
            print(f"Container already exists, retrieving it...")
            cosmos_container = cosmos_db.get_container_client(cosmos_container_name)

# === Helper Functions ===
def upload_file_to_blob(file_path):
    """Upload a file to Azure Blob Storage and return the file name."""
    connect_str = f"DefaultEndpointsProtocol=https;AccountName={storage_account_name};AccountKey={storage_account_key};EndpointSuffix=core.windows.net"
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client(container_name)

    try:
        container_client.get_container_properties()
    except Exception:
        print(f"Creating blob container '{container_name}'...")
        container_client.create_container()

    file_name = os.path.basename(file_path)
    blob_client = container_client.get_blob_client(file_name)
    
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

    print(f"Uploaded: {file_name}")
    return file_name

def generate_sas_url(file_name):
    """Generate a SAS URL for accessing the blob."""
    sas_token = generate_blob_sas(
        account_name=storage_account_name,
        container_name=container_name,
        blob_name=file_name,
        account_key=storage_account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    return f"https://{storage_account_name}.blob.core.windows.net/{container_name}/{file_name}?{sas_token}"

def analyze_document_from_url(blob_url):
    """Analyze a document using Azure Document Intelligence service."""
    try:
        poller = document_client.begin_analyze_document("prebuilt-layout", {"urlSource": blob_url})
        result = poller.result()
        return result
    except Exception as e:
        print(f"Document analysis error: {e}")
        return None

def extract_text_from_result(result):
    """Extract text content from Document Intelligence result."""
    all_text = ""
    if result and hasattr(result, 'pages'):
        for page in result.pages:
            if hasattr(page, 'lines'):
                for line in page.lines:
                    all_text += line.content + " "
    return all_text.strip()

def chunk_text(text, max_tokens=500):
    """Split text into chunks of approximately max_tokens size, respecting sentence boundaries."""
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
    """Get embedding vector for text using Azure OpenAI API."""
    try:
        response = openai_client.embeddings.create(input=[text], model=embedding_model_name)
        return np.array(response.data[0].embedding)
    except Exception as e:
        print(f"Error generating embedding: {e}")
        # Return a zero vector as fallback
        return np.zeros(1536)  # Default dimension for text-embedding-ada-002

def store_chunks_in_cosmos(file_name, chunks, embeddings):
    """Store document chunks and their embeddings in Cosmos DB."""
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        try:
            doc = {
                "id": f"{file_name}_{i}",
                "fileName": file_name,
                "chunkIndex": i,
                "chunkText": chunk,
                "embedding": embedding.tolist(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            cosmos_container.upsert_item(doc)
        except Exception as e:
            print(f"Error storing chunk {i} from {file_name}: {e}")
    
    print(f"Stored {len(chunks)} chunks in Cosmos DB for '{file_name}'")

def upload_and_analyze_documents(file_paths):
    """Process multiple documents: upload, analyze, chunk, and store."""
    all_chunks = []
    all_embeddings = []
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue

        try:
            # Upload file to blob storage
            file_name = upload_file_to_blob(file_path)
            
            # Generate SAS URL for the uploaded blob
            blob_url = generate_sas_url(file_name)
            
            # Analyze document using Document Intelligence
            print(f"Analyzing document: {file_name}...")
            result = analyze_document_from_url(blob_url)
            
            # Extract text from the analysis result
            extracted_text = extract_text_from_result(result)
            
            if not extracted_text.strip():
                print(f"No text extracted from {file_name}")
                continue
            
            # Split text into manageable chunks
            print(f"Chunking extracted text...")
            chunks = chunk_text(extracted_text)
            
            # Generate embeddings for each chunk
            print(f"Generating embeddings for {len(chunks)} chunks...")
            embeddings = []
            for chunk in chunks:
                embedding = get_embedding(chunk)
                embeddings.append(embedding)
            
            # Tag chunks with source file name
            tagged_chunks = [f"[{file_name}]\n{chunk}" for chunk in chunks]
            all_chunks.extend(tagged_chunks)
            all_embeddings.extend(embeddings)
            
            # Store chunks and embeddings in Cosmos DB
            store_chunks_in_cosmos(file_name, chunks, embeddings)
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    if all_chunks:
        return all_chunks, np.array(all_embeddings)
    else:
        print("No documents were successfully processed.")
        return [], np.array([])

def list_available_models():
    """List available OpenAI models in the Azure resource."""
    try:
        models = openai_client.models.list()
        print("\nAvailable models:")
        for model in models:
            print(f"- {model.id}")
        return [model.id for model in models]
    except Exception as e:
        print(f"Error listing models: {e}")
        return []

def get_working_model():
    """Find a working chat model deployment."""
    try:
        models = list_available_models()
        
        # Try a few common model deployment names
        candidate_models = [
            openai_deployment_name,  # Try the configured one first
            "gpt-35-turbo", 
            "gpt-4",
            "gpt-35",
            "gpt35",
            "gpt-3.5-turbo"
        ]
        
        # First check if any of our candidates are in the available models
        for model in candidate_models:
            if model in models:
                print(f"Using model deployment: {model}")
                return model
                
        # If we have any models at all, use the first one that looks like a chat model
        for model in models:
            if any(name in model.lower() for name in ["gpt", "chat", "turbo"]):
                print(f"Using model deployment: {model}")
                return model
                
        # If we get here, we couldn't find a suitable model
        print("Warning: Couldn't find a suitable chat model. Using default name.")
        return openai_deployment_name
        
    except Exception as e:
        print(f"Error finding working model: {e}")
        return openai_deployment_name

def chat_with_multi_docs(chunks, chunk_embeddings):
    """Interactive chat interface that retrieves relevant document chunks."""
    if len(chunks) == 0:
        print("No document content available for chat. Please process documents first.")
        return
        
    print("\n🧠 Document Intelligence Agent is ready. Type your questions. Type 'exit' to quit.\n")
    
    # Find a working model deployment
    model = get_working_model()
    
    while True:
        user_query = input("You: ").strip()
        
        if user_query.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
            
        if not user_query:
            print("Please enter a question.")
            continue
            
        try:
            # Generate embedding for the user query
            print("Finding relevant information...")
            query_embedding = get_embedding(user_query).reshape(1, -1)
            
            # Calculate cosine similarity between query and all document chunks
            sims = cosine_similarity(query_embedding, chunk_embeddings)[0]
            
            # Get indices of top 3 most similar chunks
            top_indices = np.argsort(sims)[-3:][::-1]
            
            # Combine the top chunks as context
            context = "\n\n".join([chunks[i] for i in top_indices])
            
            # Generate response using Azure OpenAI
            system_prompt = f"""You are a helpful assistant answering based only on the document context below. 
If the answer is not in the context, say that you don't have enough information. 
Be concise and focus on answering the user's question.

Context:
{context}
"""
            print("Generating response...")
            try:
                response = openai_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_query},
                    ],
                    max_tokens=800,
                    temperature=0.2,
                    model=model,
                )
                
                reply = response.choices[0].message.content
                print(f"\nAgent: {reply}\n")
            
            except Exception as chat_error:
                print(f"Error with OpenAI chat: {chat_error}")
                
                # Fallback to simple response based on top chunk
                print("\nFallback mode: Showing most relevant document section:")
                print(f"\nAgent: I found this relevant information in your documents:\n")
                print(chunks[top_indices[0]])
                print("\n(Note: AI response generation failed. Showing raw document content instead.)")
            
        except Exception as e:
            print(f"Error: {e}")
            print("Sorry, I encountered an error processing your question. Please try again.")

def load_chunks_from_cosmos():
    """Load all document chunks from Cosmos DB."""
    try:
        print("Loading document chunks from database...")
        query = "SELECT * FROM c"
        
        # Enable cross-partition query
        items = list(cosmos_container.query_items(
            query=query, 
            enable_cross_partition_query=True  # This is critical for querying across partitions
        ))
        
        if not items:
            print("No chunks found in the database.")
            return [], np.array([])
            
        chunks = []
        embeddings = []
        
        for item in items:
            file_name = item.get("fileName", "unknown")
            chunk_text = item.get("chunkText", "")
            embedding = item.get("embedding", [])
            
            if chunk_text and embedding:
                chunks.append(f"[{file_name}]\n{chunk_text}")
                embeddings.append(np.array(embedding))
        
        print(f"Loaded {len(chunks)} chunks from the database.")
        return chunks, np.array(embeddings)
        
    except Exception as e:
        print(f"Error loading from Cosmos DB: {e}")
        return [], np.array([])

# === Main Function ===
def main():
    print("=== Document Intelligence Agent ===")
    print("This agent can process documents, extract text, and answer questions about their content.")
    
    # Global variables to store chunks and embeddings
    global_chunks = []
    global_embeddings = np.array([])
    
    while True:
        print("\nOptions:")
        print("1. Process documents")
        print("2. Chat with processed documents")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            file_input = input("Enter file paths (comma-separated): ").strip()
            file_paths = [fp.strip() for fp in file_input.split(",") if fp.strip()]
            
            if not file_paths:
                print("No files provided.")
                continue
                
            all_chunks, all_embeddings = upload_and_analyze_documents(file_paths)
            
            if len(all_chunks) > 0:
                global_chunks = all_chunks
                global_embeddings = all_embeddings
                print(f"\nSuccessfully processed {len(file_paths)} documents into {len(all_chunks)} chunks.")
                
                # Ask if user wants to chat now
                chat_now = input("Do you want to chat with these documents now? (y/n): ").strip().lower()
                if chat_now in ["y", "yes"]:
                    chat_with_multi_docs(global_chunks, global_embeddings)
            
        elif choice == "2":
            # First check if we have chunks in memory
            if len(global_chunks) > 0:
                chat_with_multi_docs(global_chunks, global_embeddings)
            else:
                # Try to load chunks from Cosmos DB
                loaded_chunks, loaded_embeddings = load_chunks_from_cosmos()
                if len(loaded_chunks) > 0:
                    global_chunks = loaded_chunks
                    global_embeddings = loaded_embeddings
                    chat_with_multi_docs(global_chunks, global_embeddings)
                else:
                    print("No documents have been processed yet. Please process documents first.")
        
            
        elif choice == "3":
            print("Exiting program. Goodbye!")
            break
            
        else:
            print("Invalid choice. Please enter 1, 2, 3")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting gracefully.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")