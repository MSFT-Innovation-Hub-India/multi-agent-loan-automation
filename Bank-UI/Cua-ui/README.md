# Global Trust Bank - Customer Lookup System

A web-based UI for the AI-powered customer lookup system that integrates with your existing agent.

## Features

- Modern, responsive web interface
- Step-by-step customer lookup process
- Real-time status updates during agent execution
- Automatic CRM reference extraction
- Professional banking theme with Global Trust Bank branding

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

### 3. Environment Setup

Make sure you have a `.env` file with your Azure OpenAI credentials (if needed).

### 4. Run the Application

#### Option A: Using the batch file (Windows)
```bash
run.bat
```

#### Option B: Direct Python execution
```bash
python app.py
```

### 5. Access the Web Interface

Open your browser and navigate to:
```
http://127.0.0.1:8080
```

## How to Use

1. **Enter Customer ID**: Input the customer ID you want to search for (e.g., CUST0001)
2. **Enter Credentials**: Provide your CRM system username and password
3. **Start Lookup**: The AI agent will automatically:
   - Navigate to the CRM system
   - Handle login
   - Search for the customer
   - Extract the CRM reference number
4. **View Results**: The CRM reference number will be displayed on the interface

## File Structure

```
├── app.py                 # Flask web server
├── agent_modified.py      # Modified agent for web integration
├── templates/
│   └── index.html        # Main web interface
├── static/
│   ├── styles.css        # CSS styling
│   └── script.js         # JavaScript functionality
├── requirements.txt      # Python dependencies
├── run.bat              # Windows startup script
└── README.md            # This file
```

## API Endpoints

- `GET /` - Serves the main web interface
- `POST /api/start-lookup` - Starts a customer lookup session
- `GET /api/status/<session_id>` - Polls for lookup status and results

## Browser Requirements

- Chrome/Chromium (required for Playwright automation)
- Modern browser with JavaScript enabled
- Internet connection for CRM system access

## Troubleshooting

1. **Import Errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`
2. **Browser Issues**: Install Playwright browsers with `playwright install chromium`
3. **Port Conflicts**: If port 5000 is in use, modify the port in `app.py`
4. **Agent Errors**: Check that your Azure OpenAI credentials are correctly configured
