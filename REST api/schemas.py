from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class LoanApplicationCreate(BaseModel):
    applicant_name: str
    email: EmailStr
    phone: str
    loan_amount: float
    loan_purpose: str
    loan_term_months: int
    monthly_income: float
    employment_type: str

class LoanApplicationBase(BaseModel):
    applicant_name: str
    email: EmailStr
    phone: str
    loan_amount: float
    loan_purpose: str
    loan_term_months: int
    monthly_income: float
    employment_type: str

class LoanApplicationCreate(LoanApplicationBase):
    pass

class LoanApplicationResponse(LoanApplicationBase):
    id: int
    status: str
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
