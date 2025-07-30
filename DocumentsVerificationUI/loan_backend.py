"""
FastAPI Backend Service for Loan Evaluation with Multiple Agents
Provides REST API endpoints to interact with specialized loan evaluation agents
"""

import asyncio
import sys
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

# Ensure proper Unicode handling on Windows
if sys.platform.startswith('win'):
    import locale
    # Set console encoding to UTF-8 to handle Unicode characters
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import the loan evaluation system
from summary import LoanEvaluationSummary

# FastAPI app configuration
app = FastAPI(
    title="Loan Evaluation Agents API",
    description="REST API for comprehensive loan evaluation using specialized Azure AI Agents",
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

# Global evaluation system instance
evaluation_system: Optional[LoanEvaluationSummary] = None

# Pydantic models
class LoanEvaluationRequest(BaseModel):
    customer_name: str
    loan_type: str = "Home Loan"
    include_agents: Optional[List[str]] = None  # Optional list of specific agents to run

class LoanEvaluationResponse(BaseModel):
    message: str
    customer_info: Optional[Dict[str, Any]] = None
    evaluation_summary: Optional[str] = None
    individual_results: Optional[Dict[str, Any]] = None
    status: str = "success"

class AgentEvaluationRequest(BaseModel):
    agent_type: str  # "identity", "income", "guarantor", "inspection", "valuation"
    prompt: Optional[str] = None

class AgentEvaluationResponse(BaseModel):
    agent_type: str
    result: Dict[str, Any]
    status: str = "success"

class HealthResponse(BaseModel):
    status: str
    agents_status: str
    timestamp: str

async def initialize_evaluation_system():
    """Initialize the loan evaluation system"""
    global evaluation_system
    
    try:
        print("🚀 Initializing Loan Evaluation System...")
        print("🔧 Loading configuration...")
        
        # Import config here to catch any import errors
        from DocumentsVerifierBAckend.config import ENDPOINT, RESOURCE_GROUP, SUBSCRIPTION_ID, PROJECT_NAME
        print(f"   Endpoint: {ENDPOINT}")
        print(f"   Resource Group: {RESOURCE_GROUP}")
        print(f"   Project: {PROJECT_NAME}")
        
        evaluation_system = LoanEvaluationSummary()
        evaluation_system.create_agents()
        print("✅ Loan Evaluation System connected!")
        return True

    except ImportError as e:
        print(f"❌ Configuration import error: {e}")
        print("   Please ensure config.py exists with proper Azure settings")
        return False
    except Exception as e:
        print(f"❌ Failed to initialize evaluation system: {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error details: {str(e)}")
        
        # Provide helpful troubleshooting information
        print("\n🔧 Troubleshooting steps:")
        print("1. Run 'python test_config.py' to test your Azure configuration")
        print("2. Verify your Azure credentials with 'az login'")
        print("3. Check that your Azure AI Studio project exists")
        print("4. Ensure you have proper permissions on the subscription")
        
        return False

async def cleanup_evaluation_system():
    """Cleanup the evaluation system resources"""
    global evaluation_system
    
    try:
        if evaluation_system:
            evaluation_system.cleanup()
            evaluation_system = None
            
        print("🧹 Evaluation system cleanup completed.")
    except Exception as e:
        print(f"Cleanup error (can be ignored): {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize the evaluation system when the FastAPI app starts"""
    print("🚀 Starting Loan Evaluation Agents API...")
    print("🛡️ Multiple Azure AI Agents functionality enabled")
    print("📝 Agents will process comprehensive loan evaluations")
    # Initialize in background to avoid blocking startup
    asyncio.create_task(initialize_evaluation_system_background())

async def initialize_evaluation_system_background():
    """Background task to initialize the evaluation system"""
    success = await initialize_evaluation_system()
    if not success:
        print("⚠️ Warning: Evaluation system initialization failed. Some features may not work.")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup when the FastAPI app shuts down"""
    print("🔄 Shutting down Loan Evaluation Agents API...")
    await cleanup_evaluation_system()

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Loan Evaluation Agents API",
        "version": "2.0.0",
        "status": "running",
        "agents_available": ["identity", "income", "guarantor", "inspection", "valuation"],
        "evaluation_system_status": "initialized" if evaluation_system else "not_initialized"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        agents_status="initialized" if evaluation_system else "not_initialized",
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/evaluation/complete", response_model=LoanEvaluationResponse)
async def run_complete_evaluation(request: LoanEvaluationRequest):
    """Run complete loan evaluation with all agents"""
    global evaluation_system
    
    # Try to initialize evaluation system if not available
    if not evaluation_system:
        print("🔄 Evaluation system not initialized, attempting to initialize...")
        success = await initialize_evaluation_system()
        if not success:
            raise HTTPException(
                status_code=503, 
                detail={
                    "error": "Loan evaluation system is not initialized",
                    "message": "Azure AI connection failed. Please check your configuration.",
                    "troubleshooting": [
                        "1. Run 'python test_config.py' to test your Azure configuration",
                        "2. Verify your Azure credentials with 'az login'", 
                        "3. Check that your Azure AI Studio project exists",
                        "4. Ensure config.py has the correct endpoint URL"
                    ]
                }
            )
    
    if not request.customer_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Customer name is required and cannot be empty."
        )
    
    try:
        print(f"🔍 Running complete loan evaluation for: {request.customer_name}")
        
        # Store original customer name in the evaluation system for reference
        evaluation_system.customer_name = request.customer_name
        evaluation_system.loan_type = request.loan_type
        
        # Run the complete evaluation
        final_summary = evaluation_system.run_complete_evaluation()
        
        if not final_summary:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate loan evaluation summary."
            )
        
        print(f"✅ Complete loan evaluation generated successfully for {request.customer_name}")
        
        return LoanEvaluationResponse(
            message=final_summary,
            evaluation_summary=final_summary,
            individual_results=evaluation_system.agent_outputs,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error running complete evaluation: {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run complete loan evaluation: {str(e)}"
        )

@app.post("/api/evaluation/agent", response_model=AgentEvaluationResponse)
async def run_single_agent_evaluation(request: AgentEvaluationRequest):
    """Run evaluation for a single specific agent"""
    global evaluation_system
    
    # Try to initialize evaluation system if not available
    if not evaluation_system:
        print("🔄 Evaluation system not initialized, attempting to initialize...")
        success = await initialize_evaluation_system()
        if not success:
            raise HTTPException(
                status_code=503, 
                detail="Loan evaluation system is not initialized. Please try again later."
            )
    
    if request.agent_type not in ["identity", "income", "guarantor", "inspection", "valuation"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent type. Must be one of: identity, income, guarantor, inspection, valuation"
        )
    
    try:
        print(f"🔍 Running {request.agent_type} agent evaluation...")
        
        # Define default prompts for each agent
        default_prompts = {
            'identity': (
                "Analyze all identity documents (Aadhaar, PAN, address proof) and provide comprehensive verification. "
                "Extract: full name, DOB, PAN number, Aadhaar number, complete address. "
                "Check for authenticity and consistency. Return results in JSON format with status, details, and any issues."
            ),
            'income': (
                "Analyze income documents (salary slips, bank statements, Form 16) and assess financial eligibility. "
                "Extract: monthly income, employment status, employer details, employment duration. "
                "Check consistency across documents. Return results in JSON format with income assessment and eligibility."
            ),
            'guarantor': (
                "Analyze guarantor verification call recording and documents. "
                "Extract: guarantor name, relationship, financial standing, statements from call. "
                "Assess eligibility and reliability. Return results in JSON format with guarantor evaluation."
            ),
            'inspection': (
                "Analyze property inspection video and materials. "
                "Assess: property condition, visible damages, construction quality, safety concerns. "
                "Evaluate impact on collateral value. Return structured assessment of property condition."
            ),
            'valuation': (
                "Analyze sale deed and property documents for valuation. "
                "Determine: last sale price, sale year, current market value (11% annual appreciation). "
                "Assess risks and suitability as collateral. Return valuation analysis with estimated value."
            )
        }
        
        prompt = request.prompt or default_prompts.get(request.agent_type, "Analyze the relevant documents for this loan application.")
        
        # Run the specific agent evaluation
        result = evaluation_system.run_agent_evaluation(request.agent_type, prompt)
        
        print(f"✅ {request.agent_type} agent evaluation completed")
        
        return AgentEvaluationResponse(
            agent_type=request.agent_type,
            result=result,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error running {request.agent_type} agent evaluation: {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run {request.agent_type} agent evaluation: {str(e)}"
        )

@app.get("/api/agents/list")
async def list_available_agents():
    """List all available agents and their status"""
    global evaluation_system
    
    agents_info = {
        "available_agents": ["identity", "income", "guarantor", "inspection", "valuation"],
        "system_status": "initialized" if evaluation_system else "not_initialized",
        "agents_descriptions": {
            "identity": "Verifies identity documents (Aadhaar, PAN, address proof)",
            "income": "Analyzes income documents and financial eligibility", 
            "guarantor": "Evaluates guarantor verification and reliability",
            "inspection": "Assesses property condition from inspection materials",
            "valuation": "Determines property value from sale deed and documents"
        }
    }
    
    if evaluation_system and hasattr(evaluation_system, 'agents'):
        agents_info["initialized_agents"] = list(evaluation_system.agents.keys())
    else:
        agents_info["initialized_agents"] = []
    
    return agents_info

@app.get("/api/evaluation/results")
async def get_last_evaluation_results():
    """Get the results from the last evaluation run"""
    global evaluation_system
    
    if not evaluation_system:
        raise HTTPException(
            status_code=404,
            detail="No evaluation system available"
        )
    
    if not hasattr(evaluation_system, 'agent_outputs') or not evaluation_system.agent_outputs:
        raise HTTPException(
            status_code=404,
            detail="No evaluation results available. Run a complete evaluation first."
        )
    
    return {
        "individual_results": evaluation_system.agent_outputs,
        "customer_name": getattr(evaluation_system, 'customer_name', 'Unknown'),
        "loan_type": getattr(evaluation_system, 'loan_type', 'Unknown'),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/evaluation/summary")
async def generate_summary_only():
    """Generate only the final summary from existing agent results"""
    global evaluation_system
    
    if not evaluation_system:
        raise HTTPException(
            status_code=404,
            detail="No evaluation system available"
        )
    
    if not hasattr(evaluation_system, 'agent_outputs') or not evaluation_system.agent_outputs:
        raise HTTPException(
            status_code=400,
            detail="No agent results available. Run agent evaluations first."
        )
    
    try:
        print("🔍 Generating final summary from existing results...")
        
        final_summary = evaluation_system.generate_final_summary()
        
        if not final_summary:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate final summary."
            )
        
        print("✅ Final summary generated successfully")
        
        return {
            "summary": final_summary,
            "status": "success"
        }
        
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}"
        )

@app.get("/api/system/diagnostics")
async def system_diagnostics():
    """Get system diagnostic information"""
    try:
        from DocumentsVerifierBAckend.config import ENDPOINT, RESOURCE_GROUP, SUBSCRIPTION_ID, PROJECT_NAME, INDEXES
        
        diagnostics = {
            "config_loaded": True,
            "configuration": {
                "endpoint": ENDPOINT,
                "resource_group": RESOURCE_GROUP,
                "subscription_id": SUBSCRIPTION_ID[:8] + "..." if SUBSCRIPTION_ID else None,
                "project_name": PROJECT_NAME,
                "indexes_configured": len(INDEXES)
            },
            "evaluation_system_status": "initialized" if evaluation_system else "not_initialized",
            "troubleshooting_steps": [
                "1. Run 'python test_config.py' to test Azure configuration",
                "2. Verify Azure credentials with 'az login'",
                "3. Check Azure AI Studio project exists",
                "4. Ensure proper permissions on subscription"
            ]
        }
        
        if evaluation_system:
            try:
                diagnostics["agents_status"] = {
                    "agents_created": len(evaluation_system.agents) if hasattr(evaluation_system, 'agents') else 0,
                    "connection_id": getattr(evaluation_system, 'conn_id', 'Not set')[:50] + "..." if getattr(evaluation_system, 'conn_id', None) else None
                }
            except:
                diagnostics["agents_status"] = "Error getting agent status"
        
        return diagnostics
        
    except ImportError as e:
        return {
            "config_loaded": False,
            "error": f"Configuration import failed: {str(e)}",
            "troubleshooting_steps": [
                "1. Ensure config.py exists in the project root",
                "2. Check config.py syntax",
                "3. Verify all required variables are defined"
            ]
        }
    except Exception as e:
        return {
            "config_loaded": False,
            "error": f"System diagnostic failed: {str(e)}",
            "error_type": type(e).__name__
        }

if __name__ == "__main__":
    print("🚀 Starting Loan Evaluation Agents API Server...")
    uvicorn.run(
        "loan_backend:app",
        host="127.0.0.1",
        port=8001,  # Same port as before for consistency
        reload=True
    )
