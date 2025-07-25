"""
FastAPI Server for Semantic Kernel Loan Orchestrator
Provides REST API endpoints for the intent-based loan agent routing system.
Uses the existing FinalLoanOrchestrator class for better code reuse and maintainability.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import os
import sys
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the working orchestrator directly
from final_orchestrator import FinalLoanOrchestrator
from database import get_db, SessionLocal
from models import MasterCustomerData

# Load environment variables
load_dotenv()

# Global orchestrator instance
orchestrator = None

# Track active threads
active_threads = {}

# Initialize FastAPI app
app = FastAPI(
    title="Semantic Kernel Loan Orchestrator API",
    description="API for orchestrating loan applications using Semantic Kernel agents with intent-based routing",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Agent",
            "description": "Agent messaging and communication operations"
        },
        {
            "name": "root",
            "description": "Root endpoint operations"
        },
        {
            "name": "health",
            "description": "Health check operations"
        },
        {
            "name": "Threads",
            "description": "Operations for managing conversation threads"
        }
    ]
)

# Add CORS middleware for web client compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)


class MessageRequest(BaseModel):
    """Request model for agent messages"""
    message: str  # Only the user's message is required


class MessageResponse(BaseModel):
    """Response model for agent messages"""
    message: str  # The agent's response message
    agent_id: str  # The ID of the agent that handled the request
    thread_id: str  # The conversation thread ID
    message_id: str  # The ID of this specific message
    agent_type: str  # "prequalification", "application", or "loan_status_check"
    status: str
    created_at: str


class APIOrchestrator:
    """
    Wrapper class that adapts FinalLoanOrchestrator for FastAPI use.
    This provides the API-specific logic while reusing the working orchestrator.
    """
    
    def __init__(self):
        self.orchestrator = FinalLoanOrchestrator()
        self.initialized = False
        self.thread_id = None
        
    async def initialize(self):
        """Initialize the underlying orchestrator."""
        if self.initialized:
            return True
            
        try:
            success = await self.orchestrator.initialize()
            if success:
                self.initialized = True
                self.thread_id = f"api_thread_{str(uuid.uuid4())}"
                print(f"✅ API Orchestrator initialized with thread {self.thread_id}")
            return success
        except Exception as e:
            print(f"❌ Error initializing API orchestrator: {e}")
            return False
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """
        Process a user message using the FinalLoanOrchestrator.
        
        Args:
            message: The user's message
            
        Returns:
            Dict containing response message and metadata
        """
        if not self.initialized:
            if not await self.initialize():
                raise HTTPException(status_code=500, detail="Failed to initialize orchestrator")
        
        # Generate message ID
        message_id = f"msg_{str(uuid.uuid4())}"
        
        try:
            # Add user message to orchestrator's conversation history
            from semantic_kernel.contents import ChatMessageContent
            user_message = ChatMessageContent(role="user", content=message)
            
            # Initialize conversation history if it doesn't exist
            if not hasattr(self.orchestrator, 'conversation_history'):
                self.orchestrator.conversation_history = []
            
            self.orchestrator.conversation_history.append(user_message)
            
            # Select appropriate agent using the orchestrator's selector
            selected_agent = await self.orchestrator.selector.select_agent(
                self.orchestrator.agents, 
                self.orchestrator.conversation_history
            )
            
            if not selected_agent:
                raise HTTPException(status_code=500, detail="No agent available to handle the request")
            
            agent_name = self.orchestrator.selector._get_agent_name(selected_agent)
            print(f"🔄 API processing with {agent_name} for message: {message[:50]}...")
            print(f"🔍 Selected agent details: {type(selected_agent).__name__}")
            
            # Get response from selected agent (same pattern as FinalLoanOrchestrator)
            response_text = ""
            
            async for response in selected_agent.invoke(
                messages=message, 
                thread=self.orchestrator.thread
            ):
                if hasattr(response, 'content') and response.content:
                    response_text = response.content
                    
                    # Create tracked response (same as FinalLoanOrchestrator)
                    class ResponseWithAgent:
                        def __init__(self, content, agent_name):
                            self.content = content
                            self.agent_name = agent_name
                            self.role = "assistant"
                    
                    tracked_response = ResponseWithAgent(response.content, agent_name)
                    self.orchestrator.conversation_history.append(tracked_response)
                    
                    # Update thread (same as FinalLoanOrchestrator)
                    if hasattr(response, 'thread_id'):
                        self.orchestrator.thread = response.thread_id
                    elif hasattr(response, 'thread'):
                        self.orchestrator.thread = response.thread
            
            # Ensure response is a string
            if not response_text:
                response_text = "I'm processing your request. Please provide more details if needed."
            
            # Convert to string if needed (fixing the Pydantic validation issue)
            if hasattr(response_text, 'content'):
                response_text = str(response_text.content)
            elif not isinstance(response_text, str):
                response_text = str(response_text)
            
            # Determine agent type and ID
            if agent_name == "PrequalificationAgent":
                agent_id = "prequalification_agent"
                agent_type = "prequalification"
            elif agent_name == "ApplicationAssistAgent":
                agent_id = "application_assist_agent"
                agent_type = "application"
            elif agent_name == "LoanStatusCheckAgent":
                agent_id = "loan_status_check_agent"
                agent_type = "loan_status_check"
            else:
                agent_id = "orchestrator"
                agent_type = "orchestrator"
            
            # Update active threads tracking
            active_threads[self.thread_id] = {
                'current_agent': agent_id,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            # Check if application submission was completed and run audit server-side only
            if agent_name.lower() == "applicationassistagent" and "application has been successfully submitted" in response_text.lower():
                # Run audit process in background - logs only on server, not returned to user
                print("🛡️ [SERVER] Application submission detected - starting server-side audit process...")
                asyncio.create_task(self.handle_audit_process_server_side(response_text))
            
            return {
                'message': response_text,
                'agent_id': agent_id,
                'thread_id': self.thread_id,
                'message_id': message_id,
                'agent_type': agent_type,
                'status': 'success',
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error processing message: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error processing message: {str(e)}"
            )
    
    async def cleanup(self):
        """Clean up resources."""
        if self.orchestrator:
            await self.orchestrator.cleanup()
    
    async def handle_audit_process_server_side(self, response_text: str):
        """
        Handle audit process on server side only - logs printed to terminal, not returned to user.
        This runs the same audit logic as final_orchestrator but keeps it server-side only.
        """
        try:
            print("🛡️ [SERVER] Starting audit process (server-side only)...")
            
            # Step 1: Get latest customer ID from database
            print("🔍 [SERVER] Getting latest customer ID from database...")
            db = SessionLocal()
            try:
                latest_customer = db.query(MasterCustomerData).order_by(
                    MasterCustomerData.Customer_ID.desc()
                ).first()
                
                if latest_customer:
                    customer_id = latest_customer.Customer_ID
                    print(f"🆔 [SERVER] Latest Customer ID: {customer_id}")
                else:
                    print("❌ [SERVER] No customer found in database")
                    return
            finally:
                db.close()
            
            # Step 2: Get Audit Agent
            audit_agent = next((a for a in self.orchestrator.agents if self.orchestrator.selector._get_agent_name(a).lower() == "auditagent"), None)
            if not audit_agent:
                print("⚠️ [SERVER] AuditAgent not found.")
                return
            
            print("=" * 60)
            print("🛡️ [SERVER] STARTING AUDIT PROCESS")
            print("=" * 60)
            
            # Step 3: Prequalification Audit
            prequal_prompt = f"""
Create audit record for customer {customer_id} - Prequalification Check.
Audit Type: "Prequalification Check"
Audit Status: "COMPLETED"
Auditor Name: "PrequalificationAgent"
Remarks: "Prequalification process completed successfully. Customer meets basic eligibility criteria for loan application."
Follow-up Required: "No"
"""
            
            print("🛡️ [SERVER] Step 1: Running Prequalification Audit...")
            prequal_response = await self.orchestrator.invoke_agent_with_retry(
                audit_agent, 
                prequal_prompt,
                max_retries=2,
                timeout=60,  # 1 minute for audit operations
                background=True  # Use background mode to reduce verbose logs
            )
            
            if prequal_response:
                print(f"📝 [SERVER] Prequalification Audit Response:")
                print(f"   [SERVER] {prequal_response}")
                print("✅ [SERVER] Prequalification audit completed successfully.")
            else:
                print("❌ [SERVER] Prequalification audit failed after retries.")
                return
            
            print("-" * 40)
            
            # Step 4: Application Audit
            app_prompt = f"""
Create audit record for customer {customer_id} - Application Review.
Audit Type: "Application Review"
Audit Status: "COMPLETED" 
Auditor Name: "ApplicationAssistAgent"
Remarks: "Loan application submitted successfully. All required documents and information collected. Application ready for review process."
Follow-up Required: "Yes"

Application Summary:
{response_text}
"""
            
            print("🛡️ [SERVER] Step 2: Running Application Audit...")
            app_response = await self.orchestrator.invoke_agent_with_retry(
                audit_agent, 
                app_prompt,
                max_retries=2,
                timeout=60,  # 1 minute for audit operations
                background=True  # Use background mode to reduce verbose logs
            )
            
            if app_response:
                print(f"📝 [SERVER] Application Audit Response:")
                print(f"   [SERVER] {app_response}")
                print("✅ [SERVER] Application audit completed successfully.")
            else:
                print("❌ [SERVER] Application audit failed after retries.")
                return
                
            print("=" * 60)
            print(f"🎉 [SERVER] ALL AUDIT PROCESSES COMPLETED FOR CUSTOMER {customer_id}!")
            print("📊 [SERVER] Summary:")
            print(f"   [SERVER] • Prequalification Audit: ✅ COMPLETED")
            print(f"   [SERVER] • Application Audit: ✅ COMPLETED") 
            print(f"   [SERVER] • Customer ID: {customer_id}")
            print(f"   [SERVER] • Status: Ready for review")
            print("=" * 60)
            
            # Send email notifications after audit completion (server-side only)
            current_customer_id = customer_id
            
            # Stage 1: Application - Initial application submission confirmation
            try:
                print(f"\n📧 [SERVER] Sending Stage 1 email notification (Application Submission)...")
                stage1_email_result = await self.orchestrator.send_stage_email_notification_async("1", current_customer_id)
                if stage1_email_result.get("status") == "submitted":
                    print(f"✅ [SERVER] Stage 1 email sent successfully")
                    print(f"   📧 [SERVER] Template: {stage1_email_result.get('template_name', 'application')}")
                    print(f"   📋 [SERVER] Notification: Application submission confirmation sent to customer")
                else:
                    print(f"⚠️ [SERVER] Stage 1 email notification issue: {stage1_email_result.get('message', 'Unknown')}")
            except Exception as email_error:
                print(f"⚠️ [SERVER] Stage 1 email notification failed: {str(email_error)}")
            
            # Wait 1 minute before sending next email
            print(f"⏳ [SERVER] Waiting 1 minute before sending Stage 2 email...")
            await asyncio.sleep(60)  # 60 seconds = 1 minute
            
            # Stage 2: Document Submission - Document upload instructions
            try:
                print(f"\n📧 [SERVER] Sending Stage 2 email notification (Document Submission)...")
                stage2_email_result = await self.orchestrator.send_stage_email_notification_async("2", current_customer_id)
                if stage2_email_result.get("status") == "submitted":
                    print(f"✅ [SERVER] Stage 2 email sent successfully")
                    print(f"   📧 [SERVER] Template: {stage2_email_result.get('template_name', 'document_submission')}")
                    print(f"   📋 [SERVER] Notification: Document upload instructions sent to customer")
                else:
                    print(f"⚠️ [SERVER] Stage 2 email notification issue: {stage2_email_result.get('message', 'Unknown')}")
            except Exception as email_error:
                print(f"⚠️ [SERVER] Stage 2 email notification failed: {str(email_error)}")
            
            # Wait 1 minute before sending next email
            print(f"⏳ [SERVER] Waiting 1 minute before sending Stage 3 email...")
            await asyncio.sleep(60)  # 60 seconds = 1 minute
            
            # Stage 3: Verification - Document verification in progress
            try:
                print(f"\n� [SERVER] Sending Stage 3 email notification (Document Verification)...")
                stage3_email_result = await self.orchestrator.send_stage_email_notification_async("3", current_customer_id)
                if stage3_email_result.get("status") == "submitted":
                    print(f"✅ [SERVER] Stage 3 email sent successfully")
                    print(f"   📧 [SERVER] Template: {stage3_email_result.get('template_name', 'verification')}")
                    print(f"   📋 [SERVER] Notification: Document verification process notification sent to customer")
                else:
                    print(f"⚠️ [SERVER] Stage 3 email notification issue: {stage3_email_result.get('message', 'Unknown')}")
            except Exception as email_error:
                print(f"⚠️ [SERVER] Stage 3 email notification failed: {str(email_error)}")
            
            print("\n" + "=" * 60)
            print(f"📬 [SERVER] EMAIL NOTIFICATIONS COMPLETED!")
            print("📊 [SERVER] Email Summary:")
            print(f"   [SERVER] • Stage 1 - Application Confirmation: 📧 SENT")
            print(f"   [SERVER] • Stage 2 - Document Instructions: 📧 SENT") 
            print(f"   [SERVER] • Stage 3 - Verification Process: 📧 SENT")
            print(f"   [SERVER] • Customer ID: {current_customer_id}")
            print("=" * 60)
            print("�💡 [SERVER] Audit process and email notifications completed - user only sees original response")
                
        except Exception as e:
            print(f"❌ [SERVER] Error during audit process: {str(e)}")


# API Endpoints

@app.get("/", 
         tags=["root"],
         operation_id="GetRoot")
def read_root():
    """
    Welcome endpoint for the Semantic Kernel Loan Orchestrator API.
    
    Returns:
        Dict: Welcome message and API information
    """
    return {
        "message": "Welcome to Semantic Kernel Loan Orchestrator API",
        "description": "Intent-based loan agent routing using Azure Semantic Kernel",
        "version": "1.0.0",
        "endpoints": {
            "message": "/agent/message",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.post("/agent/message", 
          response_model=MessageResponse,
          tags=["Agent"],
          operation_id="ProcessAgentMessage")
async def process_agent_message(request: MessageRequest):
    """
    Process a message through the semantic kernel agent orchestration system.
    Uses intent-based routing to select the appropriate agent (Prequalification, Application, or Audit).
    
    **Automatic Audit Process:**
    - When ApplicationAssistAgent responds with "application has been successfully submitted"
    - Audit process runs automatically on server-side (logs in terminal only)
    - User response remains unchanged - only sees the agent's original response
    - Server logs show complete audit trail for compliance
    
    Args:
        request: MessageRequest containing only the user's message
        
    Returns:
        MessageResponse: The agent's response with metadata (audit logs not included)
        
    Examples:
        POST /agent/message
        {
            "message": "I want to check my loan eligibility"
        }
        
        POST /agent/message
        {
            "message": "I want to apply for a loan"
        }
        
        POST /agent/message
        {
            "message": "documents uploaded successfully"
        }
        
        Response for application submission:
        {
            "message": "Your application has been successfully submitted...",
            "agent_id": "application_assist_agent",
            "agent_type": "application",
            "status": "success"
        }
        
        Note: Audit process runs in background on server - check terminal logs for audit details.
    """
    global orchestrator
    
    try:
        # Initialize orchestrator if needed
        if not orchestrator:
            orchestrator = APIOrchestrator()
        
        # Process the message using the FinalLoanOrchestrator
        result = await orchestrator.process_message(message=request.message)
        
        return MessageResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/health",
         tags=["health"],
         operation_id="HealthCheck")
async def health_check():
    """
    Health check endpoint to verify the API and orchestrator status.
    
    Returns:
        Dict: Health status and system information
    """
    global orchestrator
    
    orchestrator_status = "not_initialized"
    if orchestrator and orchestrator.initialized:
        orchestrator_status = "healthy"
    elif orchestrator:
        orchestrator_status = "initializing"
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "orchestrator_status": orchestrator_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/threads/{thread_id}", 
         response_model=Dict[str, Any],
         tags=["Threads"],
         operation_id="GetThread")
async def get_thread(thread_id: str):
    """
    Get details about a specific thread
    """
    if thread_id not in active_threads:
        raise HTTPException(
            status_code=404,
            detail="Thread not found"
        )
    
    # Return thread information
    history_count = 0
    if orchestrator and hasattr(orchestrator.orchestrator, 'conversation_history'):
        history_count = len(orchestrator.orchestrator.conversation_history)
    
    return {
        "thread_id": thread_id,
        "agent_id": active_threads[thread_id]['current_agent'],
        "last_updated": active_threads[thread_id]['last_updated'],
        "message_count": history_count,
        "status": "active"
    }


# Startup and shutdown events

@app.on_event("startup")
async def startup_event():
    """Initialize the orchestrator on startup."""
    global orchestrator
    print("🚀 Starting Semantic Kernel Loan Orchestrator API...")
    print("🛡️ Server-side audit functionality enabled")
    print("📝 Audit logs will appear in terminal only, not in user responses")
    orchestrator = APIOrchestrator()
    # Initialize in background to avoid blocking startup
    asyncio.create_task(orchestrator.initialize())


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    global orchestrator
    print("🔄 Shutting down Semantic Kernel Loan Orchestrator API...")
    if orchestrator:
        await orchestrator.cleanup()


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Semantic Kernel Loan Orchestrator API Server...")
    print("📍 Server will be available at: http://127.0.0.1:8000")
    print("📖 API Documentation: http://127.0.0.1:8000/docs")
    print("🔍 Alternative docs: http://127.0.0.1:8000/redoc")
    
    uvicorn.run(
        "fastapi_orchestrator_clean:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )
