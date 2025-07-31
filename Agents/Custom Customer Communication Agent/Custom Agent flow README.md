# Custom Agent Files Documentation

This documentation covers the five core files that make up the Custom Agent system for loan processing and customer communication.

> **Note**: For detailed documentation on the main agent runner, see [Custom Template Agent README](Custom%20Template%20Agent%20README.md)

## 📁 File Overview

| File Name | Purpose | Key Functionality |
|-----------|---------|------------------|
| `custom_agent_functions.py` | Core business logic functions | API calls, loan processing, email sending |
| `custom_agent_tools.py` | Tool definitions for AI agent | Schema definitions, parameter validation |
| `agent.py` | Main agent runner | Agent initialization, conversation handling |
| `email_templates.py` | Email template management | HTML templates, stage mapping |
| `template_config.py` | Configuration and metadata | Stage definitions, utilities |

---

## 1. 📄 custom_agent_functions.py

**Purpose**: Contains all the business logic functions that can be called by the AI agent to perform specific operations.

### Key Functions:

#### 1.1 `submit_loan_application()`
- **Input**: `applicant_name`, `loan_amount`, `loan_type`, `credit_score`, `contact_email`
- **Output**: Dictionary with application ID and status
- **Example**:
  ```python
  # Input
  submit_loan_application(
      applicant_name="John Smith",
      loan_amount=50000.0,
      loan_type="personal",
      credit_score=720,
      contact_email="john@email.com"
  )
  
  # Output
  {
      "status": "submitted",
      "application_id": "APP12345678",
      "message": "Application submitted successfully"
  }
  ```

#### 1.2 `check_loan_status()`
- **Input**: `application_id`, `applicant_name`
- **Output**: Dictionary with current status and next steps
- **Example**:
  ```python
  # Input
  check_loan_status("APP12345678", "John Smith")
  
  # Output
  {
      "status": "under_review",
      "application_id": "APP12345678",
      "next_steps": "Please submit required documents",
      "estimated_completion": "3-5 business days"
  }
  ```

#### 1.3 `send_email_template()`
- **Input**: `customer_id`, `stage`
- **Output**: Dictionary with email send status
- **Example**:
  ```python
  # Input
  send_email_template("CUST0001", "3")
  
  # Output
  {
      "status": "submitted",
      "customer_id": "CUST0001",
      "stage": "3",
      "template_name": "verification",
      "message": "Thank you for using Global Trust Bank services"
  }
  ```

#### Other Functions:
- `trigger_logic_app_workflow()` - Triggers custom workflows
- `reduce_interest_rate()` - Processes rate reduction requests
- `trigger_campaign()` / `trigger_contest()` - Marketing functions
- `send_mail()` - Basic email sending function

---

## 2. 🛠️ custom_agent_tools.py

**Purpose**: Defines tool schemas that the AI agent uses to understand how to call functions.

### Key Tool Creators:

#### 2.1 `create_submit_loan_application_tool()`
- **Returns**: Tool definition with parameter schema
- **Schema**: Defines required fields (name, amount, type, credit score, email)
- **Example**:
  ```json
  {
      "type": "function",
      "function": {
          "name": "submit_loan_application",
          "description": "Submit a new loan application...",
          "parameters": {
              "type": "object",
              "properties": {
                  "applicant_name": {"type": "string"},
                  "loan_amount": {"type": "number"},
                  "loan_type": {"type": "string"},
                  "credit_score": {"type": "integer"},
                  "contact_email": {"type": "string"}
              },
              "required": ["applicant_name", "loan_amount", "loan_type", "credit_score", "contact_email"]
          }
      }
  }
  ```

#### 2.2 `create_send_email_template_tool()`
- **Returns**: Tool definition for email template sending
- **Schema**: Requires customer_id and stage
- **Example**:
  ```json
  {
      "type": "function",
      "function": {
          "name": "send_email_template",
          "description": "Send templated email for loan process stages...",
          "parameters": {
              "type": "object",
              "properties": {
                  "customer_id": {"type": "string"},
                  "stage": {"type": "string"}
              },
              "required": ["customer_id", "stage"]
          }
      }
  }
  ```

#### 2.3 `get_all_custom_agent_tools()`
- **Returns**: List of all available tool definitions
- **Usage**: Called by the agent to register all available tools

---

## 3. 🤖 custom_template_agent.py

**Purpose**: Main agent runner that handles conversations and orchestrates tool usage.

> **📖 For detailed documentation on this file, see [Custom Template Agent README](Custom%20Template%20Agent%20README.md)**

### Quick Overview:
- **Agent Initialization**: Connects to Azure AI services
- **Conversation Management**: Handles user interactions
- **Tool Execution**: Orchestrates function calls
- **Response Handling**: Manages agent responses

### Example Usage:
```bash
python agent.py
```

### Key Features:
- Real-time conversation handling
- Tool call orchestration
- Debug output for troubleshooting
- Memory management for customer context

---

## 4. 📧 email_templates.py

**Purpose**: Manages all email templates used for different loan process stages.

### Key Functions:

#### 4.1 `get_email_templates()`
- **Returns**: Dictionary of all available email templates
- **Structure**: Each template has subject, description, and HTML body
- **Example**:
  ```python
  {
      "application": {
          "subject": "Your Home Loan Application Has Been Submitted – Welcome to Global Trust Bank",
          "description": "Welcome email confirming successful application submission",
          "body": "<!DOCTYPE html>..." # Full HTML content
      },
      "verification": {
          "subject": "Document Verification in Progress – Global Trust Bank",
          "description": "Verification status update with timeline",
          "body": "<!DOCTYPE html>..." # Full HTML content
      }
  }
  ```

#### 4.2 `map_stage_to_template()`
- **Input**: Stage identifier (number or name)
- **Output**: Template name
- **Example**:
  ```python
  # Input variations
  map_stage_to_template("1") → "application"
  map_stage_to_template("3") → "verification"
  map_stage_to_template("application") → "application"
  map_stage_to_template("verification") → "verification"
  ```

#### 4.3 `get_stage_mapping()`
- **Returns**: Dictionary mapping various stage inputs to template names
- **Supports**: Numbers, names, and alternative formats

### Available Templates:
1. **application** - Welcome and confirmation
2. **document_submission** - Document upload instructions
3. **verification** - Verification in progress
4. **document_approval** - Documents approved
5. **approval** - Loan approved
6. **loan_letter** - Loan letter ready

---

## 5. ⚙️ template_config.py

**Purpose**: Provides configuration, metadata, and utility functions for template management.

### Key Components:

#### 5.1 Configuration Constants
```python
STAGE_MAPPING = {
    1: "application",
    2: "document_submission",
    3: "verification",
    4: "document_approval",
    5: "approval",
    6: "loan_letter"
}

STAGE_DESCRIPTIONS = {
    "application": {
        "stage_number": 1,
        "name": "Application Submission",
        "description": "Initial application submission confirmation",
        "primary_color": "#2c5530",
        "icon": "🏠"
    }
    # ... more stages
}
```

#### 5.2 Utility Functions

##### `get_stage_by_number()`
- **Input**: Stage number (1-6)
- **Output**: Stage name
- **Example**: `get_stage_by_number(3)` → `"verification"`

##### `get_stage_info()`
- **Input**: Stage name
- **Output**: Complete stage information dictionary
- **Example**:
  ```python
  get_stage_info("verification")
  # Returns:
  {
      "stage_number": 3,
      "name": "Document Verification",
      "description": "Document verification in progress",
      "key_features": ["Status updates", "Timeline information"],
      "primary_color": "#8b4513",
      "icon": "🔍"
  }
  ```

##### `validate_stage()`
- **Input**: Stage name
- **Output**: Boolean (True if valid)
- **Example**: `validate_stage("verification")` → `True`

##### `get_stage_progress_percentage()`
- **Input**: Stage name
- **Output**: Progress percentage (0-100)
- **Example**: `get_stage_progress_percentage("verification")` → `50.0`

---

## 🔄 File Interactions

### Flow Diagram:
```
custom_template_agent.py
    ↓ (imports)
custom_agent_tools.py → custom_agent_functions.py
    ↓ (uses)            ↓ (calls)
email_templates.py ← template_config.py
```

### Example Complete Flow:
1. **User Input**: "Send stage 3 email to CUST0001"
2. **Agent Processing**: Identifies need for email template tool
3. **Tool Definition**: `custom_agent_tools.py` provides schema
4. **Function Execution**: `custom_agent_functions.py` calls `send_email_template()`
5. **Template Mapping**: `email_templates.py` maps "3" to "verification"
6. **Configuration**: `template_config.py` provides metadata
7. **Result**: Verification email sent via Logic App

---

## 🚀 Quick Start Usage

### Running the Agent:
```python
python custom_template_agent.py
```

### Example Interactions:
```
User: "My customer ID is CUST0001 and I'm at stage 3"
Agent: 📧 Sending email template 'verification' for customer CUST0001...
Output: Thank you for using Global Trust Bank services you will be notified via mail

User: "I need to submit a loan application"
Agent: I'll help you submit a loan application. Please provide:
       - Your full name
       - Loan amount requested
       - Type of loan (mortgage, personal, auto, education)
       - Your credit score
       - Contact email
```

---

## 📋 Requirements

### Python Packages:
```
azure-ai-projects~=1.0.0b7
azure-identity
requests
```

### Environment Setup:
- Azure AI Project credentials
- Logic App endpoints configured
- Agent ID and connection string

---

## 🔧 Customization

### Adding New Templates:
1. Add template to `email_templates.py` in `get_email_templates()`
2. Update stage mapping in `template_config.py`
3. Add configuration in `STAGE_DESCRIPTIONS`

### Adding New Functions:
1. Create function in `custom_agent_functions.py`
2. Create tool definition in `custom_agent_tools.py`
3. Add tool to `get_all_custom_agent_tools()`
4. Update agent handler in `custom_template_agent.py`

### Modifying Agent Behavior:
- Edit system instructions in `custom_template_agent.py`
- Adjust tool descriptions in `custom_agent_tools.py`
- Update response handling in conversation loop

---

## 📊 Summary

These five files work together to create a comprehensive AI agent system for loan processing and customer communication:

- **Functions** (`custom_agent_functions.py`): The "what" - actual operations
- **Tools** (`custom_agent_tools.py`): The "how" - parameter definitions
- **Agent** (`custom_template_agent.py`): The "orchestrator" - conversation management
- **Templates** (`email_templates.py`): The "content" - email templates
- **Config** (`template_config.py`): The "rules" - configuration and metadata

Each file has a specific role, and together they provide a complete solution for automated customer communication in loan processing workflows.
