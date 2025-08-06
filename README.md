# Multi-Agent Loan Automation System

An intelligent, end-to-end loan processing system powered by multiple specialized AI agents for automated loan application processing, verification, and decision making.

## 🏗️ System Architecture

### Core Components

#### 🤖 Multi-Agent System
- **Identity Verification Agent**: Document verification and identity validation
- **Income Assessment Agent**: Financial capacity and income verification
- **Guarantor Verification Agent**: Guarantor assessment and validation
- **Collateral Inspection Agent**: Property and asset inspection
- **Valuation Agent**: Asset valuation and appraisal
- **Underwriting Agent**: Risk assessment and loan decision coordination
- **Loan Offer Generation Agent**: Personalized loan offer creation
- **Customer Communication Agent**: Automated customer interactions
- **Audit Agent**: Compliance monitoring and process oversight

#### 🖥️ User Interfaces
- **Bank UI**: Comprehensive banking staff interface for loan management
- **Customer UI**: Modern customer-facing application portal
- **Documents Verification UI**: Specialized document processing interface
- **Audit UI**: Compliance and audit management dashboard
- **CUA (Computer Use Agent)**: Advanced customer analytics

#### 🔧 Supporting Services
- **Orchestrator**: Central coordination system for agent workflows
- **Index Creation**: Document indexing and search capabilities
- **REST APIs**: Microservices for pre-qualification, application, and audit processes
- **Dataset Management**: Comprehensive loan and customer data handling

### Technology Stack

#### Backend Technologies
- **Python 3.8+**: Core development language
- **FastAPI**: High-performance web framework
- **Azure AI Projects**: Agent orchestration and management
- **Azure OpenAI**: GPT-4o-mini for intelligent processing
- **Azure Cosmos DB**: Document database for customer data
- **Azure AI Search**: Document indexing and retrieval
- **Semantic Kernel**: AI workflow orchestration

#### Frontend Technologies
- **Next.js 15.0.1**: React-based web framework
- **React 18.3.1**: User interface components
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible component library
- **JavaScript/TypeScript**: Client-side logic

#### Azure Services Integration
- **Azure AI Foundry**: Agent development platform
- **Azure SQL Database**: Relational data storage
- **Azure Logic Apps**: Workflow automation

## 🚀 Getting Started

### Prerequisites

#### System Requirements
- **Python**: Version 3.8 or higher
- **Node.js**: Version 18 or higher
- **npm/yarn**: Package management
- **Git**: Version control

#### Azure Services Required
- Azure AI Foundry subscription
- Azure OpenAI Service (GPT-4o-mini deployment)
- Azure Cosmos DB account
- Azure AI Search service
- Azure SQL Database
- Azure Key Vault

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/MSFT-Innovation-Hub-India/multi-agent-loan-automation.git
cd multi-agent-loan-automation
```

#### 2. Environment Configuration
```bash
# Copy the environment template
cp .env.example .env

# Edit the .env file with your Azure credentials
nano .env  # or use your preferred editor
```

#### 3. Backend Setup

##### Install Python Dependencies
```bash
# Main orchestrator dependencies
pip install -r requirements.txt

# Individual service dependencies
cd DocumentsVerificationUI && pip install -r requirements.txt
cd ../Bank-UI && pip install -r requirements.txt
cd ../AuditUI && pip install -r requirements.txt
cd ../Index_creation && pip install -r requirements.txt
```

##### Initialize Database Indices
```bash
cd Index_creation
python cu_index.py      # Customer understanding index
python doc_index.py     # Document processing index
```

#### 4. Frontend Setup

##### Customer UI (Next.js)
```bash
cd CustomerUI/react
npm install
npm run build
```

##### Document Verification UI
```bash
cd DocumentsVerificationUI/frontend
npm install
npm run build
```

##### Audit UI
```bash
cd AuditUI/frontend
npm install
npm run build
```

### Configuration

#### Required Environment Variables
Edit your `.env` file with the following configuration:

```bash
# Azure AI Project Configuration
AZURE_AI_PROJECT_ENDPOINT=your_project_endpoint
AZURE_AI_RESOURCE_GROUP=your_resource_group
AZURE_SUBSCRIPTION_ID=your_subscription_id
AZURE_PROJECT_NAME=your_project_name

# Azure OpenAI Configuration
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_ENDPOINT=your_openai_endpoint
AZURE_OPENAI_API_KEY=your_openai_api_key

# Azure Cosmos DB Configuration
COSMOS_DB_ENDPOINT=your_cosmos_endpoint
COSMOS_DB_KEY=your_cosmos_key
COSMOS_DB_DATABASE_NAME=GlobalTrustBank
COSMOS_DB_CONTAINER_NAME=loan_applications

# Azure AI Search Indices
IDENTITY_INDEX=identity-verification-index
INCOME_INDEX=income-assessment-index
GUARANTOR_INDEX=guarantor-verification-index
INSPECTION_INDEX=collateral-inspection-index
VALUATION_INDEX=property-valuation-index

# Database Configuration (for Loan Offer Agent)
DATABASE_SERVER=your_sql_server.database.windows.net
DATABASE_NAME=Global_Trust_Bank
DATABASE_USERNAME=your_db_username
DATABASE_PASSWORD=your_db_password

# Application Configuration
DEFAULT_CUSTOMER_ID_PREFIX=CUST
LOG_LEVEL=INFO
ENVIRONMENT=development
```

## 🏃‍♂️ Running the System

### Start Backend Services

#### 1. Main Orchestrator
```bash
python orch.py
```

#### 2. Document Verification Service
```bash
cd DocumentsVerificationUI
python loan_backend.py
```

#### 3. Bank UI Service
```bash
cd Bank-UI
python app.py
```

#### 4. Customer UI Backend
```bash
cd CustomerUI/Agents
python app.py
```

#### 5. Audit Service
```bash
cd AuditUI
python audit_backend.py
```

### Start Frontend Applications

#### Customer Interface
```bash
cd CustomerUI/react
npm run dev
# Access at http://localhost:3000
```

#### Bank Staff Interface
```bash
cd Bank-UI
python app.py
# Access at http://localhost:5000
```

#### Document Verification Interface
```bash
cd DocumentsVerificationUI/frontend
npm run dev
# Access at http://localhost:3001
```

#### Audit Dashboard
```bash
cd AuditUI/frontend
npm run dev
# Access at http://localhost:3002
```

## 📊 System Features

### 🔍 Loan Processing Workflow

#### 1. Application Process
- **Pre-Qualification**: Initial eligibility assessment
- **Document Collection**: Automated document requirements
- **Application Assistance**: Step-by-step guidance
- **Document Verification**: AI-powered document validation

#### 2. Assessment Process
- **Identity Verification**: Multi-factor identity validation
- **Income Assessment**: Comprehensive financial analysis
- **Guarantor Verification**: Guarantor eligibility and validation
- **Collateral Inspection**: Property and asset evaluation
- **Risk Assessment**: Credit scoring and risk profiling

#### 3. Decision Process
- **Underwriting Analysis**: Automated risk assessment
- **Loan Structuring**: Optimal loan terms calculation
- **Approval Workflow**: Multi-level approval process
- **Offer Generation**: Personalized loan offers

#### 4. Post-Processing
- **Customer Communication**: Automated notifications
- **Documentation**: Loan agreement generation
- **Compliance Monitoring**: Regulatory compliance checks
- **Audit Trail**: Comprehensive process logging