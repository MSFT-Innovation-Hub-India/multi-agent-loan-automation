# Loan Processing API

This is a FastAPI-based loan processing application that connects to Azure SQL Database using Azure AD authentication.

## Project Structure
```
loan_app/
├── main.py           # FastAPI application and API endpoints
├── database.py       # Database connection and session management
├── models.py         # SQLAlchemy ORM models
├── schemas.py        # Pydantic models for request/response validation
└── requirements.txt  # Project dependencies
```

## Setup Instructions

1. Install the ODBC Driver 18 for SQL Server:
   - Download from: https://go.microsoft.com/fwlink/?linkid=2249006
   - Install with: `msodbcsql18.msi IACCEPTMSODBCSQLLICENSETERMS=YES`

2. Create a `.env` file with your Azure SQL Database details:
   ```env
   AZURE_SQL_SERVER=your-server.database.windows.net
   AZURE_SQL_DATABASE=your-database-name
   AZURE_SQL_TENANT_ID=your-tenant-id
   AZURE_SQL_CLIENT_ID=your-client-id
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

5. Access the API documentation:
   - OpenAPI docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

- POST `/api/loan/apply` - Submit a new loan application
- GET `/api/loan/{loan_id}` - Get loan application details
- POST `/api/loan/{loan_id}/documents` - Upload documents for a loan application

## Authentication

This application uses Azure AD authentication to connect to Azure SQL Database. Make sure you have:
1. Proper Azure AD roles assigned to your account
2. ODBC Driver 18 for SQL Server installed
3. Correct environment variables set in `.env` file
