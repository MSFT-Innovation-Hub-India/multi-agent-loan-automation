# Index Creation Module

This module provides functionality for creating and managing Azure AI Search indexes using various Azure services including Azure AI, Azure Blob Storage, Azure Document Intelligence, and Azure OpenAI.

## Features

- **Content Understanding Index Creation** (`cu_index.py`): Creates indexes using Azure Content Understanding services for documents, audio, and video content
- **Document Index Creation** (`doc_index.py`): Creates indexes using Azure Document Intelligence for document processing and embedding generation

## Setup

### Prerequisites

- Python 3.8+
- Azure subscription with the following services configured:
  - Azure AI Services
  - Azure Blob Storage
  - Azure Document Intelligence
  - Azure OpenAI
  - Azure AI Search

### Installation

1. Install required Python packages:
```bash
pip install azure-storage-blob azure-ai-documentintelligence azure-search-documents azure-identity openai python-dotenv pillow numpy
```

2. Copy the environment template:
```bash
cp .env.example .env
```

3. Configure your Azure credentials in the `.env` file:
```bash
# Azure AI Configuration
AZURE_AI_ENDPOINT=https://your-ai-endpoint.services.ai.azure.com/
AZURE_AI_API_VERSION=2024-12-01-preview

# Azure Blob Storage Configuration
STORAGE_ACCOUNT_NAME=your-storage-account-name
STORAGE_ACCOUNT_KEY=your-storage-account-key
CONTAINER_NAME=your-container-name

# Azure Document Intelligence Configuration
DOC_INTEL_ENDPOINT=https://your-doc-intel-endpoint.cognitiveservices.azure.com/
DOC_INTEL_KEY=your-document-intelligence-key

# Azure OpenAI Configuration
OPENAI_ENDPOINT=https://your-openai-endpoint.openai.azure.com/
OPENAI_SUBSCRIPTION_KEY=your-openai-subscription-key
OPENAI_API_VERSION=2023-05-15
OPENAI_DEPLOYMENT_NAME=your-gpt-deployment-name
EMBEDDING_MODEL_NAME=text-embedding-ada-002

# Azure AI Search Configuration
SEARCH_ENDPOINT=https://your-search-service.search.windows.net
SEARCH_SERVICE_ENDPOINT=https://your-search-service.search.windows.net
SEARCH_KEY=your-search-service-key
SEARCH_SERVICE_KEY=your-search-service-key
SEARCH_INDEX_NAME=your-index-name
INDEX_NAME=your-index-name
```

## Usage

### Content Understanding Index (`cu_index.py`)

This script processes multimodal content (documents, audio, video) from Azure Blob Storage and creates search indexes.

```bash
python cu_index.py
```

Features:
- Interactive mode for selecting customers and document types
- Support for document, audio, and video content analysis
- Automatic content extraction and indexing
- SAS token generation for secure blob access

### Document Index (`doc_index.py`)

This script processes documents using Azure Document Intelligence and creates embeddings-based search indexes.

```bash
python doc_index.py
```

Features:
- Document text extraction using Azure Document Intelligence
- Text chunking and embedding generation
- Customer and document type organization
- Batch processing capabilities

You can also run with command line arguments:
```bash
python doc_index.py CUST0001 Identity
```

## File Structure

```
Index_creation/
├── cu_index.py              # Content Understanding index creation
├── cu_index_config.py       # Configuration for Content Understanding
├── doc_index.py             # Document Intelligence index creation  
├── doc_index_config.py      # Configuration for Document Intelligence
├── README.md                # This file
├── .env.example             # Environment variables template
├── .env                     # Your actual environment variables (git ignored)
├── .gitignore              # Git ignore rules
└── Vectordb/               # Vector database storage (git ignored)
```

## Expected Blob Storage Structure

The scripts expect the following folder structure in your Azure Blob Storage container:

```
Container/
├── CUST0001/
│   ├── Identity/
│   │   ├── document1.pdf
│   │   └── document2.jpg
│   ├── Income/
│   │   └── payslip.pdf
│   └── Collateral/
│       └── property_docs.pdf
├── CUST0002/
│   └── Identity/
│       └── id_card.jpg
└── ...
```

## Security Notes

- Never commit your `.env` file to version control
- Use Azure Key Vault for production environments
- Regularly rotate your API keys and access tokens
- Ensure proper access controls on your Azure resources

## Troubleshooting

1. **Authentication Issues**: Verify your Azure credentials in the `.env` file
2. **Blob Access Issues**: Check your storage account key and container permissions
3. **Search Index Issues**: Ensure your Azure AI Search service is properly configured
4. **Processing Errors**: Check the container structure matches the expected format

## Contributing

When making changes:
1. Update the `.env.example` file if new environment variables are added
2. Update this README with any new features or configuration changes
3. Ensure all hardcoded values are moved to environment variables