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
    BankEmployees,
    AuditRecords
)
import uvicorn
import os
from dotenv import load_dotenv
load_dotenv()
# --- Audit Log Models ---
from pydantic import BaseModel

class AuditLogRequest(BaseModel):
    customer_id: str
    audit_type: str
    audit_status: str
    audit_name: str
    remarks: str
    agent_name: str
    follow_up_required: bool
    response: str = None

class AuditLogResponse(BaseModel):
    audit_type: str
    audit_status: str
    audit_date: str
    remarks: str
    agent_name: str
    follow_up_required: str

class AuditRecordRequest(BaseModel):
    customer_id: str
    audit_type: str
    audit_status: str
    auditor_name: str
    remarks: str
    follow_up_required: str
    is_active: bool = True

class AuditRecordResponse(BaseModel):
    audit_id: int
    customer_id: str
    event_time: str
    audit_type: str
    audit_status: str
    auditor_name: str
    remarks: str
    follow_up_required: str
    is_active: bool

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
            "url": "https://loanauditagent.azurewebsites.net"
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

@app.post("/api/audit-records", tags=["ExecuteFunction"], operation_id="CreateAuditRecord")
async def create_audit_record(
    record: AuditRecordRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new audit record.
    Returns the created audit record as confirmation.
    """
    try:
        # Check if customer exists
        customer = db.query(MasterCustomerData).filter_by(Customer_ID=record.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        audit = AuditRecords(
            Customer_ID=record.customer_id,
            Audit_Type=record.audit_type,
            Audit_Status=record.audit_status,
            Auditor_Name=record.auditor_name,
            Remarks=record.remarks,
            Follow_Up_Required=record.follow_up_required,
            IsActive=1 if record.is_active else 0
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)
        
        return {
            "message": "Audit record created successfully",
            "record": {
                "audit_id": audit.Audit_ID,
                "customer_id": audit.Customer_ID,
                "event_time": audit.Event_Time.isoformat(),
                "audit_type": audit.Audit_Type,
                "audit_status": audit.Audit_Status,
                "auditor_name": audit.Auditor_Name,
                "remarks": audit.Remarks,
                "follow_up_required": audit.Follow_Up_Required,
                "is_active": bool(audit.IsActive)
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audit-records/{customer_id}", tags=["ExecuteFunction"], operation_id="GetAuditRecordsAsJson")
async def get_audit_records_as_json(
        customer_id: str,
        db: Session = Depends(get_db)
    ):
        """
        Get all audit records for a customer as a JSON array (not a string).
        Returns the records sorted by event time.
        """
        try:
            # Check if customer exists
            customer = db.query(MasterCustomerData).filter_by(Customer_ID=customer_id).first()
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")

            records = db.query(AuditRecords).filter_by(Customer_ID=customer_id).order_by(AuditRecords.Event_Time.asc()).all()
            result = []
            for r in records:
                result.append({
                    "Audit_ID": r.Audit_ID,
                    "Customer_ID": r.Customer_ID,
                    "Event_Time": r.Event_Time.isoformat() if r.Event_Time else None,
                    "Audit_Type": r.Audit_Type,
                    "Audit_Status": r.Audit_Status,
                    "Auditor_Name": r.Auditor_Name,
                    "Remarks": r.Remarks,
                    "Follow_Up_Required": r.Follow_Up_Required,
                    "IsActive": bool(r.IsActive)
                })
            return {"records": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

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
