# Global Trust Bank CRM System

A comprehensive Customer Relationship Management (CRM) system for Global Trust Bank, featuring both frontend web interface and backend automation capabilities.

## 🏦 Project Overview

This project consists of two main components:

1. **Frontend**: A Flask-based web application for bank CRM management
2. **Backend**: An AI-powered automation system using Azure OpenAI and browser automation

## 📁 Project Structure

```
CUA/
├── Frontend/
│   ├── app.py                    # Main Flask application
│   ├── static/
│   │   └── style.css            # Custom CSS styles
│   └── templates/
│       ├── base.html            # Base template
│       ├── login.html           # Login page
│       ├── dashboard.html       # Main dashboard
│       ├── customers.html       # Customer list view
│       ├── customer_detail.html # Individual customer details
│       ├── add_customer.html    # Add new customer form
│       ├── loans.html           # Loan management
│       └── transactions.html    # Transaction history
├── Backend - CUA/
│   └── globaltrustbank_cau.py   # AI automation backend
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🚀 Features

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
   Copy the `.env` file and update it with your actual credentials:
   ```bash
   # The .env file is already provided with default settings
   # Update the following key variables:
   # - AZURE_OPENAI_API_KEY: Your Azure OpenAI API key
   # - AZURE_OPENAI_ENDPOINT: Your Azure OpenAI endpoint
   # - FLASK_SECRET_KEY: A secure secret key for Flask sessions
   # - ADMIN_USERNAME/ADMIN_PASSWORD: Change default login credentials
   ```

## 🏃‍♂️ Running the Application

### Frontend (Web CRM)
```bash
cd Frontend
python app.py
```
Access the application at: `http://localhost:5000`

**Default Login Credentials:**
- Username: Set in `.env` file (`ADMIN_USERNAME`)
- Password: Set in `.env` file (`ADMIN_PASSWORD`)
- Default: admin/admin123 (change these in production!)

### Backend (Automation)
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
- **Environment Variables**: Configure settings in `.env` file
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

### Available APIs
- `GET /api/customers` - Retrieve all customers
- `GET /api/transactions` - Retrieve all transactions
- All endpoints require authentication

## 🚀 Deployment

### Development
```bash
python app.py
```

