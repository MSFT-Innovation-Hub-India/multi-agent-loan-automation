# Loan Offer Generation Agent

## Overview
The Loan Offer Generation Agent is an AI-powered automated system for Global Trust Bank that assesses home loan applications, calculates personalized loan offers, and generates comprehensive loan proposals. The agent integrates with Azure SQL Database, Azure AI Projects, and Logic Apps to provide end-to-end loan processing automation.

## Features

### 🏦 Core Functionality
- **Automated Loan Assessment**: Comprehensive eligibility evaluation based on customer data
- **Personalized Interest Rates**: Dynamic rate calculation based on customer profile
- **Multiple Loan Options**: Provides various tenure options (15, 20, 25, 30 years)
- **AI-Powered Summaries**: Generates intelligent loan officer recommendations
- **Email Automation**: Sends formatted loan offers via Logic Apps

### 📊 Assessment Criteria
- Credit score validation (minimum 650)
- Income verification and EMI capacity analysis
- Loan-to-Value (LTV) ratio calculation (max 85%)
- Employment stability evaluation
- Risk category assessment
- Banking relationship analysis

### 💰 Loan Parameters
- **Minimum Credit Score**: 650
- **Maximum LTV Ratio**: 85%
- **Income Multiplier**: 3.5x
- **Maximum Tenure**: 30 years
- **Base Interest Rate**: 8.5%
- **Processing Fee**: 0.5% of loan amount
- **Insurance Premium**: 0.25% of loan amount

## Prerequisites

### Software Requirements
- Python 3.8+
- Azure SQL Database access
- Azure AI Projects access
- ODBC drivers for SQL Server

### Python Dependencies
```bash
pip install azure-ai-projects==1.0.0b10
pip install pyodbc
pip install requests
pip install azure-identity
```

### Environment Setup
1. **Azure SQL Database**: Access to Global Trust Bank database
2. **Azure AI Projects**: Configured AI assistant for loan summaries
3. **Logic Apps**: Email automation endpoint
4. **ODBC Drivers**: SQL Server drivers for database connectivity

## Configuration

### Database Configuration
```python
SERVER = "global-trust-bank.database.windows.net"
DATABASE = "Global_Trust_Bank"
USERNAME = "your_username"
PASSWORD = "your_password"
```

### Required Database Tables
- `Master_Customer_Data` - Customer personal information
- `Employment_Info` - Employment and income details
- `Bank_Info` - Account and banking relationship data
- `Loan_Info` - Existing loan information
- `Transaction_History` - Transaction patterns

## Usage

### Running the Agent
```bash
python loan_offer_generation_agent.py
```

### Menu Options
1. **Assess loan for Customer ID with collateral** - Full loan assessment
2. **Quick eligibility check** - Basic customer eligibility
3. **Exit** - Close the application

### Example Usage

#### Full Loan Assessment
```python
# Customer ID
customer_id = "CUST0001"

# Collateral Information (JSON format)
collateral_info = {
    "property_value": 5000000,
    "property_type": "Apartment", 
    "location": "Mumbai"
}

# Requested loan amount (optional)
requested_amount = 4000000

# Generate loan offer
generate_loan_offer(customer_id, collateral_info, requested_amount)
```

#### Programmatic Usage
```python
from loan_offer_generation_agent import generate_loan_offer

# Generate loan offer
result = generate_loan_offer(
    customer_id="CUST0001",
    collateral_json='{"property_value": 5000000, "property_type": "Apartment", "location": "Mumbai"}',
    requested_amount=4000000
)

if result:
    print("Loan offer generated successfully!")
    print(f"Final interest rate: {result['final_rate']:.2f}%")
    print(f"Available loan options: {len(result['loan_options'])}")
```

## Key Functions

### Core Functions
- `get_customer_data(customer_id)` - Retrieves comprehensive customer information
- `assess_loan_eligibility(customer_data, collateral_info, requested_amount)` - Evaluates loan eligibility
- `calculate_interest_rate(customer_data)` - Computes personalized interest rates
- `generate_loan_offer(customer_id, collateral_json, requested_amount)` - Main orchestration function

### Assessment Functions
- `calculate_loan_details(loan_amount, interest_rate, tenure_years)` - EMI and payment calculations
- `generate_ai_loan_summary()` - AI-powered loan recommendations
- `display_loan_offer()` - Formatted output display

### Communication Functions
- `send_loan_offer_email()` - Logic Apps integration for email
- `format_loan_offer_email()` - HTML email formatting

## Interest Rate Calculation

### Base Rate: 8.5%

### Rate Adjustments
| Factor | Adjustment | Condition |
|--------|------------|-----------|
| Excellent Credit (750+) | -0.5% | Credit score ≥ 750 |
| Good Credit (650-749) | 0.0% | Credit score 650-749 |
| Fair Credit (600-649) | +0.5% | Credit score 600-649 |
| Existing Customer | -0.25% | Banking relationship exists |
| High Income | -0.25% | Monthly income > ₹100,000 |
| Stable Employment | -0.25% | Work experience ≥ 3 years |
| Low Risk Category | -0.25% | Customer risk = LOW |
| High Risk Category | +0.75% | Customer risk = HIGH |

### Minimum Rate: 7.0%

## Output Examples

### Console Output
```
🏦 GLOBAL TRUST BANK - HOME LOAN ASSESSMENT
================================================================================
📋 Customer ID: CUST0001
🏠 Property Value: ₹50,00,000
💰 Requested Amount: ₹40,00,000

🔍 Fetching customer data...
✅ Customer found: John Doe

🔍 Assessing loan eligibility...
✅ Customer is eligible for the requested loan amount

💹 Calculating personalized interest rate...

💰 LOAN OPTIONS:
────────────────────────────────────────────────────────────────────────────────
Tenure   Loan Amount     Interest Rate EMI             Total Payment
────────────────────────────────────────────────────────────────────────────────
15       ₹40,00,000           8.25%     ₹38,456        ₹69,22,080
20       ₹40,00,000           8.25%     ₹33,729        ₹80,95,040
25       ₹40,00,000           8.25%     ₹31,089        ₹93,26,700
30       ₹40,00,000           8.25%     ₹29,456        ₹1,06,04,160
```

### Email Output
The system generates professional HTML emails with:
- Customer and property details
- Loan options table
- AI-generated loan officer summary
- Next steps and contact information
- 30-day offer validity

## Error Handling

### Common Issues
1. **Database Connection Failures**
   - Firewall restrictions
   - Invalid credentials
   - Network connectivity

2. **Missing Customer Data**
   - Invalid customer ID
   - Incomplete records

3. **Eligibility Issues**
   - Low credit score
   - Insufficient income
   - High risk category

### Troubleshooting
- Check Azure SQL firewall settings
- Verify ODBC driver installation
- Validate customer data completeness
- Ensure Logic Apps endpoint availability

## Security Considerations

### Data Protection
- Encrypted database connections
- Secure credential management
- Azure AD authentication
- HTTPS communication for APIs

### Compliance
- Banking regulation compliance
- Data privacy protection
- Audit trail maintenance
- Secure document handling

## Integration Points

### Azure Services
- **Azure SQL Database**: Customer and loan data
- **Azure AI Projects**: Intelligent loan summaries
- **Logic Apps**: Email automation
- **Azure Identity**: Authentication

### External Systems
- Bank core systems
- Document management
- Credit scoring agencies
- Property valuation services

## Monitoring and Logging

### Logging Features
- Database connection status
- Eligibility assessment results
- Interest rate calculations
- Email delivery status
- Error tracking and reporting

### Performance Metrics
- Response time monitoring
- Success/failure rates
- Customer satisfaction tracking
- Loan approval statistics

## Future Enhancements

### Planned Features
- Multi-loan type support (personal, car, business)
- Advanced risk modeling
- Real-time property valuation integration
- Mobile app integration
- Blockchain-based document verification

### Scalability
- Microservices architecture
- Container deployment
- Load balancing
- Auto-scaling capabilities

## Support and Maintenance

### Contact Information
- **Development Team**: AI Solutions Team
- **Database Admin**: DBA Team
- **Infrastructure**: Cloud Operations

### Maintenance Schedule
- Weekly database health checks
- Monthly AI model updates
- Quarterly security reviews
- Annual system upgrades

## License
Proprietary software of Global Trust Bank. All rights reserved.

## Version History
- **v1.0.0** - Initial release with basic loan assessment
- **v1.1.0** - Added AI-powered summaries
- **v1.2.0** - Enhanced email automation
- **v1.3.0** - Improved risk assessment algorithms

---

*Last Updated: June 2025*
*Global Trust Bank - Digital Innovation Team*
