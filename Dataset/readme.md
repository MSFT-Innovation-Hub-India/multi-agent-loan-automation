# Global Trust Bank - Dataset

This folder contains sample datasets and document archives used for the multi-agent loan automation system. It is intended for development, testing, and demonstration purposes.

## Contents

### SQL Data Files

- **audit_log.sql**: Audit trail and action logs for all loan processing activities.
- **bank_employees.sql**: Sample data for bank employee records.
- **bank_info.sql**: Bank branch and institution information.
- **employment_info.sql**: Employment and income details for customers.
- **loan_info.sql**: Loan application and approval data.
- **master_customer_data_snake_case.sql**: Master customer data in snake_case format.
- **tables.sql**: Table creation scripts for all relevant entities.
- **transaction_history.sql**: Transaction records for customer accounts.

### Document Archive

- **Document/**: Contains subfolders for each customer (e.g., `CUST0001/`, `CUST0006/`).
    - Each subfolder includes scanned documents and PDFs such as:
        - Aadhaar card
        - PAN card
        - Bank transaction statements
        - CIBIL score reports
        - Form 16 and pay slips
        - Land/property documents
        - Income certificates
        - Marriage certificates
        - Passport copies

## Usage

- Use the SQL files to populate your development or demo database.
- The `Document/` directory can be used for document verification, OCR, and AI-based analysis workflows.

## Notes

- All data is synthetic and for internal use only.
- Do not use this data for production or share outside the organization.

