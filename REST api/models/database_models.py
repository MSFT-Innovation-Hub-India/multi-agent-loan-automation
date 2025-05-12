from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    applicant_name = Column(String(100))
    email = Column(String(100))
    annual_income = Column(Float)
    loan_amount = Column(Float)
    loan_purpose = Column(String(200))
    employment_status = Column(String(50))
    credit_score = Column(Integer, nullable=True)
    application_date = Column(DateTime, default=func.now())
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

    # Relationship with LoanApplication
    application = relationship("LoanApplication", back_populates="decision")
