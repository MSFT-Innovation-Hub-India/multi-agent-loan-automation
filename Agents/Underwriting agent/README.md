# Credit Underwriting Agent

## Overview

The Credit Underwriting Agent is an AI-powered supervisory assistant designed for credit assessment, risk analysis, and loan underwriting processes. It integrates with Azure AI services and Azure SQL Database to provide comprehensive automated credit analysis for Global Trust Bank.

## Features

### 🔧 Technical Capabilities
- **Direct Database Access**: Real-time connectivity to Global Trust Bank's Azure SQL Database
- **Automated Data Retrieval**: Customer information retrieved automatically using Customer ID
- **AI-Powered Analysis**: Azure AI integration for intelligent credit assessment
- **Risk Assessment**: Comprehensive creditworthiness evaluation
- **Document Verification**: Automated KYC and document status checking

### 📊 Database Integration
- **Master_Customer_Data**: Personal information, KYC status, contact details
- **Employment_Info**: Job details, income, work experience
- **Bank_Info**: Account details, balances, banking relationship
- **Loan_Info**: Loan applications, credit scores, loan history
- **Transaction_History**: Banking transactions, financial behavior

### 🎯 Core Functions
- Complete customer profile analysis
- Credit score evaluation
- Debt-to-Income (DTI) ratio calculation
- Risk factor identification
- Loan recommendations
- Document verification status
- Transaction pattern analysis

## Prerequisites

### Required Python Packages
```bash
pip install azure-ai-projects==1.0.0b10 pyodbc
```

### Dependencies
- **azure-ai-projects**: Azure AI integration
- **azure.identity**: Azure authentication
- **pyodbc**: SQL Server database connectivity
- **datetime**: Date/time operations
- **json**: JSON data handling

### System Requirements
- Python 3.7+
- Azure AI Projects account
- Azure SQL Database access
- ODBC Driver 18 for SQL Server

## Installation

1. **Clone or download the script**:
   ```bash
   git clone <repository-url>
   cd underwriting-agent
   ```

2. **Install required packages**:
   ```bash
   pip install azure-ai-projects==1.0.0b10 pyodbc
   ```

3. **Configure Azure credentials**:
   - Set up DefaultAzureCredential
   - Update connection string for your Azure AI project
   - Configure database connection parameters

## Configuration

### Database Configuration
Update the database connection parameters in the `initialize_database_connection()` method:

```python
server = 'your-server.database.windows.net'
database = 'Your_Database_Name'
username = 'your-username'
password = 'your-password'
```

### Azure AI Configuration
Update the connection string in the `initialize_agent()` method:

```python
conn_str = "your-azure-ai-connection-string"
agent_id = "your-agent-id"
```

## Usage

### Running the Application
```bash
python under-writing-agent.py
```

### Basic Commands
- **Customer Analysis**: `Analyze customer CUST0006`
- **Alternative Format**: `Customer ID CUST0006`
- **General Questions**: Ask about underwriting processes
- **Special Commands**:
  - `capabilities` - Show available features
  - `new conversation` - Start fresh thread
  - `thread info` - Display current session info
  - `db status` - Check database connection
  - `quit/exit/bye` - End session

## Sample Input and Output

### Sample Input 1: Customer Analysis Request
```
You: Analyze customer CUST0006
```

### Sample Output 1: Comprehensive Credit Analysis Report
```
📊 **CREDIT UNDERWRITING ANALYSIS REPORT**
═══════════════════════════════════════════

**CUSTOMER:** Rajesh Kumar Singh (ID: CUST0006)
**DATE:** 2025-06-20 14:30:45

🏷️ **PERSONAL INFORMATION**
• Name: Rajesh Kumar Singh
• Father's Name: Ram Kumar Singh
• Age: 32 years
• Gender: Male
• PAN: ABCDE1234F
• Aadhaar: 1234-5678-9012
• Phone: +91-9876543210
• Email: rajesh.singh@email.com
• Address: 123 MG Road, Mumbai, Maharashtra - 400001
• KYC Status: Verified
• Customer Since: 2020-03-15

💼 **EMPLOYMENT INFORMATION**
• Employment Type: Salaried
• Employer: Tech Solutions Pvt Ltd
• Designation: Senior Software Engineer
• Work Experience: 8 years
• Employment Status: Active
• Income Verification: Verified

💰 **FINANCIAL PROFILE**
• Monthly Income: ₹75,000.00
• Other Income: ₹5,000.00
• Total Monthly Income: ₹80,000.00
• Account Balance: ₹2,50,000.00
• Average Monthly Balance: ₹1,80,000.00
• Credit Score: 785

🏦 **BANKING INFORMATION**
• Bank Name: Global Trust Bank
• Account Type: Salary Account
• Account Status: Active
• Customer Category: Premium

📋 **LOAN APPLICATION DETAILS**
• Loan Amount Requested: ₹15,00,000.00
• Loan Purpose: Home Purchase
• Loan Type: Home Loan
• Proposed EMI: ₹18,500.00
• Interest Rate: 8.5%
• Tenure: 240 months
• Application Date: 2025-06-18
• Current Status: Under Review
• Collateral Required: Property Mortgage
• Insurance Required: Yes

📊 **RISK ANALYSIS**
• Risk Score: 85/100
• Risk Category: Low Risk
• DTI Ratio: 23.13%
• LTI Ratio: 15.63%

⚠️ **RISK FACTORS:**
• No significant risk factors identified

✅ **UNDERWRITING RECOMMENDATIONS:**
• ✅ APPROVE - Low risk profile
• Recommended loan amount: ₹15,00,000.00
• Standard interest rate applicable

📈 **TRANSACTION SUMMARY (Last 3 Months):**
• Total Transactions: 45
• Total Credits: ₹2,40,000.00
• Total Debits: ₹1,85,000.00
• Average Transaction: ₹5,200.00

📄 **DOCUMENT VERIFICATION STATUS:**
• KYC Status: Verified
• PAN Card: ✅ Available
• Aadhaar Card: ✅ Available
• Income Verification: Verified

👥 **PROCESSING TEAM:**
• Document Verifier: Priya Sharma
• Field Agent: Amit Patel
• Bank Manager: Suresh Reddy
• Loan Officer: Kavita Joshi

🤖 **AI AGENT'S PROFESSIONAL ANALYSIS:**
═══════════════════════════════════════════

**CREDITWORTHINESS ASSESSMENT:** 
Excellent creditworthiness profile. Customer demonstrates strong financial stability with consistent income, healthy credit score of 785, and substantial banking relationship spanning 5 years.

**KEY STRENGTHS:**
• Outstanding credit score (785) - well above approval threshold
• Stable employment with 8+ years experience in IT sector
• Strong DTI ratio of 23.13% - well within acceptable limits
• Verified income documentation and KYC compliance
• Healthy account balance and transaction patterns

**CONCERNS & WEAKNESSES:**
• No significant concerns identified
• Minor consideration: Loan amount represents 15.6x monthly income (within acceptable range)

**LOAN RECOMMENDATION:**
Strong approval candidate with minimal risk factors. All documentation verified and financial ratios within policy guidelines.

**SUGGESTED TERMS:**
• Loan Amount: ₹15,00,000 (as requested)
• Interest Rate: 8.5% (standard rate applicable)
• Tenure: 20 years (as requested)
• Processing Fee: ₹30,000

**CONDITIONS:**
• Property valuation report
• Legal clearance of property documents
• Home insurance policy activation

**NEXT STEPS:**
1. Property verification by technical team
2. Legal document review
3. Final sanction letter preparation

**📋 FINAL RECOMMENDATION:** APPROVE loan of ₹15,00,000 at 8.5% interest rate with standard terms and conditions.
═══════════════════════════════════════════
```

### Sample Input 2: General Query
```
You: What factors do you consider for DTI ratio calculation?
```

### Sample Output 2: Educational Response
```
🏦 Credit Underwriting Agent:

**Debt-to-Income (DTI) Ratio Calculation - Key Factors:**

📊 **PRIMARY COMPONENTS:**
• **Monthly Debt Obligations**: All recurring monthly debt payments
• **Gross Monthly Income**: Total income before taxes and deductions

🔢 **DEBT COMPONENTS INCLUDED:**
• Existing loan EMIs (home, personal, auto loans)
• Credit card minimum payments
• Other recurring debt obligations
• Proposed new loan EMI (for approval assessment)

💰 **INCOME COMPONENTS:**
• Primary salary/business income
• Verified additional income sources
• Rental income (if applicable)
• Investment returns (regular/recurring)

📈 **DTI CALCULATION FORMULA:**
DTI Ratio = (Total Monthly Debt Payments / Gross Monthly Income) × 100

⚖️ **ACCEPTABLE DTI THRESHOLDS:**
• **Excellent**: Below 20% - Minimal risk
• **Good**: 20-30% - Acceptable risk
• **Moderate**: 30-40% - Requires careful evaluation
• **High Risk**: Above 40% - Generally not recommended

🎯 **UNDERWRITING GUIDELINES:**
• Home Loans: DTI should not exceed 40%
• Personal Loans: DTI should not exceed 50%
• Multiple loans: Combined DTI assessment required

This ratio helps assess the borrower's ability to manage monthly payments and repay new debt responsibly.
```

### Sample Input 3: Database Status Check
```
You: db status
```

### Sample Output 3: System Status
```
✅ Database connection: Active
🔍 Customer analysis: Available
```

## Error Handling

The system includes comprehensive error handling for:
- Database connection failures
- Customer ID not found
- Invalid data formats
- Azure AI service connectivity issues
- Network timeouts

## File Structure

```
underwriting-agent/
│
├── under-writing-agent.py    # Main application file
├── README.md                 # This documentation
└── __pycache__/             # Python cache files
    └── under-writing-agent.cpython-313.pyc
```

## Key Classes and Methods

### CreditUnderwritingAgent Class

#### Core Methods:
- `initialize_database_connection()`: Establishes Azure SQL connection
- `get_customer_data(customer_id)`: Retrieves comprehensive customer data
- `analyze_credit_profile(customer_data)`: Performs risk assessment
- `initialize_agent()`: Sets up Azure AI agent
- `get_agent_response(user_message)`: Processes user queries
- `handle_customer_analysis(user_message)`: Specialized customer analysis

#### Utility Methods:
- `safe_format_currency(value)`: Currency formatting with error handling
- `safe_format_number(value, default)`: Number formatting with defaults
- `display_agent_capabilities()`: Shows available features

## Security Considerations

- Database credentials should be stored securely (environment variables recommended)
- Azure credentials managed through DefaultAzureCredential
- Customer data handled according to banking privacy regulations
- Connection encryption enabled for database communications

## Performance Features

- Efficient SQL queries with JOINs for comprehensive data retrieval
- Cached database connections
- Optimized data processing for large customer datasets
- Real-time transaction analysis

## Troubleshooting

### Common Issues:

1. **Database Connection Failed**:
   - Verify connection string parameters
   - Check network connectivity
   - Ensure ODBC driver is installed

2. **Customer Not Found**:
   - Verify customer ID format (CUST0001, CUST0006, etc.)
   - Check database permissions
   - Confirm customer exists in system

3. **Azure AI Connection Issues**:
   - Verify Azure credentials
   - Check connection string
   - Ensure AI service is accessible

## Support

For technical support or questions:
- Review error messages in console output
- Check database connectivity
- Verify Azure service status
- Ensure all dependencies are installed

## Version Information

- **Version**: 1.0
- **Python**: 3.7+
- **Azure AI Projects**: 1.0.0b10
- **Last Updated**: June 2025

---

**Note**: This application handles sensitive financial data. Ensure compliance with relevant banking regulations and data privacy laws in your jurisdiction.
