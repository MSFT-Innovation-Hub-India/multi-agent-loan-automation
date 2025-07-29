from fastapi import FastAPI, HTTPException, status, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db, engine, Base
from models.database_models import (
    MasterCustomerData,
    EmploymentInfo,
    LoanInfo,
    BankInfo,
    TransactionHistory,
    AuditLog,
    BankEmployees
)
import uvicorn
import os

# Create database tables
Base.metadata.create_all(bind=engine)

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
            "url": "https://prequalification.azurewebsites.net"
        }
    ],
    openapi_tags=[
        {
            "name": "ExecuteFunction",
            "description": "Operations for loan processing and orchestration"
        },
        {
            "name": "root",
            "description": "Root endpoint operations"
        },
        {
            "name": "health",
            "description": "Health check operations"
        },
        {
            "name": "Eligibility",
            "description": "Loan eligibility and qualification operations"
        }
    ]
)

# Add CORS middleware with specific configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
    max_age=3600,  # Maximum time to cache preflight requests
)

@app.get("/",
         tags=["root"],
         operation_id="GetRoot")
def read_root():
    """
    Welcome endpoint for the Loan Processing API.
    
    Returns:
    - Dict: Welcome message
    """
    return {"message": "Welcome to Loan Processing API"}

@app.get("/health",
         tags=["health"],
         operation_id="HealthCheck")
async def health_check(
    db: Session = Depends(get_db)
):
    """
    Health check endpoint that verifies database connectivity.
    
    Parameters:
    - db: Database session dependency
    
    Returns:
    - Dict: Health status with database connectivity information
    """
    try:
        # Test database connection
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

@app.get("/api/users/{customer_id}/summary",
         tags=["ExecuteFunction"],
         operation_id="GetCustomerSummary")
async def get_customer_summary(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """
    Get customer summary including loan history, income, and credit score.
    
    Parameters:
    - customer_id: Unique identifier of the customer
    - db: Database session dependency
    
    Returns:
    - Dict: Customer profile with loan details and financial information
    """
    # Get customer and employment info
    customer = db.query(MasterCustomerData).filter_by(Customer_ID=customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    employment = db.query(EmploymentInfo).filter_by(Customer_ID=customer_id).first()

    # Get all loans with amount > 0 (active applications or disbursed loans)
    loans = db.query(LoanInfo).filter(
        LoanInfo.Customer_ID == customer_id,
        LoanInfo.Loan_Required == "Yes",
        LoanInfo.Loan_Amount > 0
    ).all()

    # Get credit score from most recent loan application
    latest_loan = db.query(LoanInfo).filter_by(
        Customer_ID=customer_id,
        Loan_Required="Yes"
    ).order_by(LoanInfo.Application_Date.desc()).first()
    
    credit_score = latest_loan.Credit_Score if latest_loan else None

    # Format existing loans
    existing_loans = []
    for loan in loans:
        existing_loans.append({
            "type": loan.Loan_Purpose,  # Using Loan_Purpose as it contains "Car", "Home", etc.
            "amount": float(loan.Loan_Amount),
            "monthly_emi": float(loan.EMI) if loan.EMI else 0,
            "tenure_years": (loan.Tenure_Months or 0) // 12,  # Convert months to years
            "status": loan.Loan_Status
        })

    return {
        "customer_id": customer.Customer_ID,
        "name": customer.Name,
        "monthly_income": float(employment.Monthly_Income) if employment else 0,
        "credit_score": credit_score,
        "existing_loans": existing_loans
    }
@app.get("/api/users/{customer_id}/eligibility", tags=["Eligibility"], operation_id="GetHomeLoanEligibility")
async def get_home_loan_eligibility(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """
    Estimate home loan eligibility based on monthly income, credit score, age, and existing EMIs.

    Parameters:
    - customer_id: Unique customer ID

    Returns:
    - Dict with eligible loan amount, interest rate, and fixed tenure
    """
    # Fetch customer details and validate existence
    customer = db.query(MasterCustomerData).filter_by(Customer_ID=customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Age validation (21-65 years)
    if not customer.Age:
        raise HTTPException(status_code=400, detail="Age information not found")
    
    age = int(customer.Age)
    if age < 21 or age > 65:
        return {
            "loan_amount_he_can_apply": 0,
            "interest_rate_starting_from": "N/A",
            "tenure_years": 0,
            "reason": f"Age {age} is outside eligible range (21-65 years)"
        }

    # Get employment info and validate income
    employment = db.query(EmploymentInfo).filter_by(Customer_ID=customer_id).first()
    if not employment:
        raise HTTPException(status_code=400, detail="Employment information not found")

    # Use Total_Monthly_Income if available, otherwise calculate from Monthly_Income and Other_Income
    monthly_income = float(employment.Total_Monthly_Income or 0)
    if monthly_income == 0:
        monthly_income = float(employment.Monthly_Income or 0) + float(employment.Other_Income or 0)

    if monthly_income == 0:
        raise HTTPException(status_code=400, detail="Valid income information not found")

    # Get latest loan application for credit score
    latest_loan = db.query(LoanInfo).filter(
        LoanInfo.Customer_ID == customer_id,
        LoanInfo.Loan_Required == "Yes"
    ).order_by(LoanInfo.Application_Date.desc()).first()

    # Credit score check
    credit_score = float(latest_loan.Credit_Score) if latest_loan and latest_loan.Credit_Score else None
    if credit_score and credit_score < 650:  # Minimum credit score threshold
        return {
            "loan_amount_he_can_apply": 0,
            "interest_rate_starting_from": "N/A",
            "tenure_years": 0,
            "reason": "Credit score below minimum requirement"
        }

    # Get all active loans
    active_loans = db.query(LoanInfo).filter(
        LoanInfo.Customer_ID == customer_id,
        LoanInfo.Loan_Required == "Yes",
        LoanInfo.Loan_Amount > 0,
        LoanInfo.Loan_Status.notin_(["REJECTED", "CLOSED"])  # Only consider active loans
    ).all()

    # Calculate total EMI obligations
    total_existing_emi = sum(float(loan.EMI or 0) for loan in active_loans)

    # Eligibility calculation parameters
    INTEREST_RATE = 0.085  # 8.5% base rate
    TENURE_YEARS = min(30, 65 - age)  # Adjust tenure based on age to not exceed 65 years
    TENURE_MONTHS = TENURE_YEARS * 12
    monthly_interest = INTEREST_RATE / 12
    MAX_OBLIGATIONS_RATIO = 0.4  # Maximum 40% of income for loan obligations

    # Maximum affordable EMI (40% of income - existing EMIs)
    max_emi = (MAX_OBLIGATIONS_RATIO * monthly_income) - total_existing_emi

    # If no room for additional EMI
    if max_emi <= 0:
        return {
            "loan_amount_he_can_apply": 0,
            "interest_rate_starting_from": "8.5%",
            "tenure_years": TENURE_YEARS,
            "reason": "Existing loan obligations exceed maximum allowed percentage of income"
        }

    # Calculate eligible loan amount using EMI formula
    # P = EMI * {(1 + r)^n - 1} / {r * (1 + r)^n}
    # where P is principal (loan amount), r is monthly interest rate, n is tenure in months
    numerator = (1 + monthly_interest) ** TENURE_MONTHS - 1
    denominator = monthly_interest * (1 + monthly_interest) ** TENURE_MONTHS
    eligible_loan = max_emi * (numerator / denominator)

    # Round to nearest thousand for cleaner numbers
    eligible_loan = round(eligible_loan / 1000) * 1000

    return {
        "loan_amount_he_can_apply": eligible_loan,
        "interest_rate_starting_from": "8.5%",
        "tenure_years": TENURE_YEARS,
        "current_obligations": total_existing_emi,
        "max_emi_allowed": round(MAX_OBLIGATIONS_RATIO * monthly_income, 2)
    }


@app.get("/api/loan/discovery-steps",
         tags=["ExecuteFunction"],
         operation_id="GetLoanDiscoverySteps")
async def get_discovery_steps(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """
    Get loan discovery steps based on customer status, verifying all relevant table data.
    
    Parameters:
    - customer_id: Unique identifier of the customer
    - db: Database session dependency
    
    Returns:
    - Dict: Customized loan discovery steps based on customer profile
    """
    # Check if customer exists and get complete customer data
    customer = db.query(MasterCustomerData).filter_by(Customer_ID=customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Get all related data
    employment = db.query(EmploymentInfo).filter_by(Customer_ID=customer_id).first()
    bank_info = db.query(BankInfo).filter_by(Customer_ID=customer_id).first()
    loans = db.query(LoanInfo).filter(
        LoanInfo.Customer_ID == customer_id,
        LoanInfo.Loan_Required == "Yes",
        LoanInfo.Loan_Amount > 0
    ).all()

    steps = []
    customer_status = "New"
    
    # Verify customer status based on Customer_Since
    if customer.Customer_Since:
        customer_status = "Existing"

    # Check active loans
    active_loans = [loan for loan in loans if loan.Loan_Status and loan.Loan_Status.upper() not in ["REJECTED", "CLOSED"]]
    if active_loans:
        loan_details = []
        for loan in active_loans:
            status_text = f"({loan.Loan_Status})" if loan.Loan_Status else ""
            loan_details.append(f"{loan.Loan_Purpose} Loan ₹{loan.Loan_Amount:,} {status_text}")
        steps.append(f"Step 1: Review your loan applications: {', '.join(loan_details)}.")
    else:
        steps.append("Step 1: No active loan applications found. Let's start fresh.")

    # Verify KYC status - Check if both PAN and Aadhaar exist
    kyc_verified = bool(customer.PAN and customer.Aadhaar)
    if not kyc_verified:
        steps.append("Step 2: Please complete your KYC by submitting Aadhaar, PAN, and address proof.")
    else:
        steps.append("Step 2: KYC is complete.")

    # Employment verification
    if employment:
        # Include total monthly income for better context
        total_income = float(employment.Total_Monthly_Income) if employment.Total_Monthly_Income else (
            float(employment.Monthly_Income or 0) + float(employment.Other_Income or 0)
        )
        income_text = f" Total monthly income: ₹{total_income:,.2f}." if total_income > 0 else ""
        steps.append(f"Step 3: Employment type is {employment.Employment_Type}. "
                    f"Income verification status: {employment.Income_Verification}.{income_text}")
    else:
        steps.append("Step 3: Please submit employment details including salary slips or IT returns.")

    # Risk assessment
    if customer.Risk_Category and customer.Risk_Category.lower() in ["high", "very high"]:
        steps.append("Step 4: As a high-risk customer, additional scrutiny will be applied.")
    elif customer.Fraud_Flag and customer.Fraud_Flag.lower() == "yes":
        steps.append("Step 4: Additional verification required due to security flags.")
    else:
        steps.append("Step 4: Risk profile accepted.")

    # Property document requirement
    if bank_info and bank_info.Account_Status.upper() == "FROZEN":
        steps.append("Step 5: Your bank account is frozen. Please resolve this before proceeding with property documents.")
    else:
        steps.append("Step 5: Submit property documents (sale deed, valuation report) for the home you want to purchase.")
    
    # Get credit score from most recent loan application
    latest_loan = None
    if loans:
        latest_loan = max(loans, key=lambda x: x.Application_Date if x.Application_Date else datetime.min)
    credit_score = latest_loan.Credit_Score if latest_loan else "not available"
    
    # Add eligibility calculation step
    steps.append(f"Step 6: Based on all documents and your credit score ({credit_score}), eligibility will be calculated.")
    
    # Final step with contact method based on bank info
    contact_methods = []
    if bank_info:
        if bank_info.Mobile_Banking == "Active":
            contact_methods.append("mobile app")
        if bank_info.Internet_Banking == "Active":
            contact_methods.append("internet banking")
    if contact_methods:
        steps.append(f"Step 7: Final offer will be shared through your registered {' and '.join(contact_methods)}.")
    else:
        steps.append("Step 7: Final offer will be shared on your registered email/mobile.")

    return {
        "customer_status": customer_status,
        "loan_type": "Home Loan",
        "steps": steps
    }

@app.get("/api/users/search",
         tags=["ExecuteFunction"],
         operation_id="GetCustomerIdByName")
async def get_customer_id_by_name(
    name: str,
    db: Session = Depends(get_db)
):
    """
    Get Customer ID based on customer name.
    
    Parameters:
    - name: Name of the customer to search for
    - db: Database session dependency
    
    Returns:
    - Dict: List of matching customers with their details
    """
    # Search for customers with similar names (case-insensitive)
    customers = db.query(MasterCustomerData).filter(
        MasterCustomerData.Name.ilike(f"%{name}%")
    ).all()
    
    if not customers:
        raise HTTPException(
            status_code=404,
            detail=f"No customers found with name containing '{name}'"
        )

    # Return list of matching customers with relevant details
    results = []
    for customer in customers:
        results.append({
            "customer_id": customer.Customer_ID,
            "name": customer.Name,
            "age": customer.Age,
            "city": customer.City,
            "state": customer.State,
            "customer_since": customer.Customer_Since.isoformat() if customer.Customer_Since else None
        })

    return {
        "search_term": name,
        "matches_found": len(results),
        "customers": results
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENV", "dev") == "dev"
    )
