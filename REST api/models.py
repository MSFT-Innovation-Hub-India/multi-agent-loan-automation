from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id = Column(Integer, primary_key=True, index=True)
    applicant_name = Column(String(100), nullable=False)
    email = Column(String(120), nullable=False)
    phone = Column(String(15), nullable=False)
    loan_amount = Column(Float, nullable=False)
    loan_purpose = Column(String(200), nullable=False)
    loan_term_months = Column(Integer, nullable=False)
    monthly_income = Column(Float, nullable=False)
    employment_type = Column(String(50), nullable=False)
    status = Column(String(50), default="DRAFT")
    rejection_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)