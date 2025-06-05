from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .loan_status import LoanStatusType

class LoanApplicationBase(BaseModel):
    applicant_name: str = Field(..., description="Full name of the loan applicant")
    gender: str = Field(..., description="Gender of the applicant")
    dob: datetime = Field(..., description="Date of birth")
    age: int = Field(..., ge=18, le=100, description="Age of the applicant")
    marital_status: str = Field(..., description="Marital status")
    education_level: str = Field(..., description="Education level")
    annual_income: float = Field(..., gt=0, description="Annual income in ₹")
    employment_type: str = Field(..., description="Type of employment")
    loan_amount: float = Field(..., gt=0, description="Requested loan amount in ₹")
    tenure_months: int = Field(..., gt=0, le=360, description="Loan tenure in months")
    credit_score: Optional[int] = Field(None, ge=300, le=850, description="Credit score")
    existing_loans: bool = Field(False, description="Has existing loans")
    num_existing_loans: int = Field(0, ge=0, description="Number of existing loans")
    total_emi_amount: float = Field(0.0, ge=0, description="Total EMI amount in ₹")
    loan_purpose: str = Field(..., description="Purpose of the loan")
    city: str = Field(..., description="City of residence")
    phone_number: str = Field(..., description="Contact phone number")
    email: str = Field(..., description="Email address")
    aadhaar_number: str = Field(..., min_length=12, max_length=12, description="Aadhaar number")
    pan_number: str = Field(..., min_length=10, max_length=10, description="PAN number")
    account_type: str = Field(..., description="Bank account type")
    guarantor_available: bool = Field(..., description="Is guarantor available")

class LoanApplicationCreate(LoanApplicationBase):
    pass

class LoanApplicationResponse(LoanApplicationBase):
    id: int
    application_date: datetime
    status: LoanStatusType

    class Config:
        from_attributes = True