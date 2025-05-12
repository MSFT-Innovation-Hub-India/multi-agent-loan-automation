from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class LoanStatusType(str, Enum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISBURSED = "DISBURSED"

class LoanStatus(BaseModel):
    application_id: int
    status: LoanStatusType
    last_updated: datetime
    reviewer_comments: Optional[str] = None
    risk_score: Optional[float] = Field(None, ge=0, le=100)
    approved_amount: Optional[float] = Field(None, gt=0)
    interest_rate: Optional[float] = Field(None, ge=0, le=100)
    tenure_months: Optional[int] = Field(None, gt=0, le=360)

    class Config:
        from_attributes = True

class EMIRequest(BaseModel):
    loan_amount: float = Field(..., gt=0)
    interest_rate: float = Field(..., gt=0, le=100)
    tenure_months: int = Field(..., gt=0, le=360)

class EMIResponse(BaseModel):
    emi_amount: float
    total_amount: float
    interest_amount: float

class LoanStatusUpdate(BaseModel):
    status: str = Field(..., description="Current status of the loan application")
    notes: Optional[str] = Field(None, description="Additional notes about the status update")

class LoanStatusResponse(LoanStatusUpdate):
    id: int
    loan_application_id: int
    updated_at: datetime
    class Config:
        from_attributes = True

class LoanDecisionRequest(BaseModel):
    decision: LoanStatusType = Field(..., description="Decision: APPROVED or REJECTED")
    reviewer_comments: str = Field(..., description="Reason for the decision")
    approved_amount: Optional[float] = Field(None, gt=0, description="Approved loan amount (required if approved)")
    interest_rate: Optional[float] = Field(None, ge=0, le=100, description="Interest rate (required if approved)")
    tenure_months: Optional[int] = Field(None, gt=0, le=360, description="Loan tenure in months (required if approved)")
    rejection_reason: Optional[str] = Field(None, description="Detailed reason for rejection (required if rejected)")

class LoanApprovalRequest(BaseModel):
    approved_amount: float = Field(..., gt=0, description="Approved loan amount")
    interest_rate: float = Field(..., ge=0, le=100, description="Annual interest rate")
    tenure_months: int = Field(..., gt=0, le=360, description="Loan tenure in months")
    reviewer_comments: str = Field(..., description="Comments from the loan reviewer")

class LoanRejectionRequest(BaseModel):
    rejection_reason: str = Field(..., description="Detailed reason for rejection")
    reviewer_comments: str = Field(..., description="Comments from the loan reviewer")

class LoanDecisionResponse(BaseModel):
    application_id: int
    status: LoanStatusType
    decision_date: datetime
    reviewer_comments: str
    approved_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    tenure_months: Optional[int] = None
    rejection_reason: Optional[str] = None

    class Config:
        from_attributes = True
