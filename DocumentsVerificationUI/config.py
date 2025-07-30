# Azure AI Project Configuration
ENDPOINT = "https://eastus2.api.azureml.ms"
RESOURCE_GROUP = "rg-kushikote-9315_ai"
SUBSCRIPTION_ID = "055cefeb-8cfd-4996-b2d5-ee32fa7cf4d4"
PROJECT_NAME = "docstorage"

# Azure AI Search Indexes for each agent
INDEXES = {
    "identity": "identityindex",
    "income": "rag-1749535545848", 
    "guarantor": "gua",
    "inspection": "hou",
    "valuation": "rag-1750155157603"
}

# Connection ID for AI Search (fallback)
DEFAULT_SEARCH_CONNECTION_ID = "/subscriptions/055cefeb-8cfd-4996-b2d5-ee32fa7cf4d4/resourceGroups/rg-kushikote-9315_ai/providers/Microsoft.MachineLearningServices/workspaces/docstorage/connections/dataexc"
