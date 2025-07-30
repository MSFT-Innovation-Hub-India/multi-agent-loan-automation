# AuditUI - Multi-Agent Audit Summary System

## Overview

The AuditUI is a specialized web-based interface designed for generating comprehensive audit summary reports for loan applications. This system combines a React + Next.js frontend with a FastAPI backend powered by Azure AI agents to deliver automated audit analysis and reporting capabilities for financial institutions and compliance teams.

## Features

### 🔍 Audit Analysis
- **Comprehensive Audit Reports**: Generate detailed audit summaries for loan applications
- **Audit Trail Tracking**: Complete audit history and compliance tracking
- **Status Monitoring**: Real-time audit status updates and progress tracking

### 🤖 AI-Powered Features
- **Azure AI Agent Integration**: Powered by Semantic Kernel and Azure AI Projects
- **Intelligent Data Processing**: Automated audit data analysis and formatting
- **API-Driven Operations**: Seamless integration with audit databases and systems
- **Dynamic Report Generation**: Context-aware audit summaries based on loan data

## Architecture

### Frontend (Next.js)
- **Framework**: Next.js 15.0.1 with React 18.3.1
- **UI Components**: Radix UI components with Tailwind CSS
- **Port Configuration**: Runs on port 3001 
- **State Management**: React hooks for audit session management
- **Responsive Design**: Professional interface optimized for audit workflows

### Backend (FastAPI)
- **Framework**: FastAPI with Python 3.8+
- **AI Integration**: Azure AI Agent with Semantic Kernel
- **API Operations**: OpenAPI-powered audit data retrieval
- **Port Configuration**: Runs on port 8001
- **Authentication**: Azure Identity integration for secure access

## Prerequisites

Before setting up the AuditUI system, ensure you have the following:

### System Requirements
- **Node.js**: Version 18 or higher
- **Python**: Version 3.8 or higher
- **npm or yarn**: For frontend package management
- **pip**: For Python package management

### Azure Services Required
- **Azure AI Foundry**: For agent orchestration and audit processing
- **Azure OpenAI**: For GPT-4o-mini model access
- **Azure AI Projects**: For semantic kernel integration

### API Keys and Connections
- Azure AI Project Connection String
- GPT-4o-mini deployment access
- Audit database API access

## Installation & Setup

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd multi-agent-loan-automation/AuditUI
```

### Step 2: Backend Setup

#### 2.1 Install Python Dependencies
```bash
# Navigate to AuditUI directory
cd AuditUI
pip install -r requirements.txt
```

#### 2.2 Create Backend Environment File
Create a `.env` file in the `AuditUI` directory with the following configuration:

```bash
# Environment variables for Audit Summary Agent
# Azure AI Project Configuration
AZURE_AI_AGENT_PROJECT_CONNECTION_STRING='YOUR_PROJECT_CONNECTION_STRING'
AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME='YOUR_DEPLOYMENT_MODEL'

# API Configuration
API_HOST=127.0.0.1
API_PORT=8001
```

### Step 3: Frontend Setup (React Application)

#### 3.1 Navigate to Frontend Directory and Install Dependencies
```bash
cd frontend
npm install
# or
yarn install
```

#### 3.2 Create Frontend Environment File
Create a `.env.local` file in the `frontend` directory:

```bash
# Backend API Configuration
NEXT_PUBLIC_AUDIT_BACKEND_URL=http://localhost:8001
```

## Running the Application

### Step 1: Start the Backend Server
```bash
cd AuditUI
python audit_backend.py
```

The backend server will start on `http://localhost:8001`

**Verify Backend is Running:**
- API Documentation: `http://localhost:8001/docs`
- Health Check: `http://localhost:8001/health`

### Step 2: Start the Frontend Application
```bash
cd AuditUI/frontend
npm run dev
# or
yarn dev
```

The frontend application will start on `http://localhost:3001`

### Step 3: Access the Application
Open your browser and navigate to `http://localhost:3001`

## User Guide

### Getting Started with the Audit Interface

1. **Initial Setup**
   - Ensure both backend and frontend servers are running
   - Open the application in your browser at `http://localhost:3001`
   - Verify the welcome message appears in the interface

2. **Generating Audit Reports**
   - Enter a customer name in the input field
   - Wait for the AI agent to process the request and generate the report

3. **Understanding Audit Reports**
   The system generates comprehensive reports with:
   - **Customer Information**: ID, name, loan details, and application status
   - **Detailed Audit Trail**: Complete audit history with timestamps and status
   - **Overview Summary**: Comprehensive analysis and recommendations

### File Structure
```
AuditUI/
├── audit_backend.py                    # Main FastAPI server
├── audit_summary_agent_sk.py           # Standalone agent script
├── instructions.txt                    # Agent instructions configuration
├── audit_agent.json                   # OpenAPI specification for audit tools
├── frontend/                           # Frontend Next.js application
│   ├── src/
│   │   ├── app/                        # Next.js app directory
│   │   │   ├── page.tsx               # Main page component
│   │   │   ├── audit-interface.tsx     # Audit interface component
│   │   │   ├── layout.tsx             # Application layout
│   │   │   └── globals.css            # Global styles
│   │   ├── components/
│   │   │   └── ui/                    # UI components
│   │   │       ├── button.tsx         # Button component
│   │   │       └── input.tsx          # Input component
│   │   └── lib/
│   │       └── utils.ts               # Utility functions
│   ├── public/                        # Static assets
│   ├── package.json                   # Node.js dependencies
│   ├── next.config.ts                 # Next.js configuration
│   └── tailwind.config.ts             # Tailwind CSS configuration
└── README.md                          # This file
```

## License

Internal use only - Microsoft Innovation Hub India
Confidential and proprietary software

---

*Last Updated: July 30, 2025*
*Version: 1.0.0*
