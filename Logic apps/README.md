# Banking AI Agent with Azure Logic Apps Integration

A sophisticated AI-powered banking assistant that leverages Azure AI Projects and Logic Apps to provide comprehensive loan services, including application submission, status checking, workflow triggering, and interest rate reduction requests.

## 🏛️ Overview

This project creates an intelligent banking agent that can handle various loan-related tasks through natural conversation. The agent integrates with Azure Logic Apps to process requests and provides standardized responses to maintain a professional banking experience.

## ✨ Features

### Core Banking Services
- **🏠 Loan Application Submission**: Submit new loan applications for mortgages, personal loans, auto loans, education loans, and business loans
- **📊 Loan Status Checking**: Check the current status of existing loan applications
- **⚙️ Workflow Triggering**: Trigger various banking workflows including loan approval, account creation, and document processing
- **📉 Interest Rate Reduction**: Request interest rate reductions on existing loans with credit score-based eligibility assessment

### Agent Capabilities
- **💬 Natural Language Processing**: Understand customer requests through conversational AI
- **🔧 Smart Tool Selection**: Automatically determine which tools to use based on customer needs
- **📋 Required Information Collection**: Intelligently gather all necessary information before processing requests
- **🎯 Professional Banking Experience**: Provide standardized responses consistent with banking protocols

## 🏗️ Architecture

### File Structure
```
agent logic apps/
├── README.md                           # This documentation file
├── loan_application_agent_demo.py      # Main demo application with full agent functionality
├── custom_agent_functions.py           # Core function implementations for banking operations
├── custom_agent_tools.py              # Tool definitions and schemas for the AI agent
├── config.py                          # Configuration settings
├── interactive_agent.py               # Basic conversation agent without tools
├── enhanced_agent_chatbot.py          # Enhanced agent with basic tool integration
├── user_functions.py                  # Original interest rate reduction function
└── agent_tools.py                     # Original tool definitions
```

### Component Overview

#### Main Application (`loan_application_agent_demo.py`)
- **Purpose**: Primary interactive banking agent with full Azure Logic Apps integration
- **Features**: Complete tool functionality, conversation management, error handling
- **Usage**: Run this file for the full banking agent experience

#### Core Functions (`custom_agent_functions.py`)
- **Purpose**: Implementation of all banking operations that integrate with Logic Apps
- **Functions**:
  - `submit_loan_application()`: Process new loan applications
  - `check_loan_status()`: Retrieve application status information
  - `trigger_logic_app_workflow()`: Execute specific banking workflows
  - `reduce_interest_rate()`: Handle interest rate reduction requests

#### Tool Definitions (`custom_agent_tools.py`)
- **Purpose**: Define tool schemas and parameters for the AI agent
- **Features**: JSON schema definitions, parameter validation, usage instructions

## 🚀 Getting Started

### Prerequisites

#### Required Python Packages
```bash
pip install azure-ai-projects~=1.0.0b7
pip install azure-identity
pip install requests
```

#### Azure Resources
- **Azure AI Projects**: Configured with appropriate connection string
- **Azure Logic Apps**: Set up with HTTP trigger endpoints
- **Azure Credentials**: DefaultAzureCredential configured for authentication

### Installation

1. **Clone or Download** the project files to your local machine

2. **Install Dependencies**:
   ```bash
   pip install azure-ai-projects~=1.0.0b7 azure-identity requests
   ```

3. **Configure Azure Connection**:
   - Update the connection string in `loan_application_agent_demo.py`:
   ```python
   conn_str="YOUR_AZURE_AI_PROJECT_CONNECTION_STRING"
   ```

4. **Update Agent ID**:
   - Replace the agent ID with your specific agent:
   ```python
   agent = project_client.agents.get_agent("YOUR_AGENT_ID")
   ```

5. **Configure Logic App URLs**:
   - Update the Logic App URLs in `custom_agent_functions.py` with your endpoints

### Running the Application

#### Main Banking Agent
```bash
python loan_application_agent_demo.py
```

This starts the interactive banking agent with full functionality.

#### Basic Conversation Agent
```bash
python interactive_agent.py
```

This provides a simple conversational experience without tools.

## 🛠️ Usage Guide

### Available Commands and Interactions

#### 1. Loan Application Submission
**User Intent**: "I want to apply for a loan"

**Required Information**:
- Applicant name (full name)
- Loan amount (in dollars)
- Loan type (mortgage, personal, auto, education, business, other)
- Credit score (300-850)
- Contact email

**Example Interaction**:
```
👤 You: I want to apply for a personal loan
🤖 Agent: I'd be happy to help you apply for a personal loan. Let me collect the required information...
👤 You: John Smith, $25000, credit score 720, john.smith@email.com
🤖 Agent: Perfect! I'm submitting your personal loan application...
```

#### 2. Loan Status Checking
**User Intent**: "What's the status of my loan application?"

**Required Information**:
- Application ID
- Applicant name (for verification)

**Example Interaction**:
```
👤 You: Can you check the status of my loan application?
🤖 Agent: I can help you check your loan status. I'll need your application ID and name...
👤 You: My application ID is APP12345678 and my name is John Smith
🤖 Agent: Let me check the status of your application...
```

#### 3. Interest Rate Reduction
**User Intent**: "I want to reduce my interest rate" or "Can you lower my loan rate?"

**Required Information**:
- Customer ID
- Loan ID
- Current credit score

**Example Interaction**:
```
👤 You: I'd like to reduce the interest rate on my loan
🤖 Agent: I can help you request an interest rate reduction. I'll need some information...
👤 You: Customer ID is CUST789, loan ID is LOAN456, credit score is 780
🤖 Agent: Based on your excellent credit score, you have a high chance of approval...
```

#### 4. Workflow Triggering
**User Intent**: Various banking operations

**Available Workflows**:
- **loan_approval**: Process loan approval requests
- **account_creation**: Create new bank accounts
- **document_processing**: Process submitted documents

**Example Interaction**:
```
👤 You: I need to create a new savings account
🤖 Agent: I can help you with account creation. Let me gather the required information...
```

### Response Patterns

All banking operations return standardized messages:
> "Your [request type] has been submitted to Global Trust Bank. You will receive updates via your registered email ID."

This ensures a consistent professional banking experience across all interactions.

## 🔧 Configuration

### Azure AI Projects Configuration

```python
# Connection string format
conn_str = "eastus2.api.azureml.ms;PROJECT_ID;RESOURCE_GROUP;PROJECT_NAME"

# Initialize client
project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=conn_str
)
```

### Logic App Endpoints

Configure your Logic App URLs in `custom_agent_functions.py`:

```python
# Main Logic App endpoint
api_url = "https://YOUR_LOGIC_APP.azurewebsites.net:443/api/agent/triggers/..."

# Interest rate reduction endpoint
api_url = "https://YOUR_LOGIC_APP.azurewebsites.net:443/api/full_agent/triggers/..."
```

### Agent Instructions

The agent operates with specific instructions for tool usage:

- **Tool Selection**: Only use tools when user intent explicitly matches tool purpose
- **Information Collection**: Always gather all required parameters before using tools
- **Professional Communication**: Maintain banking-appropriate language and responses
- **Error Handling**: Provide helpful guidance when information is missing or invalid

## 🧪 Development and Testing

### Adding New Tools

1. **Create Function** in `custom_agent_functions.py`:
```python
def new_banking_function(param1: str, param2: int) -> Dict[str, Any]:
    """
    Description of the new banking function.
    """
    # Implementation here
    return {"status": "success", "message": "Operation completed"}
```

2. **Define Tool Schema** in `custom_agent_tools.py`:
```python
def create_new_banking_tool() -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "new_banking_function",
            "description": "Clear description for the agent",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "Parameter description"},
                    "param2": {"type": "integer", "description": "Parameter description"}
                },
                "required": ["param1", "param2"]
            }
        }
    }
```

3. **Add Tool to List** in `get_all_custom_agent_tools()` function

4. **Handle Tool Call** in main application's tool processing loop

### Testing Individual Components

#### Test Functions Directly
```python
from custom_agent_functions import submit_loan_application

result = submit_loan_application(
    applicant_name="Test User",
    loan_amount=50000,
    loan_type="personal",
    credit_score=720,
    contact_email="test@example.com"
)
print(result)
```

#### Test Agent Conversation
Run any of the main files and interact through the console interface.

## 🔒 Security Considerations

### Sensitive Information Handling
- **Credit Scores**: Validated within realistic ranges (300-850)
- **Email Addresses**: Format validation applied
- **Customer IDs**: Treated as sensitive identifiers
- **Application Data**: Not stored locally, immediately sent to Logic Apps

### Azure Security
- **Authentication**: Uses DefaultAzureCredential for secure Azure authentication
- **Connections**: All Logic App communications use HTTPS
- **Credentials**: No hardcoded secrets in the codebase

### Best Practices
- **Input Validation**: All user inputs are validated before processing
- **Error Handling**: Comprehensive error handling prevents information leakage
- **Logging**: Minimal logging to avoid exposing sensitive data

## 🚨 Troubleshooting

### Common Issues

#### "AttributeError: 'AgentsClient' object has no attribute 'submit_tool_outputs'"
**Solution**: Use `submit_tool_outputs_to_run` instead of `submit_tool_outputs`

#### Agent Not Responding
**Check**:
- Azure connection string is correct
- Agent ID exists and is accessible
- DefaultAzureCredential is properly configured

#### Logic App Integration Failures
**Check**:
- Logic App URLs are correct and accessible
- HTTP triggers are properly configured
- Request payload format matches Logic App expectations

#### Tool Not Being Called
**Verify**:
- Tool schema is correctly defined
- Required parameters are clearly specified
- Agent instructions include guidance for tool usage

### Debug Mode

Add debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 API Reference

### Function Signatures

#### submit_loan_application
```python
def submit_loan_application(
    applicant_name: str, 
    loan_amount: float, 
    loan_type: str, 
    credit_score: int, 
    contact_email: str
) -> Dict[str, Any]
```

#### check_loan_status
```python
def check_loan_status(
    application_id: str, 
    applicant_name: str
) -> Dict[str, Any]
```

#### trigger_logic_app_workflow
```python
def trigger_logic_app_workflow(
    workflow_name: str, 
    input_data: Dict[str, Any]
) -> Dict[str, Any]
```

#### reduce_interest_rate
```python
def reduce_interest_rate(
    customer_id: str, 
    loan_id: str, 
    credit_score: int
) -> Dict[str, Any]
```

### Return Value Format

All functions return dictionaries with consistent structure:

```python
{
    "status": "success|error|submitted",
    "message": "Human-readable status message",
    # Additional function-specific fields
}
```

## 🤝 Contributing

### Development Guidelines
1. **Follow Existing Patterns**: Maintain consistency with existing function and tool structures
2. **Add Documentation**: Include comprehensive docstrings for all new functions
3. **Test Thoroughly**: Verify both individual functions and full agent integration
4. **Update README**: Document any new features or configuration changes

### Code Style
- Use type hints for all function parameters and return values
- Follow PEP 8 style guidelines
- Include clear, descriptive variable names
- Add comments for complex logic

## 📄 License

This project is part of Microsoft Azure AI demonstrations. Please refer to your Azure subscription terms for usage rights and restrictions.

## 📞 Support

For technical support:
1. **Azure AI Issues**: Contact Azure Support through the Azure Portal
2. **Logic Apps Issues**: Use Azure Logic Apps documentation and support channels
3. **Code Issues**: Review troubleshooting section above

---

**Version**: 1.0  
**Last Updated**: January 2025  
**Azure AI Projects SDK**: ~1.0.0b7
