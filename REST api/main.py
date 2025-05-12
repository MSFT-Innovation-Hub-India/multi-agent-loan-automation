from fastapi import FastAPI, HTTPException, status, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from models.loan_application import LoanApplicationCreate, LoanApplicationResponse
from models.loan_status import (
    LoanStatusType,
    LoanStatus,
    LoanApprovalRequest,
    LoanRejectionRequest,
    LoanDecisionResponse
)
from database import get_db, engine, Base
from models.database_models import LoanApplication, LoanDecision
import uvicorn
import os

# Get root_path from environment variable, default to "" for local development
root_path = os.getenv("ROOT_PATH", "")

app = FastAPI(
    title="Loan Processing API",
    description="REST API for loan processing and orchestration. Supports Aadhaar and PAN verification, and processes loan applications in Indian Rupees (₹).",
    version="1.0.0",
    root_path=root_path,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    servers=[
        {
            "url": "https://loanweb.azurewebsites.net"
        }
    ],
    openapi_tags=[
        {
            "name": "ExecuteFunction",
            "description": "Operations for loan processing"
        }
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["root"])
def read_root():
    """
    Welcome endpoint for the Loan Processing API.
    """
    return {"message": "Welcome to Loan Processing API"}

@app.get("/health", tags=["health"])
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint that verifies database connectivity"""    
    try:
        # Test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "details": {
                "api_version": "1.0.0",
                "environment": os.getenv("ENVIRONMENT", "production")
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "database": "disconnected",
            "error": str(e)
        }

@app.post("/api/loan/apply", 
          response_model=LoanApplicationResponse,
          status_code=status.HTTP_201_CREATED,
          tags=["ExecuteFunction"],
          operation_id="ApplyLoan")
async def apply_loan(
    application: LoanApplicationCreate,
    db: Session = Depends(get_db)
):
    """
    Submit a new loan application.

    Parameters:
    - applicant_name: Full name of the loan applicant
    - gender: Gender of the applicant
    - dob: Date of birth
    - age: Age of the applicant (18-100)
    - marital_status: Marital status
    - education_level: Education level
    - annual_income: Annual income in ₹
    - employment_type: Type of employment
    - loan_amount: Requested loan amount in ₹
    - tenure_months: Loan tenure in months (1-360)
    - credit_score: Credit score (300-850, optional)
    - existing_loans: Whether applicant has existing loans
    - num_existing_loans: Number of existing loans
    - total_emi_amount: Total EMI amount in ₹
    - loan_purpose: Purpose of the loan
    - city: City of residence
    - phone_number: Contact phone number
    - email: Email address
    - aadhaar_number: 12-digit Aadhaar number
    - pan_number: 10-digit PAN number
    - account_type: Bank account type
    - guarantor_available: Whether a guarantor is available

    Returns:
    - LoanApplicationResponse: Created loan application details with unique ID
    """
    try:
        db_application = LoanApplication(
            applicant_name=application.applicant_name,
            gender=application.gender,
            dob=application.dob,
            age=application.age,
            marital_status=application.marital_status,
            education_level=application.education_level,
            annual_income=float(application.annual_income),
            employment_type=application.employment_type,
            loan_amount=float(application.loan_amount),
            tenure_months=application.tenure_months,
            credit_score=application.credit_score,
            existing_loans=application.existing_loans,
            num_existing_loans=application.num_existing_loans,
            total_emi_amount=float(application.total_emi_amount),
            loan_purpose=application.loan_purpose,
            city=application.city,
            phone_number=application.phone_number,
            email=application.email,
            aadhaar_number=application.aadhaar_number,
            pan_number=application.pan_number,
            account_type=application.account_type,
            guarantor_available=application.guarantor_available,
            application_date=datetime.now(),
            status=LoanStatusType.PENDING
        )
        
        db.add(db_application)
        db.commit()
        db.refresh(db_application)
        
        return LoanApplicationResponse(
            id=db_application.id,
            application_date=db_application.application_date,
            status=db_application.status,
            **application.model_dump()
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/loan/{loan_id}",
         response_model=LoanApplicationResponse,
         tags=["ExecuteFunction"],
         operation_id="GetLoan")
def get_loan(
    loan_id: int,
    db: Session = Depends(get_db)
):
    """
    Get loan application details by ID.

    Parameters:
    - loan_id: Unique identifier of the loan application

    Returns:
    - LoanApplicationResponse: Complete details of the loan application
    """
    loan = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan application not found"
        )
    return loan

@app.post("/api/loan/{loan_id}/approve", 
          tags=["ExecuteFunction"],
          operation_id="ApproveLoan")
async def approve_loan(
    loan_id: int,
    approval: LoanApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Approve a loan application with specified terms.

    Parameters:
    - loan_id: Unique identifier of the loan application to approve
    - approval: LoanApprovalRequest containing:
        - approved_amount: Approved loan amount in ₹
        - interest_rate: Annual interest rate as a percentage
        - tenure_months: Loan duration in months (1-360)
        - reviewer_comments: Comments from the loan reviewer
        - loan_officer_id: ID of the loan officer
        - document_verifier_id: ID of the document verifier
        - field_agent_id: ID of the field agent
        - bank_manager_id: ID of the bank manager
        - branch_name: Name of the branch
        - verification_date: Date of document verification (optional)
        - field_visit_date: Date of field visit (optional)
        - manager_approval_date: Date of manager approval (optional)

    Returns:
    - Detailed response containing approval status and loan terms
    """
    loan = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan application not found")

    if loan.status != LoanStatusType.PENDING:
        raise HTTPException(status_code=400, detail="Can only approve applications in PENDING status")    # Update application status
    loan.status = LoanStatusType.APPROVED

    # Create decision record
    db_decision = LoanDecision(
        application_id=loan_id,
        status=LoanStatusType.APPROVED,
        decision_date=datetime.now(),
        reviewer_comments=approval.reviewer_comments,
        approved_amount=float(approval.approved_amount),
        interest_rate=float(approval.interest_rate),
        tenure_months=approval.tenure_months,
        loan_officer_id=approval.loan_officer_id,
        document_verifier_id=approval.document_verifier_id,
        field_agent_id=approval.field_agent_id,
        bank_manager_id=approval.bank_manager_id,
        branch_name=approval.branch_name,
        verification_date=approval.verification_date,
        field_visit_date=approval.field_visit_date,
        manager_approval_date=approval.manager_approval_date
    )

    db.add(db_decision)
    db.commit()
    db.refresh(db_decision)
    
    return {
        "status": "success",
        "message": "Loan application approved successfully",
        "loan_details": {
            "id": loan.id,
            "applicant_name": loan.applicant_name,
            "loan_amount": loan.loan_amount,
            "status": loan.status,
            "approved_amount": db_decision.approved_amount,
            "interest_rate": db_decision.interest_rate,
            "tenure_months": db_decision.tenure_months,
            "approved_at": db_decision.decision_date,
            "loan_officer_id": db_decision.loan_officer_id,
            "document_verifier_id": db_decision.document_verifier_id,
            "field_agent_id": db_decision.field_agent_id,
            "bank_manager_id": db_decision.bank_manager_id,
            "branch_name": db_decision.branch_name,
            "verification_date": db_decision.verification_date,
            "field_visit_date": db_decision.field_visit_date,
            "manager_approval_date": db_decision.manager_approval_date
        }
    }

@app.post("/api/loan/{loan_id}/reject", 
          tags=["ExecuteFunction"],
          operation_id="RejectLoan")
async def reject_loan(
    loan_id: int,
    rejection_reason: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    Reject a loan application with a reason.

    Parameters:
    - loan_id: Unique identifier of the loan application to reject
    - rejection_reason: Detailed reason for rejecting the application

    Returns:
    - Detailed response containing rejection status and reason
    """
    loan = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan application not found")

    if loan.status != LoanStatusType.PENDING:
        raise HTTPException(status_code=400, detail="Can only reject applications in PENDING status")

    if not rejection_reason:
        raise HTTPException(status_code=400, detail="Rejection reason is required")

    # Update application status
    loan.status = LoanStatusType.REJECTED

    # Create decision record
    db_decision = LoanDecision(
        application_id=loan_id,
        status=LoanStatusType.REJECTED,
        decision_date=datetime.now(),
        reviewer_comments="Application rejected",
        rejection_reason=rejection_reason
    )

    db.add(db_decision)
    db.commit()
    db.refresh(db_decision)

    return {
        "status": "success",
        "message": "Loan application rejected successfully",
        "loan_details": {
            "id": loan.id,
            "applicant_name": loan.applicant_name,
            "loan_amount": loan.loan_amount,
            "status": loan.status,
            "rejection_reason": rejection_reason,
            "rejected_at": db_decision.decision_date
        }
    }

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="127.0.0.1", port=int(os.getenv("PORT", 8000)), reload=True)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENV", "dev") == "dev"
    )
