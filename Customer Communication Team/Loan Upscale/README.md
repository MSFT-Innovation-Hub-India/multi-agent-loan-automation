# Global Trust Bank Voice Bot Backend

A voice-enabled sales bot for Global Trust Bank that provides loan upselling services through Azure OpenAI's Realtime API.

## Overview

This backend application powers a conversational AI voice bot that acts as a sales representative for Global Trust Bank. The bot congratulates customers on their approved loans and offers additional loan products with competitive interest rates.

## Features

- **Voice Interaction**: Real-time voice conversation using Azure OpenAI Realtime API
- **Sales Bot Behavior**: Automatically congratulates customers and upsells loan products
- **Indian Banking Context**: Uses Indian Rupees (₹) and India-specific banking terms
- **Azure Authentication**: Supports both API key and Azure credential authentication
- **Static File Serving**: Serves the frontend React application

## Technology Stack

- **Framework**: aiohttp (Python async web framework)
- **AI Service**: Azure OpenAI Realtime API
- **Authentication**: Azure Identity with support for API keys and credential-based auth
- **Configuration**: Environment variables via python-dotenv

## Prerequisites

- Python 3.8+
- Azure OpenAI account with Realtime API access
- Required Python packages (see requirements.txt)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env` file:
```env
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_REALTIME_DEPLOYMENT=your_deployment_name
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_REALTIME_VOICE_CHOICE=shimmer
```

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI service endpoint | `https://your-resource.openai.azure.com/` |
| `AZURE_OPENAI_REALTIME_DEPLOYMENT` | Deployment name for realtime model | `gpt-4o-realtime-preview` |
| `AZURE_OPENAI_API_KEY` | API key for authentication | `your-api-key` |
| `AZURE_OPENAI_REALTIME_VOICE_CHOICE` | Voice selection for responses | `shimmer`, `alloy`, `echo` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_TENANT_ID` | Azure tenant ID for credential auth | None |
| `RUNNING_IN_PRODUCTION` | Production mode flag | None |

## Running the Application

### Development Mode
```bash
python app.py
```

### Using Module Mode
```bash
python -m app
```

The application will start on `http://localhost:8765`

## Application Structure

### Main Components

- **`app.py`**: Main application entry point
- **`rtmt.py`**: RTMiddleTier integration for Azure OpenAI Realtime API
- **`static/`**: Frontend React application files
- **`.env`**: Environment configuration

### Key Features

#### Voice Bot Personality
The bot is configured as a Global Trust Bank sales representative with the following characteristics:
- Warmly greets customers
- Congratulates on recently approved loans
- Offers additional loan products at 8.5% per annum starting rate
- Provides loan details: ₹2 lakh to ₹50 lakh, 1-7 years tenure
- Emphasizes quick processing (24-48 hours) and minimal documentation

#### Authentication
Supports multiple authentication methods:
1. **API Key**: Direct authentication using `AZURE_OPENAI_API_KEY`
2. **Azure CLI Credentials**: Uses `AzureDeveloperCliCredential` with tenant ID
3. **Default Credentials**: Falls back to `DefaultAzureCredential`

#### Web Routes
- **`/`**: Serves the main frontend application
- **`/realtime`**: WebSocket endpoint for voice communication
- **Static files**: Serves frontend assets from `/static` directory

## API Endpoints

### WebSocket Endpoints

- **`/realtime`**: Real-time voice communication endpoint
  - Handles bidirectional audio streaming
  - Processes voice input and generates voice responses
  - Manages conversation state

### HTTP Endpoints

- **`GET /`**: Returns the main frontend HTML page
- **`GET /static/*`**: Serves static frontend assets

## Development

### Error Handling
- Graceful fallback for authentication methods
- Environment variable validation
- WebSocket connection management

## Deployment

### Local Deployment
```bash
python app.py
```

### Production Deployment
Set the `RUNNING_IN_PRODUCTION` environment variable to skip `.env` file loading:
```bash
export RUNNING_IN_PRODUCTION=true
python app.py
```

## Dependencies

```
aiohttp==3.9.3          # Async web framework
azure-identity==1.18.0  # Azure authentication
python-dotenv==1.0.1    # Environment variable management
gunicorn                # WSGI server for production
rich                    # Enhanced console output
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Errors**: Ensure Azure OpenAI endpoint is correctly formatted
2. **Authentication Failures**: Verify API key or Azure credentials
3. **Voice Issues**: Check voice choice configuration and audio permissions

### Logs
Monitor application logs for detailed error information:
```bash
python app.py
```

## License

This project is configured for Global Trust Bank's internal use.
