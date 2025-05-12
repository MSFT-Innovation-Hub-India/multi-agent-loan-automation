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

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Get root_path from environment variable, default to "" for local development
root_path = os.getenv("ROOT_PATH", "")

app = FastAPI(
    title="Loan Processing API",
    description="REST API for loan processing and orchestration. Users will be able to submit loan applications, check loan status, and make approval/rejection decisions.",
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
    - email: Valid email address of the applicant
    - annual_income: Annual income in USD
    - loan_amount: Requested loan amount in USD
    - loan_purpose: Purpose of the loan
    - employment_status: Current employment status
    - credit_score: Credit score of the applicant

    Returns:
    - LoanApplicationResponse: Created loan application details with unique ID
    """
    try:
        db_application = LoanApplication(
            applicant_name=application.applicant_name,
            email=application.email,
            annual_income=float(application.annual_income),
            loan_amount=float(application.loan_amount),
            loan_purpose=application.loan_purpose,
            employment_status=application.employment_status,
            credit_score=application.credit_score,
            application_date=datetime.now(),
            status=LoanStatusType.PENDING  # Set initial status to PENDING
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
        - approved_amount: Approved loan amount in USD
        - interest_rate: Annual interest rate as a percentage
        - tenure_months: Loan duration in months
        - reviewer_comments: Optional comments from the loan reviewer

    Returns:
    - Detailed response containing approval status and loan terms
    """
    loan = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan application not found")

    if loan.status != LoanStatusType.PENDING:
        raise HTTPException(status_code=400, detail="Can only approve applications in PENDING status")

    # Update application status
    loan.status = LoanStatusType.APPROVED

    # Create decision record
    db_decision = LoanDecision(
        application_id=loan_id,
        status=LoanStatusType.APPROVED,
        decision_date=datetime.now(),
        reviewer_comments=approval.reviewer_comments,
        approved_amount=float(approval.approved_amount),
        interest_rate=float(approval.interest_rate),
        tenure_months=approval.tenure_months
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
            "approved_at": db_decision.decision_date
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
