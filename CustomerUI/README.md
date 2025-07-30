# CustomerUI - Multi-Agent Loan Automation System

## Overview

The CustomerUI is a comprehensive web-based interface that provides a modern chat experience for customers to interact with AI-powered loan processing agents. This system combines a React + Next.js frontend with a FastAPI backend to deliver real-time communication capabilities, allowing customers to navigate through their loan application process seamlessly.

## Features

### 🤖 Multi-Agent Support
- **Pre-Qualification Agent**: Initial eligibility assessment and guidance
- **Application Assist Agent**: Step-by-step application completion support
- **Audit Agent**: Compliance monitoring and process verification

### 💬 Real-Time Chat Interface
- Interactive chat experience with AI agents
- Real-time audio and text communication
- Voice Activity Detection (VAD) support
- Streaming responses for immediate feedback
- Message history and conversation threading

### 🎙️ Audio Features
- Audio recording and playback capabilities
- Real-time audio streaming
- Voice-to-text conversion

## Architecture

### Frontend (Next.js)
- **Framework**: Next.js 15.0.1 with React 18.3.1
- **UI Components**: Radix UI components with Tailwind CSS
- **Real-Time Communication**: RT-Client for audio/text streaming
- **State Management**: React hooks and context
- **Audio Processing**: Web Audio API integration

### Backend (FastAPI)
- **Framework**: FastAPI 0.104.1 with Python 3.8+
- **AI Integration**: Semantic Kernel with Azure AI Projects
- **Database**: SQLite/PostgreSQL support
- **Authentication**: Azure Identity integration
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## Prerequisites

Before setting up the CustomerUI system, ensure you have the following:

### System Requirements
- **Node.js**: Version 18 or higher
- **Python**: Version 3.8 or higher
- **npm or yarn**: For frontend package management
- **pip**: For Python package management

### Azure Services Required
- **Azure AI Foundry**: For agent orchestration
- **Azure OpenAI**: For GPT-4o-mini model access
- **Azure AI Projects**: For semantic kernel integration

### API Keys and Connections
- Azure AI Project Connection String
- Azure OpenAI API Key and Endpoint
- GPT-4o-mini deployment access

## Installation & Setup

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd multi-agent-loan-automation/CustomerUI
```

### Step 2: Backend Setup

#### 2.1 Install Python Dependencies
```bash
cd Agents
pip install -r requirements.txt
```

#### 2.2 Create Backend Environment File
Create a `.env` file in the `Agents` directory with the following configuration:

```bash
# Environment variables for Semantic Kernel Loan Orchestrator API
# Azure AI Project Configuration
AZURE_AI_AGENT_PROJECT_CONNECTION_STRING='CONNECTION_STRING'
AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME='MODEL'

# API Configuration
API_HOST=127.0.0.1
API_PORT=8000
```

### Step 3: Frontend Setup (React Application)

#### 3.1 Navigate to React Directory and Install Dependencies
```bash
cd react
npm install
# or
yarn install
```

#### 3.2 Create Frontend Environment File
Create a `.env.local` file in the `react` directory:

```bash
# Backend API Configuration
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# Azure OpenAI Configuration
NEXT_PUBLIC_AZURE_OPENAI_API_KEY='YOUR_OPENAI_API_KEY'
NEXT_PUBLIC_AZURE_OPENAI_ENDPOINT='YOUR_OPENAI-ENDPOINT'
NEXT_PUBLIC_AZURE_OPENAI_DEPLOYMENT='OPENAPI_MODEL'
```

## Running the Application

### Step 1: Start the Backend Server
```bash
cd CustomerUI/Agents
python fastapi_orchestrator_clean.py
```

The backend server will start on `http://localhost:8000`

**Verify Backend is Running:**
- API Documentation: `http://localhost:8000/docs`

### Step 2: Start the Frontend Application
```bash
cd CustomerUI/react
npm run dev
# or
yarn dev
```

The frontend application will start on `http://localhost:3000`

### Step 3: Access the Application
Open your browser and navigate to `http://localhost:3000`

## User Guide

### Getting Started with the Chat Interface

1. **Initial Setup**
   - Ensure both backend and frontend servers are running
   - Open the application in your browser
   - Allow microphone access for audio features (optional)

2. **Starting a Conversation**
   - Type your message or use the microphone for voice input
   - Wait for the agent's response

3. **Available Agents**
   - **Pre-Qualification Agent** 🎯: Ask about loan eligibility, requirements, and initial assessment
   - **Application Assist Agent** 🤝: Get help completing your loan application

### Using Audio Features

1. **Voice Input**
   - Click the microphone button to start recording
   - Speak clearly and wait for the recording to stop
   - The system will convert your speech to text automatically

### Chat Features

- **Message History**: All conversations are saved and accessible
- **Real-Time Responses**: See typing indicators and streaming responses
- **Multi-Format Support**: Send text, audio
- **Context Awareness**: Agents remember previous conversation context

## API Documentation

The FastAPI backend provides the following key endpoints:

- `POST /chat/message` - Send message to agent
- `GET /agents` - Get available agents
- `GET /conversation/{id}` - Get conversation history

Access full API documentation at `http://localhost:8000/docs` when the backend is running.

### WebSocket Support
Real-time communication is handled through WebSocket connections for:
- Live message streaming
- Audio data transmission
- Status updates
- Connection management

## Development

### File Structure
```
CustomerUI/
├── Agents/                          # Backend FastAPI application
│   ├── fastapi_orchestrator_clean.py   # Main FastAPI server
│   ├── final_orchestrator.py           # Agent orchestration logic
│   ├── database.py                     # Database models and connection
│   ├── models.py                       # Pydantic models
│   ├── requirements.txt                # Python dependencies
│   ├── agents/                         # Individual agent implementations
│   └── instructions/                   # Agent instruction templates
├── react/                           # Frontend Next.js application
│   ├── src/
│   │   ├── app/                     # Next.js app directory
│   │   │   ├── page.tsx             # Main page component
│   │   │   ├── chat-interface.tsx   # Chat interface component
│   │   │   └── layout.tsx           # Application layout
│   │   ├── components/              # Reusable UI components
│   │   └── lib/                     # Utility functions
│   ├── public/                      # Static assets
│   ├── package.json                 # Node.js dependencies
│   └── next.config.ts               # Next.js configuration
└── README.md                        # This file
```

## License

Internal use only - Microsoft Innovation Hub India
Confidential and proprietary software

---

*Last Updated: July 30, 2025*
*Version: 1.0.0*

