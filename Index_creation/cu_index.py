import os
import sys
import json
import uuid
import re
import logging
from io import BytesIO
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv, find_dotenv

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType
)
# Load environment variables
load_dotenv(find_dotenv())

# Setup logging
logging.basicConfig(level=logging.INFO)


# Azure endpoints and keys (imported from config)
from .cu_index_config import (
    AZURE_AI_ENDPOINT,
    AZURE_AI_API_VERSION,
    SEARCH_ENDPOINT,
    SEARCH_KEY,
    INDEX_NAME
)

# Content Understanding Client
sys.path.append(str(Path(__file__).parent.parent))
from python.content_understanding_client import AzureContentUnderstandingClient

credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")

client = AzureContentUnderstandingClient(
    endpoint=AZURE_AI_ENDPOINT,
    api_version=AZURE_AI_API_VERSION,
    token_provider=token_provider,
)

# Azure AI Search Clients
search_credential = AzureKeyCredential(SEARCH_KEY)
index_client = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=search_credential)
search_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=INDEX_NAME, credential=search_credential)

# Create index
def create_search_index():
    try:
        fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
    SearchableField(name="metadata", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
]
        index = SearchIndex(name=INDEX_NAME, fields=fields)
        index_client.create_index(index)
        print(f"Index '{INDEX_NAME}' created.")
    except Exception as e:
        print(f"Index creation skipped: {e}")

# Save keyframe image
def save_image(image_id: str, response):
    try:
        raw_image = client.get_image_from_analyze_operation(
            analyze_response=response,
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

    
'''def save_image(image_id: str, response):
    try:
        raw_image = client.get_image_from_analyze_operation(
            analyze_response=response,
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
        logging.error(f"Failed to save image {image_id}: {e}")

# Process file through Azure CU
def process_and_index(modality_name, analyzer_template_path, sample_file_path):
    analyzer_id = f"{modality_name}-{uuid.uuid4()}"
    print(f"\nProcessing: {sample_file_path} with {analyzer_template_path}")

    response = client.begin_create_analyzer(analyzer_id, analyzer_template_path=analyzer_template_path)
    client.poll_result(response)

    response = client.begin_analyze(analyzer_id, file_location=sample_file_path)
    result = client.poll_result(response)
    client.delete_analyzer(analyzer_id)

    print(json.dumps(result, indent=2))

    documents = []
    result_data = result.get("result", {})
    contents = result_data.get("contents", [])

    keyframe_ids = set()
    for idx, item in enumerate(contents):
        content_text = item.get("text") or item.get("transcript") or item.get("markdown") or ""
        metadata = json.dumps(item.get("metadata", {}))
        documents.append({
            "id": f"{modality_name}-{idx}",
            "content": content_text,
            "metadata": metadata,
        })

        # Extract keyframe image IDs (video)
        if isinstance(item.get("markdown", ""), str):
            keyframe_ids.update(re.findall(r"(keyFrame\.\d+)\.jpg", item["markdown"]))

    if documents:
        search_client.upload_documents(documents=documents)
        print(f"Uploaded {len(documents)} documents from {modality_name}")

    for keyframe_id in keyframe_ids:
        save_image(keyframe_id, response)'''

def process_and_index(modality_name, analyzer_template_path, sample_file_path):
    analyzer_id = f"{modality_name}-{uuid.uuid4()}"
    print(f"\nProcessing: {sample_file_path} with {analyzer_template_path}")

    response = client.begin_create_analyzer(analyzer_id, analyzer_template_path=analyzer_template_path)
    client.poll_result(response)

    response = client.begin_analyze(analyzer_id, file_location=sample_file_path)
    result = client.poll_result(response)
    client.delete_analyzer(analyzer_id)

    print(json.dumps(result, indent=2))

    documents = []
    keyframe_ids = set()

    result_data = result.get("result", {})
    contents = result_data.get("contents", [])

    for idx, item in enumerate(contents):
        content_text = item.get("text") or item.get("transcript") or item.get("markdown") or ""
        metadata = json.dumps(item.get("metadata", {}))

        documents.append({
            "id": f"{modality_name}-{idx}",
            "content": content_text,
            "metadata": metadata,
        })

        # Look for actual image references in the metadata
        if modality_name == "video":
            media_info = item.get("metadata", {}).get("media", {})
            image_id = media_info.get("imageId")
            if image_id:
                keyframe_ids.add(image_id)

    # Upload documents to Azure AI Search
    if documents:
        search_client.upload_documents(documents=documents)
        print(f"Uploaded {len(documents)} documents from {modality_name}")

    # Save only valid keyframe images
    for keyframe_id in keyframe_ids:
        try:
            save_image(keyframe_id, response)
        except Exception as e:
            logging.warning(f"Failed to save keyframe image {keyframe_id}: {e}")

# Entry point
if __name__ == "__main__":
    create_search_index()

    # Document
    process_and_index(
        modality_name="document",
        analyzer_template_path="./analyzer_templates/content_document.json",
        sample_file_path="./data/invoice.pdf"
    )

    # Audio
    process_and_index(
        modality_name="audio",
        analyzer_template_path="./analyzer_templates/audio_transcription.json",
        sample_file_path="./data/audio.wav"
    )

    # Video
    process_and_index(
        modality_name="video",
        analyzer_template_path="./analyzer_templates/content_video.json",
        sample_file_path="./data/FlightSimulator.mp4"
    )

    print("🎯 All content extracted and indexed successfully.")