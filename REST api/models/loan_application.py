from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .loan_status import LoanStatusType

class LoanApplicationBase(BaseModel):
    applicant_name: str = Field(..., description="Full name of the loan applicant")
    email: str = Field(..., description="Email address of the applicant")
    annual_income: float = Field(..., gt=0, description="Annual income of the applicant")
    loan_amount: float = Field(..., gt=0, description="Requested loan amount")
    loan_purpose: str = Field(..., description="Purpose of the loan")
    employment_status: str = Field(..., description="Current employment status")
    credit_score: Optional[int] = Field(None, ge=300, le=850, description="Credit score of the applicant")

class LoanApplicationCreate(LoanApplicationBase):
    pass

class LoanApplicationResponse(LoanApplicationBase):
    id: int
    application_date: datetime
    status: LoanStatusType

    class Config:
        from_attributes = True