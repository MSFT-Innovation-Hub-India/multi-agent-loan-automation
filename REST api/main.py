from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from typing import List
from database import engine, SessionLocal
import models
import schemas
from datetime import datetime

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Create FastAPI instance
app = FastAPI(title="Loan Processing API")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to Loan Processing API"}

@app.post("/api/loan/apply", response_model=schemas.LoanApplicationResponse)
async def apply_loan(
    loan_application: schemas.LoanApplicationCreate,
    db: Session = Depends(get_db)
):
    try:
        # Create new loan application
        db_loan = models.LoanApplication(
            applicant_name=loan_application.applicant_name,
            email=loan_application.email,
            phone=loan_application.phone,
            loan_amount=loan_application.loan_amount,
            loan_purpose=loan_application.loan_purpose,
            loan_term_months=loan_application.loan_term_months,
            monthly_income=loan_application.monthly_income,
            employment_type=loan_application.employment_type,
            status="DRAFT",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_loan)
        db.commit()
        db.refresh(db_loan)
        return db_loan

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/loan/{loan_id}", response_model=schemas.LoanApplicationResponse)
def get_loan(loan_id: int, db: Session = Depends(get_db)):
    loan = db.query(models.LoanApplication).filter(models.LoanApplication.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan application not found")
    return loan

@app.post("/api/loan/{loan_id}/submit")
async def submit_loan(loan_id: int, db: Session = Depends(get_db)):
    loan = db.query(models.LoanApplication).filter(models.LoanApplication.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan application not found")
    
    if loan.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Application already submitted")
    
    loan.status = "SUBMITTED"
    loan.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Loan application submitted successfully"}

@app.post("/api/loan/{loan_id}/approve")
async def approve_loan(loan_id: int, db: Session = Depends(get_db)):
    loan = db.query(models.LoanApplication).filter(models.LoanApplication.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan application not found")
    
    if loan.status != "SUBMITTED":
        raise HTTPException(status_code=400, detail="Application must be in SUBMITTED state to approve")
    
    loan.status = "APPROVED"
    loan.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "message": "Loan application approved successfully",
        "loan_details": {
            "id": loan.id,
            "applicant_name": loan.applicant_name,
            "loan_amount": loan.loan_amount,
            "status": loan.status,
            "approved_at": loan.updated_at
        }
    }

from fastapi import Body

@app.post("/api/loan/{loan_id}/reject")
async def reject_loan(
    loan_id: int,
    rejection_reason: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    loan = db.query(models.LoanApplication).filter(models.LoanApplication.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan application not found")
    
    if loan.status != "SUBMITTED":
        raise HTTPException(status_code=400, detail="Application must be in SUBMITTED state to reject")
    
    loan.status = "REJECTED"
    loan.rejection_reason = rejection_reason
    loan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(loan)
    
    return {
        "message": "Loan application rejected successfully",
        "loan_details": {
            "id": loan.id,
            "applicant_name": loan.applicant_name,
            "loan_amount": loan.loan_amount,
            "status": loan.status,
            "rejection_reason": loan.rejection_reason,
            "rejected_at": loan.updated_at
        }
    }
    
    return {
        "message": "Loan application rejected successfully",
        "loan_details": {
            "id": loan.id,
            "applicant_name": loan.applicant_name,
            "loan_amount": loan.loan_amount,
            "status": loan.status,
            "rejection_reason": loan.rejection_reason,
            "rejected_at": loan.updated_at.isoformat()
        }
    }
    
    return {
        "message": "Loan application rejected successfully",
        "loan_details": {
            "id": loan.id,
            "applicant_name": loan.applicant_name,
            "loan_amount": loan.loan_amount,
            "status": loan.status,
            "rejected_at": loan.updated_at,
            "rejection_reason": rejection_reason
        }
    }
