import openai
import requests
import logging
import json
from fastapi import FastAPI, Request, HTTPException, Depends
from typing import Dict, Optional
import re
from sqlalchemy.orm import Session
from agent_config import AZURE_OPENAI_CONFIG, API_BASE, PROMPTS
from database import SessionLocal, engine
from models import Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Loan Processing Agent")

def extract_loan_id(instruction: str) -> Optional[int]:
    """Extract loan ID from instruction."""
    # Try different patterns for loan ID
    patterns = [
        r'loan (?:id\s+)?(\d+)',
        r'loan application (\d+)',
        r'loan\s+#?(\d+)',
        r'id\s*:?\s*(\d+)',
        r'application\s+(\d+)',
        r'(\d+)'  # Last resort - just find a number
    ]
    
    for pattern in patterns:
        match = re.search(pattern, instruction.lower())
        if match:
            return int(match.group(1))
    
    return None

def get_openai_client():
    """Get Azure OpenAI client instance."""
    client = openai.AzureOpenAI(
        api_key=AZURE_OPENAI_CONFIG["api_key"],
        api_version=AZURE_OPENAI_CONFIG["api_version"],
        azure_endpoint=AZURE_OPENAI_CONFIG["api_base"]
    )
    logger.info(f"Created OpenAI client with deployment: {AZURE_OPENAI_CONFIG['deployment_name']}")
    return client

def extract_loan_details(instruction: str) -> Dict:
    """Extract loan application details using Azure OpenAI."""
    try:
        client = get_openai_client()
        completion = client.chat.completions.create(
            model=AZURE_OPENAI_CONFIG["deployment_name"],
            messages=[
                {"role": "system", "content": PROMPTS["loan_extractor"]},
                {"role": "user", "content": instruction}
            ],
            temperature=0.3
        )
        response_content = completion.choices[0].message.content
        logger.info(f"Loan details extracted: {response_content}")
        return eval(response_content)
    except Exception as e:
        logger.error(f"Error extracting loan details: {str(e)}")
        return None

def parse_instruction(instruction: str) -> Dict:
    """Parse user instruction using Azure OpenAI."""
    try:
        client = get_openai_client()
        
        # First try to parse as an action
        completion = client.chat.completions.create(
            model=AZURE_OPENAI_CONFIG["deployment_name"],
            messages=[
                {"role": "system", "content": PROMPTS["intent_classifier"]},
                {"role": "user", "content": instruction}
            ],
            temperature=0.3
        )
        response_content = completion.choices[0].message.content
        logger.info(f"Instruction parsed: {response_content}")
        
        try:
            result = eval(response_content)
            if not result.get("action"):
                # If no clear action, treat as conversational
                return {
                    "action": "chat",
                    "parameters": {"query": instruction}
                }
            return result
        except:
            # If parsing fails, handle as chat
            return {
                "action": "chat",
                "parameters": {"query": instruction}
            }
    except Exception as e:
        logger.error(f"Error parsing instruction: {str(e)}")
        return {"action": "unknown", "parameters": {}}

async def handle_apply(loan_details: Dict, db: Session = Depends(get_db)) -> Dict:
    """Handle loan application."""
    try:
        # Validate loan details
        if not all(key in loan_details for key in ["applicant_name", "email", "phone", "loan_amount", 
                                                 "loan_purpose", "loan_term_months", "monthly_income", 
                                                 "employment_type"]):
            raise HTTPException(status_code=400, detail="Missing required fields in loan application")
        
        # Create API payload with explicit type conversion
        try:
            api_payload = {
                "applicant_name": str(loan_details["applicant_name"]),
                "email": str(loan_details["email"]),
                "phone": str(loan_details["phone"]),
                "loan_amount": float(loan_details["loan_amount"]),
                "loan_purpose": str(loan_details["loan_purpose"]),
                "loan_term_months": int(loan_details["loan_term_months"]),
                "monthly_income": float(loan_details["monthly_income"]),
                "employment_type": str(loan_details["employment_type"])
            }
            
            # Make the API call
            response = requests.post(f"{API_BASE}/api/loan/apply", json=api_payload)
            if response.status_code == 200:
                result = response.json()
                application_id = result.get('id')
                
                # Return formatted response with application details and ID
                return {
                   # "application_details": result,
                    "message": f"""Here are your loan application details:
• Application ID: {application_id}
• Applicant: {api_payload['applicant_name']}
• Amount: ${api_payload['loan_amount']:,.2f}
• Status: {result.get('status', 'DRAFT')}

Your loan application has been created successfully! Please save your Application ID: {application_id} for future reference.
Would you like me to help you submit this application for review?"""
                }
        except Exception as e:
            logger.error(f"Error preparing API payload: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid loan details format")
        
        response = requests.post(f"{API_BASE}/api/loan/apply", json=api_payload)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API Error: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except requests.RequestException as e:
        logger.error(f"Connection error: {str(e)}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")

async def handle_submit(loan_id: int, db: Session = Depends(get_db)) -> Dict:
    """Handle loan submission."""
    try:
        response = requests.post(f"{API_BASE}/api/loan/{loan_id}/submit")
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API Error: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except requests.RequestException as e:
        logger.error(f"Connection error: {str(e)}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")

async def handle_approve(loan_id: int, db: Session = Depends(get_db)) -> Dict:
    """Handle loan approval."""
    try:
        response = requests.post(f"{API_BASE}/api/loan/{loan_id}/approve")
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API Error: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except requests.RequestException as e:
        logger.error(f"Connection error: {str(e)}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")

async def handle_reject(loan_id: int, reason: str, db: Session = Depends(get_db)) -> Dict:
    """Handle loan rejection."""
    try:
        response = requests.post(
            f"{API_BASE}/api/loan/{loan_id}/reject",
            json={"rejection_reason": reason}
        )
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API Error: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except requests.RequestException as e:
        logger.error(f"Connection error: {str(e)}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")

async def handle_view(loan_id: int, db: Session = Depends(get_db)) -> Dict:
    """Handle loan details viewing."""
    try:
        response = requests.get(f"{API_BASE}/api/loan/{loan_id}")
        if response.status_code == 200:
            loan_data = response.json()
            message = f"""Here are the loan details for application {loan_id}:
• Applicant: {loan_data.get('applicant_name')}
• Amount: ${loan_data.get('loan_amount', 0):,.2f}
• Status: {loan_data.get('status')}"""

            # Add status-specific information
            if loan_data.get('status') == 'DRAFT':
                message += "\n\nThis application is still in draft. Would you like me to help submit it for review? Just say 'yes submit loan " + str(loan_id) + "'"
            elif loan_data.get('status') == 'SUBMITTED':
                message += "\n\nYour application is under review. I'll notify you when there's an update."
            elif loan_data.get('status') == 'APPROVED':
                message += "\n\nCongratulations! Your loan has been approved! 🎉"
            elif loan_data.get('status') == 'REJECTED':
                message += f"\n\nI'm sorry, but this loan was rejected. Reason: {loan_data.get('rejection_reason', 'Not specified')}"
            
            return {"message": message}
        else:
            raise HTTPException(status_code=response.status_code, detail="Loan not found")
        response = requests.get(f"{API_BASE}/api/loan/{loan_id}")
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API Error: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except requests.RequestException as e:
        logger.error(f"Connection error: {str(e)}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")

async def handle_chat(query: str, db: Session = Depends(get_db)) -> Dict:
    """Handle conversational interactions."""
    try:
        client = get_openai_client()
        chat_prompt = """You are a helpful loan assistant. Respond conversationally but focused on loan-related topics.
        Current date: 2025-05-03. Keep responses concise but friendly."""
        
        completion = client.chat.completions.create(
            model=AZURE_OPENAI_CONFIG["deployment_name"],
            messages=[
                {"role": "system", "content": chat_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.7
        )
        
        response = completion.choices[0].message.content
        return {"response": response}
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return {"response": "I'm having trouble processing that right now. How else can I help you with your loan needs?"}

@app.post("/agent")
async def process_instruction(request: Request, db: Session = Depends(get_db)):
    """Process user instruction and return appropriate response."""
    data = await request.json()
    instruction = data.get("instruction", "")
    if not instruction:
        raise HTTPException(status_code=400, detail="No instruction provided")

    # Parse the instruction
    parsed = parse_instruction(instruction)
    action = parsed.get("action", "unknown")
    parameters = parsed.get("parameters", {})
    
    # For apply action, extract loan details first
    if action == "apply":
        loan_details = extract_loan_details(instruction)
        if not loan_details:
            raise HTTPException(status_code=400, detail="Could not extract loan details from instruction")
        parameters = loan_details  # Use extracted details instead of parameters

    # Handle different types of actions
    if action == "apply":
        result = await handle_apply(parameters, db)
    elif action == "view":
        result = await handle_view(parameters.get("loan_id"), db)
    elif action == "submit":
        result = await handle_submit(parameters.get("loan_id"), db)
    elif action == "approve":
        result = await handle_approve(parameters.get("loan_id"), db) 
    elif action == "reject":
        loan_id = parameters.get("loan_id")
        reason = parameters.get("reason")
        
        if not loan_id:
            return {
                "action": "error",
                "response": "Please specify which loan ID you want to reject. For example: 'reject loan 19'"
            }
        
        if not reason:
            return {
                "action": "reject_prompt",
                "response": f"""To reject loan {loan_id}, I need a reason. Please provide one:

For example:
• "Reject loan {loan_id} due to insufficient income"
• "Reject loan {loan_id} because of incomplete documentation"
• "Reject loan {loan_id} due to employment status"
• "Reject loan {loan_id} due to credit history"

What is the reason for rejecting this loan?"""
            }
            
        result = await handle_reject(loan_id, reason, db)
    elif action in ["help", "chat"]:
        # Handle conversational interactions
        result = await handle_chat(instruction, db)
    else:
        # For unrecognized actions, provide a helpful response
        result = await handle_chat(
            "I'm not sure what you're asking. Could you rephrase that or let me know what kind of loan assistance you need?",
            db
        )

    return {
        "action": action,
        "response": result
    }

@app.get("/")
async def root():
    """Root endpoint with usage examples."""
    return {
        "message": "Loan Processing Agent API",
        "examples": [
            "Apply for a loan: 'Apply for a $10000 education loan for John Doe with email john@example.com, phone 1234567890, 12 month term, monthly income $5000'",
            "Submit loan: 'Submit loan ID 1'",
            "Approve loan: 'Approve loan ID 1'",
            "Reject loan: 'Reject loan ID 1 because insufficient income'",
            "View loan: 'Show me loan ID 1'"
        ]
    }
