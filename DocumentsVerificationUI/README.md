# Documents Verification UI

This module provides a comprehensive loan evaluation system with multiple specialized AI agents for document verification and analysis. It includes both a FastAPI backend service and a Next.js frontend interface.

## Overview

The Documents Verification UI is a multi-agent system designed to automate and streamline the loan approval process by analyzing various types of documents and materials submitted by loan applicants. The system employs specialized AI agents, each focused on a specific aspect of the verification process.

## Architecture

### Backend (FastAPI)
- **Main Service**: `loan_backend.py` - FastAPI application providing REST API endpoints
- **Configuration**: `config.py` - Azure AI project configuration and search indexes
- **Agents Directory**: Contains specialized verification agents

### Frontend (Next.js)
- **Technology**: Next.js 15.4.1 with TypeScript
- **UI Framework**: Tailwind CSS with Radix UI components
- **Port**: Runs on port 3001

## Specialized Agents

### 1. Identity Agent (`identity_agent.py`)
- **Purpose**: Verifies identity documents (Aadhaar, PAN, address proof)
- **Extracts**: Name, DOB, PAN number, Aadhaar number, complete address
- **Validates**: Document authenticity and consistency across documents

### 2. Income Agent (`income_agent.py`)
- **Purpose**: Analyzes income documents and financial eligibility
- **Analyzes**: Salary slips, bank statements, Form 16
- **Assesses**: Monthly income, employment status, financial capacity

### 3. Guarantor Agent (`gua.py`)
- **Purpose**: Evaluates guarantor verification through call recordings
- **Analyzes**: Call recordings, guarantor consent, financial standing
- **Assesses**: Guarantor reliability and willingness to guarantee

### 4. Inspection Agent (`insp.py`)
- **Purpose**: Analyzes property inspection videos
- **Evaluates**: Property condition, structural integrity, maintenance level
- **Assesses**: Collateral suitability and risk factors

### 5. Valuation Agent (`val_agent.py`)
- **Purpose**: Determines property value from sale deeds and documents
- **Calculates**: Current market value with appreciation rates
- **Evaluates**: Property as loan collateral

## Azure Integration

The system leverages Azure AI services:
- **Azure AI Projects**: For agent creation and management
- **Azure AI Search**: For document indexing and retrieval
- **Azure OpenAI**: GPT-4o model for document analysis
- **Azure Identity**: For authentication and authorization

## API Endpoints

### Core Endpoints
- `GET /` - API information and status
- `GET /health` - Health check and system status
- `POST /api/evaluation/complete` - Run complete loan evaluation
- `POST /api/evaluation/agent` - Run single agent evaluation
- `GET /api/agents/list` - List available agents
- `GET /api/evaluation/results` - Get last evaluation results

### Administrative Endpoints
- `POST /api/evaluation/summary` - Generate summary from existing results
- `GET /api/system/diagnostics` - System diagnostic information

## Installation and Setup

### Prerequisites
- Python 3.8 or higher
- Node.js 18 or higher
- Azure subscription with AI services configured
- Azure AI Studio project setup

### Backend Setup

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Azure Settings**:
   Update `config.py` with your Azure AI project details:
   ```python
   ENDPOINT = "https://your-region.api.azureml.ms"
   RESOURCE_GROUP = "your-resource-group"
   SUBSCRIPTION_ID = "your-subscription-id"
   PROJECT_NAME = "your-project-name"
   ```

3. **Start the Backend Server**:
   ```bash
   python loan_backend.py
   ```
   Server will start on `http://127.0.0.1:8001`

### Frontend Setup

1. **Navigate to Frontend Directory**:
   ```bash
   cd frontend
   ```

2. **Install Node.js Dependencies**:
   ```bash
   npm install
   ```

3. **Start the Development Server**:
   ```bash
   npm run dev
   ```
   Frontend will be available on `http://localhost:3001`

## Configuration

### Azure AI Search Indexes
The system uses specific indexes for each agent:
```python
INDEXES = {
    "identity": "identityindex",
    "income": "incomeindex",
    "guarantor": "guaindex",
    "inspection": "houseinspectionindex",
    "valuation": "housevalindex"
}
```

### Environment Variables
Create a `.env.local` file in the frontend directory for environment-specific settings.

## Usage

### Complete Loan Evaluation
```bash
curl -X POST "http://127.0.0.1:8001/api/evaluation/complete" \
     -H "Content-Type: application/json" \
     -d '{"customer_name": "John Doe", "loan_type": "Home Loan"}'
```

### Single Agent Evaluation
```bash
curl -X POST "http://127.0.0.1:8001/api/evaluation/agent" \
     -H "Content-Type: application/json" \
     -d '{"agent_type": "identity"}'
```

## Features

### Multi-Agent Processing
- Parallel processing of different document types
- Specialized analysis for each verification area
- Comprehensive final summary generation

### Document Analysis
- OCR and text extraction from various document formats
- Pattern recognition for official documents
- Cross-validation between different document sources

### Real-time API
- RESTful API for easy integration
- Background task processing
- Real-time status updates

### User Interface
- Modern, responsive web interface
- Real-time progress tracking
- Detailed results visualization
- Agent-specific result breakdown

## Error Handling

The system includes comprehensive error handling:
- Azure service connection failures
- Document processing errors
- Agent initialization issues
- API validation errors

## Troubleshooting

### Common Issues

1. **Azure Connection Errors**:
   - Verify Azure credentials with `az login`
   - Check Azure AI Studio project configuration
   - Ensure proper subscription permissions

2. **Agent Initialization Failures**:
   - Confirm all required indexes exist in Azure AI Search
   - Verify project connection strings
   - Check resource group and subscription settings

3. **Document Processing Issues**:
   - Ensure documents are properly indexed
   - Verify search connection configurations
   - Check agent-specific index mappings

### Diagnostic Tools

Run system diagnostics:
```bash
curl -X GET "http://127.0.0.1:8001/api/system/diagnostics"
```

## Development

### Adding New Agents
1. Create new agent file in `agents/` directory
2. Follow the existing agent pattern with Azure AI Search integration
3. Update the `INDEXES` configuration
4. Add agent to the evaluation system

### Extending Functionality
- Add new document types to existing agents
- Implement additional validation rules
- Enhance the final summary generation logic

## Dependencies

### Python Backend
- FastAPI 0.104.1 - Web framework
- Azure AI Projects 1.0.0b4 - AI agent framework
- Azure Identity 1.15.0 - Authentication
- Pydantic 2.4.2 - Data validation
- Uvicorn 0.24.0 - ASGI server

### Node.js Frontend
- Next.js 15.4.1 - React framework
- TypeScript 5 - Type safety
- Tailwind CSS 3.4.1 - Styling
- Radix UI - Component library


