# Global Trust Bank CRM System

A comprehensive Customer Relationship Management (CRM) system for Global Trust Bank, featuring both frontend web interface and backend automation capabilities.

## 🏦 Project Overview

This project consists of four main components:

1. **Main CUA Application**: A Flask-based API service for customer lookup automation (`app.py`)
2. **CRM-UI**: A comprehensive web application for bank CRM management
3. **Frontend - CUA**: UI assets for the customer lookup interface
4. **Backend**: An AI-powered automation system using Azure OpenAI and browser automation

## 📁 Project Structure

```
CUA/
├── app.py                       # Main CUA application - Customer lookup API service
├── CRM-UI/
│   ├── app.py                   # CRM web application - Full bank management system
│   ├── static/
│   │   └── style.css           # Custom CSS styles for CRM
│   └── templates/
│       ├── base.html           # Base template
│       ├── dashboard.html      # Main CRM dashboard
│       ├── customers.html      # Customer list view
│       ├── customer_detail.html # Individual customer details
│       ├── add_customer.html   # Add new customer form
│       ├── loans.html          # Loan management
│       └── transactions.html   # Transaction history
├── Frontend - CUA/
│   ├── static/                 # Frontend assets for CUA lookup interface
│   │   ├── script.js           # JavaScript for customer lookup
│   │   └── styles.css          # CSS for lookup interface
│   └── templates/              # Templates for CUA interface
│       └── index.html          # Customer lookup form
├── Backend - CUA/
│   ├── globaltrustbank_cau.py  # AI automation backend
│   └── instrctions.txt         # Backend instructions
├── .env.example                # Environment configuration template
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## � Application Workflow

### Customer Lookup Process
1. **Frontend Interface**: User accesses the customer lookup form via `Frontend - CUA/templates/index.html`
2. **Main API Service**: `app.py` receives lookup requests and manages sessions
3. **Backend Automation**: AI agent in `Backend - CUA/` performs automated lookups
4. **Results Processing**: CRM reference numbers are extracted and returned to the user

### CRM Management Process
1. **CRM Interface**: Bank staff access the full CRM system via `CRM-UI/app.py`
2. **Customer Management**: Complete customer profiles, accounts, and transaction management
3. **Data Integration**: Sample data includes customer information with CRM references

## �🚀 Features

### Main CUA Application Features (`app.py`)
- **Customer Lookup API**: RESTful API for customer information retrieval
- **Agent Integration**: Interfaces with AI automation backend
- **Session Management**: Handles lookup sessions and status tracking
- **Real-time Status Updates**: Provides live updates during lookup process
- **CRM Reference Extraction**: Extracts and returns CRM reference numbers

### CRM Web Application Features (`CRM-UI/app.py`)
- **Customer Management**: View, add, and manage customer profiles
- **Account Management**: Track account balances, types, and status
- **Loan Management**: Monitor active loans, EMIs, and payment schedules
- **Transaction History**: Complete transaction tracking with references
- **Dashboard Analytics**: Visual overview of bank operations
- **Secure Authentication**: Login system with session management
- **Responsive Design**: Bootstrap-based UI for all devices

### Frontend Features
- **Customer Management**: View, add, and manage customer profiles
- **Account Management**: Track account balances, types, and status
- **Loan Management**: Monitor active loans, EMIs, and payment schedules
- **Transaction History**: Complete transaction tracking with references
- **Dashboard Analytics**: Visual overview of bank operations
- **Secure Authentication**: Login system with session management
- **Responsive Design**: Bootstrap-based UI for all devices

### Backend Features
- **AI Automation**: Azure OpenAI integration for intelligent processing
- **Browser Automation**: Playwright-based web automation
- **Computer Vision**: Screenshot analysis and processing
- **Environment Management**: Secure configuration handling

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Web browser (for frontend access)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CUA
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers** (for backend automation)
   ```bash
   playwright install
   ```

4. **Environment Configuration**
   Create your environment file from the template:
   ```bash
   # Copy the template file
   copy .env.example .env
   
   # Edit the .env file with your actual credentials:
   # - AZURE_OPENAI_API_KEY: Your Azure OpenAI API key
   # - AZURE_OPENAI_ENDPOINT: Your Azure OpenAI endpoint
   # - FLASK_SECRET_KEY: A secure secret key for Flask sessions
   # - ADMIN_USERNAME/ADMIN_PASSWORD: Change default login credentials
   ```

## 🏃‍♂️ Running the Applications

### Main CUA Application (Customer Lookup API)
```bash
python app.py
```
Access the API service at: `http://localhost:8080`

This service provides:
- Customer lookup functionality
- Integration with AI automation backend
- RESTful API endpoints for customer information retrieval

### CRM-UI (Full Bank Management System)
```bash
cd CRM-UI
python app.py
```
Access the web application at: `http://localhost:5000`

**Default Login Credentials:**
- Username: Set in `.env` file (`ADMIN_USERNAME`)
- Password: Set in `.env` file (`ADMIN_PASSWORD`)
- Default: admin/admin123 (change these in production!)

### Backend Automation
```bash
cd "Backend - CUA"
python globaltrustbank_cau.py
```

## 💾 Sample Data

The application comes pre-loaded with sample data including:

### Customers
- 6 sample customers with complete profiles
- Account numbers: GTB001 - GTB006
- Various account types: Savings, Current, Premium
- Indian customer profiles with PAN/Aadhar details

### Transactions
- Sample transaction history
- Various transaction types: Credit, Debit, EMI
- Complete reference and UTR numbers

### Loans
- Active home and car loans
- EMI tracking and payment schedules
- Loan reference numbers and sanction details

## 🔧 Configuration

### Frontend Configuration
- **Environment Variables**: Configure settings in `.env` file (copy from `.env.example`)
- **Secret Key**: Set `FLASK_SECRET_KEY` in `.env` for production security
- **Debug Mode**: Set `FLASK_DEBUG=False` for production deployment
- **Host/Port**: Configure `FLASK_HOST` and `FLASK_PORT` as needed
- **Authentication**: Update `ADMIN_USERNAME` and `ADMIN_PASSWORD`

### Backend Configuration
- **Azure OpenAI**: Configure API credentials in `.env` file
- **Browser Settings**: Adjust Playwright configurations via environment variables
- **Screenshot Settings**: Modify `SCREENSHOT_WIDTH` and `SCREENSHOT_HEIGHT`
- **Logging**: Configure log levels and file paths

## 🎨 Customization

### Adding New Features
1. **New Routes**: Add routes in `app.py`
2. **Templates**: Create HTML templates in `templates/` directory
3. **Styling**: Modify `static/style.css` for custom styles
4. **Data Models**: Extend existing data structures in `app.py`

### UI Customization
- Bootstrap 5.1.3 framework
- Font Awesome 6.0.0 icons
- Custom CSS in `static/style.css`
- Responsive design for mobile and desktop

## 🔒 Security Considerations

- **Environment Variables**: Never commit `.env` file to version control
- **Credentials**: Change all default passwords and API keys
- **Secret Keys**: Use strong, unique secret keys for Flask sessions
- **HTTPS**: Enable SSL in production (configure in `.env`)
- **Input Validation**: Implement proper form validation
- **CSRF Protection**: Enable CSRF protection (`WTF_CSRF_ENABLED=True`)
- **Rate Limiting**: Configure API rate limits in `.env`
- **Logging**: Monitor application logs for security events

## 📊 API Endpoints

### Main CUA Application APIs (`app.py`)
- `POST /api/start-lookup` - Start customer lookup process
  - Parameters: `customer_id`, `username`, `password`
  - Returns: `session_id` for tracking progress
- `GET /api/status/<session_id>` - Get lookup status and results
  - Returns: Status updates or final CRM reference number

### CRM-UI Application APIs (`CRM-UI/app.py`)
- `GET /api/customers` - Retrieve all customers
- `GET /api/transactions` - Retrieve all transactions
- All endpoints require authentication
- `GET /api/transactions` - Retrieve all transactions
- All endpoints require authentication

## 🚀 Deployment

### Development
```bash
python app.py
```

