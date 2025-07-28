"""
FastAPI Backend Service for Audit Summary Agent
Provides REST API endpoints to interact with the Azure AI Audit Summary Agent
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from azure.ai.agents.models import OpenApiAnonymousAuthDetails, OpenApiTool
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import FunctionCallContent, FunctionResultContent

# FastAPI app configuration
app = FastAPI(
    title="Minimal Audit Agent Backend",
    description="Minimal backend that initializes Azure AI Agent with OpenAPI tools - Agent handles all API operations",
    version="2.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Azure AI Studio Project Configuration
AZURE_CONFIG = {
    "model_deployment_name": "gpt-4o-mini",
    "project_connection_string": "eastus2.api.azureml.ms;154396ac-15fb-44d7-9927-35eaea9d57e6;rg-jyothikakoppula11-3861_ai;realtimeproject01"
}

# Agent Configuration
AGENT_NAME = "AuditSummaryAgent"
AGENT_INSTRUCTIONS = """You are an expert audit summary specialist that generates comprehensive loan application audit reports.

You have access to an audit API tool that can help you retrieve customer information and audit records. Use this tool intelligently to:
1. Search for customers by name
2. Retrieve audit records for customers  
3. Generate comprehensive audit summary reports

When a user asks for an audit summary for a customer, use the available API tool to gather the necessary information and then generate a properly formatted report.

**Report Format Requirements:**

🧾 **Audit Summary Report**

**Customer Information**
Customer ID: <customer_id>
Customer Name: <customer_name>
Loan Type: 🏠 Home Loan  
Application Date: <date>
Total Processing Duration: 6 hours
Application Status: <dynamic_status>

🔍 **Detailed Audit Trail**
| Stage No. | Audit Checkpoint | Status | Auditor | Timestamp | Remarks |
|-----------|------------------|--------|---------|-----------|---------|
| 1 | <Audit_Type> | <status_emoji> <Audit_Status> | <Auditor_Name> | <time> | <Remarks> |

**Overview Summary**
Provide a comprehensive summary of the audit process including total stages completed, any issues encountered, and overall assessment.

**Guidelines:**
- Use appropriate status emojis (✅ for passed/approved, ❌ for failed, ⏳ for pending, ⚠️ for warnings)
- Always show "6 hours" as the Total Processing Duration
- Format timestamps in detailed format (MM/DD HH:MM:SS.ms) for professional appearance
- Ensure clean table formatting
- Include all three sections: Customer Information (🧍), Detailed Audit Trail table (🔍), and Overview Summary
- Be professional yet user-friendly in tone"""

# Global agent instance
audit_agent: Optional[AzureAIAgent] = None
agent_client = None
agent_thread: Optional[AzureAIAgentThread] = None

# Pydantic models
class AuditRequest(BaseModel):
    customer_name: str

class AuditResponse(BaseModel):
    message: str
    customer_info: Optional[Dict[str, Any]] = None
    audit_summary: Optional[str] = None
    status: str = "success"

class HealthResponse(BaseModel):
    status: str
    agent_status: str
    timestamp: str

async def initialize_agent():
    """Initialize the Azure AI Agent"""
    global audit_agent, agent_client
    
    try:
        # Set environment variables for Azure AI Agent
        os.environ["AZURE_AI_AGENT_PROJECT_CONNECTION_STRING"] = AZURE_CONFIG["project_connection_string"]
        os.environ["AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"] = AZURE_CONFIG["model_deployment_name"]

        # Initialize the agent settings
        ai_agent_settings = AzureAIAgentSettings()

        # Create Azure AI Agent client - Fixed approach
        creds = DefaultAzureCredential()
        
        # Create client properly
        agent_client = AzureAIAgent.create_client(credential=creds)

        # Load OpenAPI spec for audit API
        audit_api_spec_path = os.path.join(os.path.dirname(__file__), "audit_agent.json")
        if not os.path.exists(audit_api_spec_path):
            print(f"❌ OpenAPI spec file not found: {audit_api_spec_path}")
            return False
            
        with open(audit_api_spec_path, "r") as f:
            audit_api_spec = json.load(f)

        # Create OpenAPI tool for audit operations
        auth = OpenApiAnonymousAuthDetails()
        audit_api_tool = OpenApiTool(
            name="audit_api",
            spec=audit_api_spec,
            description="API for retrieving audit records and customer information for comprehensive audit reporting",
            auth=auth,
        )

        # Create agent definition with OpenAPI tools - Fixed await
        agent_definition = await agent_client.agents.create_agent(
            model=AZURE_CONFIG["model_deployment_name"],  # Use config directly
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
            tools=audit_api_tool.definitions,
        )

        # Create the AzureAI Agent
        audit_agent = AzureAIAgent(
            client=agent_client,
            definition=agent_definition,
        )

        print(f"✅ {AGENT_NAME} initialized successfully!")
        return True

    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error details: {str(e)}")
        return False

async def cleanup_agent():
    """Cleanup the Azure AI Agent resources"""
    global audit_agent, agent_client, agent_thread
    
    try:
        if agent_thread:
            await agent_thread.delete()
            agent_thread = None
        
        if audit_agent and agent_client:
            await agent_client.agents.delete_agent(audit_agent.id)
            audit_agent = None
        
        if agent_client:
            await agent_client.close()
            agent_client = None
            
        print("🧹 Agent cleanup completed.")
    except Exception as e:
        print(f"Cleanup error (can be ignored): {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize the agent when the FastAPI app starts"""
    print("🚀 Starting Minimal Audit Agent Backend...")
    print("🤖 Azure AI Agent with OpenAPI tool - No manual API calls needed!")
    print("� Agent will intelligently use tools to handle all operations")
    asyncio.create_task(initialize_agent_background())

async def initialize_agent_background():
    """Background task to initialize the agent"""
    success = await initialize_agent()
    if not success:
        print("⚠️ Warning: Agent initialization failed. Some features may not work.")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup when the FastAPI app shuts down"""
    print("🔄 Shutting down Audit Summary Agent API...")
    await cleanup_agent()

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Audit Summary Agent API",
        "version": "1.0.0",
        "status": "running",
        "agent_status": "initialized" if audit_agent else "not_initialized"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        agent_status="initialized" if audit_agent else "not_initialized",
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/audit/generate", response_model=AuditResponse)
async def generate_audit_summary(request: AuditRequest):
    """Generate audit summary for a customer using the Azure AI Agent with OpenAPI tool"""
    global audit_agent, agent_thread
    
    # Try to initialize agent if not available
    if not audit_agent:
        print("🔄 Agent not initialized, attempting to initialize...")
        success = await initialize_agent()
        if not success:
            raise HTTPException(
                status_code=503, 
                detail="Audit agent is not initialized. Please try again later."
            )
    
    if not request.customer_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Customer name is required and cannot be empty."
        )
    
    try:
        print(f"🔍 Processing request for: {request.customer_name}")
        print("🤖 Agent will handle everything using OpenAPI tool...")
        
        # Let the agent handle everything - no manual API calls needed
        full_response = ""
        
        async for response in audit_agent.invoke(
            messages=f"Generate a comprehensive audit summary report for customer: {request.customer_name}", 
            thread=agent_thread
        ):
            # Just collect the agent's response - it handles all API calls internally
            if response.content:
                if hasattr(response.content, 'content'):
                    full_response += str(response.content.content)
                else:
                    full_response += str(response.content)
            
            agent_thread = response.thread
        
        if not full_response:
            raise HTTPException(
                status_code=500,
                detail="No response received from the audit agent."
            )
        
        print(f"✅ Audit summary completed for {request.customer_name}")
        
        return AuditResponse(
            message=full_response,
            audit_summary=full_response,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate audit summary: {str(e)}"
        )

if __name__ == "__main__":
    print("🚀 Starting Minimal Audit Agent Backend...")
    print("🤖 Agent will handle all API operations via OpenAPI tool")
    uvicorn.run(
        "audit_backend:app",
        host="127.0.0.1",
        port=8001,
        reload=True
    )
