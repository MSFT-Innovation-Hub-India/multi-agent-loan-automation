# Multi-Agent Loan Automation

An intelligent loan processing system using multiple specialized AI agents for automated loan application processing, verification, and decision making.

## Environment Setup

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Configure your environment variables:**
   Edit the `.env` file and replace placeholder values with your actual Azure service credentials:

   - **Azure AI Project**: Your Azure ML project configuration
   - **Azure OpenAI**: Your OpenAI service endpoint and API key
   - **Cosmos DB**: Your Cosmos DB connection details
   - **Agent Indices**: Your Azure AI Search index names for each agent

3. **Required Azure Services:**
   - Azure OpenAI Service
   - Azure Cosmos DB
   - Azure AI Search (for document indexing)
   - Azure AI Studio/ML (for project management)

## Security Note

- Never commit your `.env` file to version control
- The `.env` file contains sensitive API keys and connection strings
- Use Azure Key Vault for production deployments