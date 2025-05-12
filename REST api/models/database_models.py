from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    applicant_name = Column(String(100))
    gender = Column(String(20))
    dob = Column(DateTime)
    age = Column(Integer)
    marital_status = Column(String(20))
    education_level = Column(String(50))
    annual_income = Column(Float)
    employment_type = Column(String(50))
    loan_amount = Column(Float)
    tenure_months = Column(Integer)
    credit_score = Column(Integer, nullable=True)
    existing_loans = Column(Boolean, default=False)
    num_existing_loans = Column(Integer, default=0)
    total_emi_amount = Column(Float, default=0.0)
    loan_purpose = Column(String(200))
    city = Column(String(100))
    phone_number = Column(String(20))
    email = Column(String(100))
    aadhaar_number = Column(String(12))
    pan_number = Column(String(10))
    account_type = Column(String(50))
    guarantor_available = Column(Boolean)
    application_date = Column(DateTime, default=func.now())
    loan_officer = Column(String(100))
    document_verifier = Column(String(100))
    field_agent = Column(String(100))
    bank_manager = Column(String(100))
    branch_name = Column(String(100))
    status = Column(String(20))

    # Relationship with LoanDecision
    decision = relationship("LoanDecision", back_populates="application", uselist=False)

class LoanDecision(Base):
    __tablename__ = "loan_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id"))
    status = Column(String(20))
    decision_date = Column(DateTime, default=func.now())
    reviewer_comments = Column(String(500))
    approved_amount = Column(Float, nullable=True)
    interest_rate = Column(Float, nullable=True)
    tenure_months = Column(Integer, nullable=True)
    rejection_reason = Column(String(500), nullable=True)
    loan_officer_id = Column(String(100))
    document_verifier_id = Column(String(100))
    field_agent_id = Column(String(100))
    bank_manager_id = Column(String(100))
    branch_name = Column(String(100))
    verification_date = Column(DateTime, nullable=True)
    field_visit_date = Column(DateTime, nullable=True)
    manager_approval_date = Column(DateTime, nullable=True)

    # Relationship with LoanApplication
    application = relationship("LoanApplication", back_populates="decision")
