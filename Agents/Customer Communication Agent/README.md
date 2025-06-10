# Customer Communication Agent

A sophisticated AI-powered customer service agent built with Azure AI Projects that handles loan applications, customer communications, and various banking operations through natural language interactions.

## 🚀 Features

### Core Banking Operations
- **Loan Applications**: Submit new loan applications with automatic validation
- **Application Status Tracking**: Check the status of existing loan applications
- **Interest Rate Reduction**: Process requests for loan interest rate reductions
- **Customer Communication**: Send automated emails for loan process stage updates

### Marketing & Engagement
- **Campaign Management**: Trigger marketing campaigns with custom email content
- **Contest Management**: Launch and manage customer contests
- **Workflow Automation**: Integration with Azure Logic Apps for complex business processes

### Loan Process Stage Management
The agent supports 6 distinct loan process stages:
1. **Application** (Stage 1) - Initial loan application submission
2. **Document Submission** (Stage 2) - Required document upload
3. **Verification** (Stage 3) - Document and information verification
4. **Document Approval** (Stage 4) - Document approval with condition tracking
5. **Approval** (Stage 5) - Final loan approval
6. **Loan Letter** (Stage 6) - Loan letter generation and delivery

### Smart Customer Memory
- Remembers customer ID throughout the conversation
- No need to re-enter customer information for subsequent requests
- Maintains context across multiple interactions

## 📋 Prerequisites

- Python 3.8 or higher
- Azure subscription with AI Projects enabled
- Azure Logic Apps endpoints configured
- Valid Azure credentials

## 🛠️ Installation

1. **Clone or download the project files**
   ```bash
   git clone <repository-url>
   cd Customer Communication Agent
   ```

2. **Install required dependencies**
   ```bash
   pip install azure-ai-projects~=1.0.0b7
   pip install requests
   pip install azure-identity
   ```

3. **Configure Azure credentials**
   - Ensure your Azure credentials are properly configured
   - Update the connection string in `agent.py` with your Azure AI Project details

## 📁 Project Structure

```
Customer Communication Agent/
│
├── agent.py                    # Main agent application
├── agent_backup.py            # Backup of agent configuration
├── agent_fixed.py             # Updated agent with enhanced features
├── custom_agent_tools.py      # Tool definitions and schemas
├── custom_agent_functions.py  # Implementation of agent functions
├── __pycache__/               # Python cache files
└── README.md                  # This file
```

## 🔧 Configuration

### Azure AI Projects Setup
1. Update the connection string in `agent.py`:
   ```python
   project_client = AIProjectClient.from_connection_string(
       credential=DefaultAzureCredential(),
       conn_str="your-connection-string-here"
   )
   ```

2. Update the agent ID:
   ```python
   agent = project_client.agents.get_agent("your-agent-id-here")
   ```

### Logic Apps Integration
Update the API endpoints in `custom_agent_functions.py` to point to your Logic Apps:
```python
api_url = "https://your-logic-app-url.azurewebsites.net/..."
```

## 🚀 Usage

### Starting the Agent
```bash
python agent.py
```

### Example Interactions

#### Loan Application
```
User: I want to apply for a personal loan
Agent: I'd be happy to help you apply for a personal loan. Let me collect the required information...
```

#### Stage Communication
```
User: My customer ID is CUST123 and I'm in stage 4
Agent: Thank you! I have your customer ID as CUST123. For Stage 4 (document_approval), I need one more piece of information.
       Is the document approval condition met? Please answer with 'true' or 'false'.
```

#### Status Check
```
User: Check status for application APP12345
Agent: I'll check the status of application APP12345. Could you please provide your name for verification?
```

## 🔧 Available Tools

### 1. Submit Loan Application
- **Purpose**: Submit new loan applications
- **Required**: applicant_name, loan_amount, loan_type, credit_score, contact_email
- **Supported Loan Types**: mortgage, personal, auto, education, business, other

### 2. Check Loan Status
- **Purpose**: Check existing application status
- **Required**: application_id, applicant_name

### 3. Send Mail (Stage Communication)
- **Purpose**: Send customer communication emails
- **Required**: customer_id, stage
- **Special**: Stage 4 requires additional 'condition' parameter (true/false)

### 4. Interest Rate Reduction
- **Purpose**: Process interest rate reduction requests
- **Required**: customer_id, loan_id, credit_score

### 5. Campaign Management
- **Purpose**: Trigger marketing campaigns
- **Required**: subject, body

### 6. Contest Management
- **Purpose**: Launch customer contests
- **Required**: subject, body

### 7. Logic App Workflow Trigger
- **Purpose**: Trigger custom Azure Logic App workflows
- **Supported**: loan_approval, account_creation, document_processing

## 🎯 Key Features

### Intelligent Stage Handling
- Automatically validates stage requirements
- Special handling for Stage 4 (document_approval) with condition parameter
- Clear stage progression tracking

### Customer Memory
- Remembers customer ID once provided
- Eliminates repetitive information requests
- Maintains conversation context

### Error Handling
- Comprehensive error handling for API calls
- User-friendly error messages
- Graceful degradation for failed operations

### Validation
- Input validation for all parameters
- Credit score range validation (300-850)
- Email format validation
- Enum validation for loan types and stages

## 🔍 Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify Azure credentials are properly configured
   - Check connection string format
   - Ensure network connectivity to Azure services

2. **Logic App Failures**
   - Verify Logic App endpoints are accessible
   - Check API permissions and authentication
   - Validate JSON payload format

3. **Agent Not Responding**
   - Check agent ID is correct
   - Verify Azure AI Projects service status
   - Review error logs for specific issues

### Debug Mode
Enable debug logging by adding:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 API Documentation

### Function Signatures

```python
# Loan Operations
submit_loan_application(applicant_name, loan_amount, loan_type, credit_score, contact_email)
check_loan_status(application_id, applicant_name)
reduce_interest_rate(customer_id, loan_id, credit_score)

# Communication
send_mail(customer_id, stage, condition=None)

# Marketing
trigger_campaign(intent, subject, body)
trigger_contest(intent, subject, body)

# Workflow
trigger_logic_app_workflow(workflow_name, input_data)
```

## 🔐 Security Considerations

- All API calls use HTTPS encryption
- Customer data is validated before processing
- Azure credentials are managed securely
- No sensitive information is logged

## 🚀 Future Enhancements

- [ ] Multi-language support
- [ ] Advanced analytics and reporting
- [ ] Integration with additional banking systems
- [ ] Enhanced customer authentication
- [ ] Real-time notification system
- [ ] Mobile app integration

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create an issue in the repository
- Contact the development team
- Review the troubleshooting section

## 🏗️ Architecture

The application follows a modular architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   agent.py      │    │ custom_agent_   │    │ Azure Logic     │
│   (Main App)    │───▶│ functions.py    │───▶│ Apps            │
│                 │    │ (Functions)     │    │ (Backend)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│ custom_agent_   │    │ Azure AI        │
│ tools.py        │    │ Projects        │
│ (Tool Schemas)  │    │ (AI Service)    │
└─────────────────┘    └─────────────────┘
```

## 📊 Performance

- Average response time: < 2 seconds
- Supports concurrent users
- Scalable with Azure infrastructure
- Built-in retry mechanisms for reliability

---

**Version**: 1.0.0  
**Last Updated**: June 2025  
**Developed by**: Customer Service Team
