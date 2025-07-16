from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import uuid
import datetime
import json
import sys
import os
import requests
from azure.cosmos import CosmosClient, exceptions

# Add the parent directory to Python path to import the Underwriting agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Agent workflow order for guidance messages
AGENT_WORKFLOW_ORDER = [
    ('application_assist', 'Customer Service Agent', 'Loan Documentation Agent'),
    ('document_checker', 'Loan Documentation Agent', 'Credit Liability Agent'),
    ('pre_qualification', 'Credit Liability Agent', 'Credit Risk and Underwriting Agent'),
    ('Underwriting', 'Credit Risk and Underwriting Agent', 'Credit Appraisal Agent'),
    ('credit_assessor', 'Credit Appraisal Agent', 'Property Valuation Agent'),
    ('valuation', 'Property Valuation Agent', 'Audit Agent'),
    ('audit', 'Audit Agent', 'Customer Relationship Agent'),
    ('customer_communication', 'Customer Relationship Agent', 'Offer Generation Agent'),
    ('offer_generation', 'Offer Generation Agent', None)  # Last agent in workflow
]

# CosmosDB Configuration
COSMOS_URI = "https://globaltrustbank.documents.azure.com:443/"
COSMOS_KEY = "EPcG6JzbLnWUNyIGZRSvCLiAypzsU3GBqEO8E7ZlqKVwRLHXHKrkniFMKFfwCJc8qS3jfdlmJVhFACDb8bHG5Q=="
DATABASE_NAME = "LoanProcessingDB"
CONTAINER_NAME = "AgentLogs"

# Initialize Cosmos client
try:
    cosmos_client = CosmosClient(COSMOS_URI, COSMOS_KEY)
    cosmos_database = cosmos_client.get_database_client(DATABASE_NAME)
    cosmos_container = cosmos_database.get_container_client(CONTAINER_NAME)
    print("✅ CosmosDB connection established successfully")
except Exception as e:
    print(f"⚠️ Failed to connect to CosmosDB: {e}")
    cosmos_client = None
    cosmos_database = None
    cosmos_container = None

def normalize_agent_name(agent_name):
    """Normalize agent names from CosmosDB format to match the expected format"""
    # Handle the case where agent name might be in lowercase or different format
    if not agent_name:
        return agent_name
        
    agent_name_lower = agent_name.lower()
    
    if agent_name_lower == 'underwriting agent':
        return 'Underwriting agent'  # Keep lowercase to match CosmosDB
    elif agent_name_lower == 'pre-qualification agent':
        return 'Pre-Qualification Agent'
    elif agent_name_lower == 'document checker agent':
        return 'Document Checker Agent'
    elif agent_name_lower == 'application assist agent':
        return 'Application Assist Agent'
    elif agent_name_lower == 'valuation agent':
        return 'Valuation Agent'
    elif agent_name_lower == 'credit assessor agent':
        return 'Credit Assessor Agent'
    elif agent_name_lower == 'approval agent':
        return 'Approval Agent'
    elif agent_name_lower == 'offer generation agent':
        return 'Offer Generation Agent'
    elif agent_name_lower == 'customer communication agent':
        return 'Customer Communication Agent'
    elif agent_name_lower == 'post processing agent':
        return 'Post Processing Agent'
    elif agent_name_lower == 'audit agent':
        return 'Audit Agent'
    else:
        return agent_name

def get_agent_work_logs(customer_id):
    """Fetch agent work logs from CosmosDB for a specific customer"""
    if not cosmos_container:
        print("⚠️ CosmosDB not available, returning empty logs")
        return []
    
    try:
        # SQL query to get agent activity for a specific customer (removed ORDER BY)
        query = """
        SELECT 
            c.id AS composite_id,
            c.agent_id,
            c.customer_id,
            log.status,
            log.description,
            log.timestamp
        FROM c
        JOIN log IN c.work_log
        WHERE c.customer_id = @customer_id
        """
        
        # Query parameters
        parameters = [{"name": "@customer_id", "value": customer_id}]
        
        # Run query
        items = list(cosmos_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        # Process items to extract agent names from composite IDs
        processed_items = []
        for item in items:
            # Extract agent name from composite ID (format: "agent_name_CUSTOMER_ID")
            composite_id = item.get('composite_id', '')
            agent_name = item.get('agent_id', '')  # Use agent_id field if available
            
            print(f"🔍 Processing item: composite_id='{composite_id}', agent_id='{agent_name}'")
            
            # If agent_id is not available, try to extract from composite_id
            if not agent_name:
                if composite_id:
                    # Check if composite_id contains underscore (new format: "agent_name_CUSTOMER_ID")
                    if '_' in composite_id:
                        # Split by underscore and remove the last part (customer_id)
                        parts = composite_id.split('_')
                        if len(parts) > 1:
                            agent_name = '_'.join(parts[:-1])  # Join all parts except the last one
                        else:
                            agent_name = composite_id
                    else:
                        # Old format: composite_id is just the agent name
                        agent_name = composite_id
                else:
                    agent_name = 'Unknown Agent'
            
            # Normalize the agent name to match expected format
            normalized_agent_name = normalize_agent_name(agent_name)
            print(f"📋 Normalized agent name: '{agent_name}' -> '{normalized_agent_name}'")
            
            processed_item = {
                'agent_name': normalized_agent_name,
                'customer_id': item.get('customer_id', ''),
                'status': item.get('status', ''),
                'description': item.get('description', ''),
                'timestamp': item.get('timestamp', ''),
                'composite_id': composite_id
            }
            processed_items.append(processed_item)
        
        # Sort the results in Python after fetching
        processed_items.sort(key=lambda x: x.get('timestamp', ''))
        
        print(f"📊 Found {len(processed_items)} work log entries for customer {customer_id}")
        return processed_items
        
    except Exception as e:
        print(f"❌ Error fetching work logs from CosmosDB: {e}")
        return []

def get_agent_logs_by_agent_type(customer_id, agent_name):
    """Get specific agent's work logs for a customer"""
    if not cosmos_container:
        return []
    
    try:
        query = """
        SELECT 
            c.id AS composite_id,
            c.agent_id,
            c.customer_id,
            log.status,
            log.description,
            log.timestamp
        FROM c
        JOIN log IN c.work_log
        WHERE c.customer_id = @customer_id AND c.agent_id = @agent_name
        """
        
        parameters = [
            {"name": "@customer_id", "value": customer_id},
            {"name": "@agent_name", "value": agent_name}
        ]
        
        items = list(cosmos_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        # Process items to extract agent names from composite IDs
        processed_items = []
        for item in items:
            # Extract agent name from composite ID or use agent_id field
            composite_id = item.get('composite_id', '')
            agent_name = item.get('agent_id', '')
            
            # If agent_id is not available, try to extract from composite_id
            if not agent_name and composite_id:
                parts = composite_id.split('_')
                if len(parts) > 1:
                    agent_name = '_'.join(parts[:-1])
                else:
                    agent_name = composite_id
            
            # Normalize the agent name to match expected format
            agent_name = normalize_agent_name(agent_name)
            
            processed_item = {
                'agent_name': agent_name,
                'customer_id': item.get('customer_id', ''),
                'status': item.get('status', ''),
                'description': item.get('description', ''),
                'timestamp': item.get('timestamp', ''),
                'composite_id': composite_id
            }
            processed_items.append(processed_item)
        
        # Sort the results in Python after fetching
        processed_items.sort(key=lambda x: x.get('timestamp', ''))
        
        return processed_items
        
    except Exception as e:
        print(f"❌ Error fetching agent-specific logs: {e}")
        return []

def trigger_missing_documents_email(customer_id):
    """Trigger the missing documents email API"""
    try:
        # Email API endpoint
        email_api_url = "https://demo1414.azurewebsites.net:443/api/missing_documents/triggers/When_a_HTTP_request_is_received/invoke?api-version=2022-05-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=YZ3nOyknyM6xBlHMEYy_YMdDmTcgIpIVtzkgbiKX6Xg"
        
        # Email payload
        email_payload = {
            "customer_name": "Rohan Sharma",
            "customer_email": "rohan.sharma@example.com",
            "missing_document": "Payslip for June 2025"
        }
        
        # Send POST request to the email API
        response = requests.post(
            email_api_url,
            json=email_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200 or response.status_code == 202:
            print(f"✅ Email triggered successfully for customer {customer_id}")
            return True
        else:
            print(f"⚠️ Email API returned status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error triggering email API: {e}")
        return False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'banking-agent-system-2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global storage for active sessions and applications
active_sessions = {}
application_workflows = {}
agent_responses = {}

class EnhancedBankingSystem:
    def __init__(self):
        self.agent_categories = {
            'APPLICATION_PROCESS': {
                'name': '📋 Loan Origination',
                'color': '#0369a1',
                'description': 'Initial application and document processing',
                'agents': {
                    'pre_qualification': {
                        'name': 'Credit Liability Agent',
                        'status': 'available',
                        'description': 'Screens the customer’s basic eligibility before initiating the loan application process.',
                        'icon': '🎯',
                        'color': '#3b82f6',
                        'capabilities': ['Income verification', 'Credit score check', 'Eligibility assessment']
                    },
                    'application_assist': {
                        'name': 'Customer Service Agent',
                        'status': 'available',
                        'description': 'Assists the customer in submitting the loan application and collecting initial details.',
                        'icon': '🤝',
                        'color': '#06b6d4',
                        'capabilities': ['Application guidance', 'Form completion', 'Customer support']
                    },
                    'document_checker': {
                        'name': 'Document Verification Agent',
                        'status': 'available', 
                        'description': 'Verifies all submitted documents for completeness and compliance requirements',
                        'icon': '📋',
                        'color': '#8b5cf6',
                        'capabilities': ['KYC validation', 'Document verification', 'Compliance check']
                    }
                }
            },
            'ASSESSMENT_PROCESS': {
                'name': '📊 Loan Assessment',
                'color': '#0369a1',
                'description': 'Comprehensive financial and risk assessment',
                'agents': {
                    'valuation': {
                        'name': 'Asset Valuation Agent',
                        'status': 'available',
                        'description': 'Evaluates the property or asset offered as collateral to determine its market value.',
                        'icon': '🏠',
                        'color': '#10b981',
                        'capabilities': ['Property valuation', 'Market analysis', 'Asset assessment']
                    },
                    'credit_assessor': {
                        'name': 'Credit Assessment Agent',
                        'status': 'available',
                        'description': 'Analyzes the applicant’s financials and creditworthiness to assess loan viability.',
                        'icon': '📊',
                        'color': '#f59e0b',
                        'capabilities': ['Credit analysis', 'Financial modeling', 'Risk scoring']
                    },
                    'Underwriting': {
                        'name': 'Credit Risk and Underwriting Agent',
                        'status': 'available',
                        'description': 'Reviews risks and makes the final underwriting decision for loan approval.',
                        'icon': '🔍',
                        'color': '#ef4444',
                        'capabilities': ['Risk assessment', 'Policy compliance', 'Decision modeling']
                    }
                }
            },
            'POST_PROCESS': {
                'name': '📄 Loan Offer Generation',
                'color': '#0369a1',
                'description': 'Customer Communication Agent',
                'agents': {
                    'offer_generation': {
                        'name': 'Offer Generation Agent',
                        'status': 'available',
                        'description': 'Prepares and issues the official loan sanction letter and offer documentation.',
                        'icon': '📄',
                        'color': '#8b5cf6',
                        'capabilities': ['Offer creation', 'Terms calculation', 'Document generation']
                    },
                    'customer_communication': {
                        'name': 'Customer Relationship Agent',
                        'status': 'available',
                        'description': 'Communicates updates, next steps, and approval status to the customer.',
                        'icon': '📞',
                        'color': '#06b6d4',
                        'capabilities': ['Customer notifications', 'Status updates', 'Communication management']
                    }
                }
            },
            'CROSS_FUNCTIONAL': {
                'name': '🔒 Audit and Compliance Agent',
                'color': '#0369a1',
                'description': 'Oversight and compliance monitoring',
                'agents': {
                    'audit': {
                        'name': 'Audit Agent',
                        'status': 'available',
                        'description': 'Senior compliance and audit specialist',
                        'icon': '🔒',
                        'color': '#dc2626',
                        'capabilities': ['Compliance monitoring', 'Audit trails', 'Risk oversight']
                    }
                }
            }
        }
        
        # Flatten agents for easy access
        self.agents = {}
        for category_key, category in self.agent_categories.items():
            for agent_key, agent in category['agents'].items():
                self.agents[agent_key] = agent
        
        # Enhanced workflow steps
        self.workflow_steps = [
            {
                'name': 'Eligibility Screening',
                'category': 'APPLICATION_PROCESS',
                'agents': ['pre_qualification'],
                'description': 'Customer eligibility and initial requirements assessment',
                'required': True
            },
            {
                'name': 'Customer Application Assistance',
                'category': 'APPLICATION_PROCESS',
                'agents': ['application_assist'],
                'description': 'Complete application form processing and validation',
                'required': True
            },
            {
                'name': 'Document Verification',
                'category': 'APPLICATION_PROCESS', 
                'agents': ['document_checker'],
                'description': 'Comprehensive document validation and KYC verification',
                'required': True
            },
            {
                'name': 'Property/Site Valuation',
                'category': 'ASSESSMENT_PROCESS',
                'agents': ['valuation'],
                'description': 'Asset and collateral valuation assessment',
                'required': False
            },
            {
                'name': 'Credit Analysis & Appraisal',
                'category': 'ASSESSMENT_PROCESS',
                'agents': ['credit_assessor'],
                'description': 'Comprehensive credit history and financial analysis',
                'required': True
            },
            {
                'name': 'Risk Assessment & Underwriting',
                'category': 'ASSESSMENT_PROCESS',
                'agents': ['Underwriting'],
                'description': 'Advanced risk modeling and underwriting analysis',
                'required': True
            },
            {
                'name': 'Customer Communication',
                'category': 'POST_PROCESS',
                'agents': ['customer_communication'],
                'description': 'Customer communication and status updates',
                'required': True
            },
            {
                'name': 'Loan Offer Generation & Processing',
                'category': 'POST_PROCESS',
                'agents': ['offer_generation'],
                'description': 'Loan offer document generation and terms finalization',
                'required': True
            },
            {
                'name': 'Compliance Check and Internal Audit',
                'category': 'CROSS_FUNCTIONAL',
                'agents': ['audit'],
                'description': 'Compliance verification and audit process',
                'required': True
            }
        ]
    
    def create_application(self, customer_id):
        """Create a new comprehensive loan application workflow"""
        app_id = str(uuid.uuid4())[:8].upper()
        
        application_workflows[app_id] = {
            'id': app_id,
            'customer_id': customer_id,
            'created_at': datetime.datetime.now().isoformat(),
            'updated_at': datetime.datetime.now().isoformat(),
            'current_step': 0,
            'status': 'active',
            'priority': 'normal',
            'loan_type': 'home_loan',
            'loan_amount': 0,
            'current_category': 'APPLICATION_PROCESS',
            'steps': self._initialize_steps(),
            'messages': [],
            'agent_responses': {},
            'agents_involved': [],
            'audit_trail': [],
            'overall_progress': 96,  # Set to 96% as requested
            'summary': {
                'customer_profile': {},
                'financial_summary': {},
                'risk_assessment': {},
                'decisions': [],
                'recommendations': []
            }
        }
        
        # Initialize agent responses storage
        agent_responses[app_id] = {}
        for agent_key in self.agents.keys():
            agent_responses[app_id][agent_key] = {
                'responses': [],
                'analysis': {},
                'recommendations': [],
                'status': 'not_started',
                'last_activity': None
            }
        
        # Add initial audit entry
        self._add_audit_entry(app_id, 'Application Created', 'System', 
                             f'New loan application created for customer {customer_id}')
        
        return app_id
    
    def _initialize_steps(self):
        """Initialize workflow steps with proper structure"""
        steps = []
        for i, step in enumerate(self.workflow_steps):
            steps.append({
                'name': step['name'],
                'category': step['category'],
                'agents': step['agents'],
                'description': step['description'],
                'required': step['required'],
                'status': 'active' if i == 0 else 'pending',
                'current_agent': None,
                'assigned_agents': [],
                'started_at': datetime.datetime.now().isoformat() if i == 0 else None,
                'completed_at': None,
                'notes': [],
                'progress': 0,
                'estimated_time': '30 minutes',
                'actual_time': None
            })
        return steps
    
    def _add_audit_entry(self, app_id, action, agent, details, step_index=None):
        """Add entry to audit trail"""
        if app_id in application_workflows:
            application_workflows[app_id]['audit_trail'].append({
                'timestamp': datetime.datetime.now().isoformat(),
                'action': action,
                'agent': agent,
                'details': details,
                'step_index': step_index
            })
  

banking_system = EnhancedBankingSystem()

@app.route('/')
def index():
    # Applications page is now the default landing page
    return render_template('applications.html')

@app.route('/dashboard')
def dashboard():
    # The original index page is now accessible at /dashboard
    # Pass any URL parameters to ensure application loading works
    return render_template('index.html')

@app.route('/applications')
def applications():
    return render_template('applications.html')

@app.route('/api/applications')
def get_applications():
    apps = list(application_workflows.values())
    
    # If no applications in the system, send an empty list
    # Our JavaScript will use dummy data when the list is empty
    return jsonify({
        'applications': apps,
        'agent_categories': banking_system.agent_categories,
        'agents': banking_system.agents
    })

@app.route('/api/application/<app_id>')
def get_application(app_id):
    if app_id in application_workflows:
        return jsonify(application_workflows[app_id])
    return jsonify({'error': 'Application not found'}), 404

@app.route('/api/agent_logs/<customer_id>')
def get_agent_logs(customer_id):
    """Get all agent work logs for a customer from CosmosDB"""
    try:
        work_logs = get_agent_work_logs(customer_id)
        
        if not work_logs:
            return jsonify({
                'success': False,
                'customer_id': customer_id,
                'logs': [],
                'message': f'No work logs found for customer {customer_id}'
            })
        
        # Group logs by agent for easier UI consumption
        logs_by_agent = {}
        for log in work_logs:
            agent_name = log['agent_name']
            if agent_name not in logs_by_agent:
                logs_by_agent[agent_name] = []
            
            logs_by_agent[agent_name].append({
                'status': log['status'],
                'description': log['description'],
                'timestamp': log['timestamp']
            })
        
        return jsonify({
            'success': True,
            'customer_id': customer_id,
            'logs': work_logs,
            'logs_by_agent': logs_by_agent,
            'total_entries': len(work_logs)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch agent logs: {str(e)}'
        }), 500

@app.route('/api/agent_logs/<customer_id>/<agent_name>')
def get_specific_agent_logs(customer_id, agent_name):
    """Get work logs for a specific agent and customer"""
    try:
        agent_logs = get_agent_logs_by_agent_type(customer_id, agent_name)
        
        return jsonify({
            'success': True,
            'customer_id': customer_id,
            'agent_name': agent_name,
            'logs': agent_logs,
            'total_entries': len(agent_logs)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch agent logs: {str(e)}'
        }), 500

@app.route('/api/create_application', methods=['POST'])
def create_application():
    data = request.json
    customer_id = data.get('customer_id')
    
    if not customer_id:
        return jsonify({'error': 'Customer ID is required'}), 400
    
    app_id = banking_system.create_application(customer_id)
    return jsonify({
        'application_id': app_id,
        'workflow': application_workflows[app_id]
    })

@app.route('/api/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    app_id = data.get('application_id')
    message = data.get('message')
    agent_type = data.get('agent_type')
    
    if not app_id or not message or not agent_type:
        return jsonify({'error': 'Missing required data'}), 400
    
    # Get agent information
    agent_info = banking_system.agents.get(agent_type)
    if not agent_info:
        return jsonify({'error': f'Unknown agent type: {agent_type}'}), 400
    
    # Process message and get response
    response = process_agent_message(agent_type, message, app_id)
    
    # Store the interaction
    if app_id not in agent_responses:
        agent_responses[app_id] = {}
    if agent_type not in agent_responses[app_id]:
        agent_responses[app_id][agent_type] = {
            'agent_name': agent_info['name'],
            'responses': []
        }
    
    agent_responses[app_id][agent_type]['responses'].append({
        'message': message,
        'response': response,
        'timestamp': datetime.datetime.now().isoformat()
    })
    
    # Update application workflow if exists
    application = None
    if app_id in application_workflows:
        application = application_workflows[app_id]
        
        # Add message to application messages
        if 'messages' not in application:
            application['messages'] = []
        
        application['messages'].extend([
            {
                'type': 'user',
                'content': message,
                'timestamp': datetime.datetime.now().isoformat(),
                'agent': agent_type,
                'agent_name': agent_info['name']
            },
            {
                'type': 'agent',
                'content': response,
                'timestamp': datetime.datetime.now().isoformat(),
                'agent': agent_type,
                'agent_name': agent_info['name']
            }
        ])
    
    return jsonify({
        'response': response,
        'agent': agent_type,
        'agent_name': agent_info['name'],
        'application': application
    })

@socketio.on('connect')
def handle_connect():
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    active_sessions[session_id] = {
        'connected_at': datetime.datetime.now().isoformat(),
        'current_application': None
    }
    emit('connected', {'session_id': session_id})

@socketio.on('disconnect')
def handle_disconnect():
    session_id = session.get('session_id')
    if session_id in active_sessions:
        del active_sessions[session_id]

@socketio.on('join_application')
def handle_join_application(data):
    app_id = data['application_id']
    if app_id in application_workflows:
        session['current_application'] = app_id
        emit('application_joined', application_workflows[app_id])

@socketio.on('send_message')
def handle_message(data):
    app_id = data.get('application_id')
    message = data.get('message')
    agent_type = data.get('agent_type')
    
    if not app_id or not message or not agent_type:
        emit('error', {'message': 'Missing required data'})
        return
    
    # Get agent information
    agent_info = banking_system.agents.get(agent_type)
    if not agent_info:
        emit('error', {'message': f'Unknown agent type: {agent_type}'})
        return
    
    # Process message and get response
    response = process_agent_message(agent_type, message, app_id)
    
    # Store the interaction
    if app_id in agent_responses and agent_type in agent_responses[app_id]:
        agent_responses[app_id][agent_type]['responses'].append({
            'message': message,
            'response': response,
            'timestamp': datetime.datetime.now().isoformat()
        })
        agent_responses[app_id][agent_type]['status'] = 'active'
        agent_responses[app_id][agent_type]['last_activity'] = datetime.datetime.now().isoformat()
    
    # Add messages to application
    if app_id in application_workflows:
        user_message = {
            'id': str(uuid.uuid4())[:8],
            'timestamp': datetime.datetime.now().isoformat(),
            'type': 'user',
            'content': message,
            'agent': agent_type,
            'agent_name': agent_info['name']
        }
        
        agent_message = {
            'id': str(uuid.uuid4())[:8],
            'timestamp': datetime.datetime.now().isoformat(),
            'type': 'agent',
            'content': response,
            'agent': agent_type,
            'agent_name': agent_info['name'],
            'icon': agent_info['icon'],
            'color': agent_info['color']
        }
        
        application_workflows[app_id]['messages'].extend([user_message, agent_message])
        application_workflows[app_id]['updated_at'] = datetime.datetime.now().isoformat()
        
        # Add to audit trail
        banking_system._add_audit_entry(app_id, 'Agent Interaction', agent_info['name'],
                                      f'Processed message: {message[:50]}...')
        
        # Emit updates
        socketio.emit('application_updated', application_workflows[app_id], room=app_id)
        socketio.emit('message_response', {
            'application_id': app_id,
            'response': response,
            'agent': agent_type,
            'agent_name': agent_info['name'],
            'icon': agent_info['icon'],
            'color': agent_info['color']
        })

def process_agent_message(agent_type, message, app_id):
    """Process messages through different agents with realistic responses"""
    
    # Get customer ID from application
    customer_id = application_workflows.get(app_id, {}).get('customer_id', 'UNKNOWN')
    
    # Special handling for Loan Documentation Agent email triggers
    if agent_type == 'document_checker':
        message_lower = message.lower().strip()
        email_triggers = [
            'send the mail',
            'send mail',
            'send the mail for missing documents',
            'send mail for missing documents',
            'send the mail for the missing documents',
            'send mail for the missing documents'
        ]
        
        # Check if the message matches any email trigger phrases
        if any(trigger in message_lower for trigger in email_triggers):
            print(f"🔔 Email trigger detected for Loan Documentation Agent")
            
            # Trigger the missing documents email
            email_sent = trigger_missing_documents_email(customer_id)
            
            if email_sent:
                response_text = "📧 **Email Sent Successfully**\n\n"
                response_text += f"**Customer:** {customer_id}\n"
                response_text += f"**Action:** Missing documents notification email sent\n\n"
                response_text += "✅ An email notification regarding missing documents has been sent to the customer.\n\n"
                response_text += "**Email Details:**\n"
                response_text += "• **Recipient:** Rohan Sharma (rohan.sharma@example.com)\n"
                response_text += "• **Subject:** Missing Document Required - Loan Application\n"
                response_text += "• **Missing Document:** Payslip for June 2025\n\n"
                response_text += f"*Email sent on {datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')}*"
                
                # Add guidance for next agent
                next_agent_name = None
                for agent_key, current_name, next_name in AGENT_WORKFLOW_ORDER:
                    if agent_key == agent_type:
                        next_agent_name = next_name
                        break
                
                if next_agent_name:
                    response_text += f"\n\n**Next Step:** Select **{next_agent_name}** for the next updates."
                else:
                    response_text += f"\n\n**Workflow Complete:** This is the final step in the loan processing workflow."
                
                return response_text
            else:
                return "❌ **Email Failed**\n\nThere was an issue sending the email notification. Please try again or contact technical support."
    
    # Check if we have pre-loaded agent details in the application
    application = application_workflows.get(app_id, {})
    agent_details = application.get('agent_details', {})
    
    # If we have pre-loaded agent details for this agent type, use them
    if agent_type in agent_details:
        agent_detail = agent_details[agent_type]
        if agent_detail.get('has_data', False):
            print(f"✅ Using pre-loaded CosmosDB data for {agent_type}")
            return agent_detail['work_history_text']
        else:
            print(f"📋 No CosmosDB data available for {agent_type}")
            return f"📋 **No Data Available**\n\nNo work logs found for this agent and customer {customer_id}."
    else:
        # Fallback: Try to get real work logs from CosmosDB for this agent
        cosmos_logs = []
        if customer_id != 'UNKNOWN':
            try:
                # Map agent types to CosmosDB agent names
                agent_name_mapping = {
                    'pre_qualification': 'Pre-Qualification Agent',
                    'document_checker': 'Document Checker Agent', 
                    'application_assist': 'Application Assist Agent',
                    'valuation': 'Valuation Agent',
                    'credit_assessor': 'Credit Assessor Agent',
                    'Underwriting': 'Underwriting agent',  # Updated to match CosmosDB format
                    'offer_generation': 'Offer Generation Agent',
                    'customer_communication': 'Customer Communication Agent',
                    'audit': 'Audit Agent'
                }
                
                cosmos_agent_name = agent_name_mapping.get(agent_type)
                if cosmos_agent_name:
                    cosmos_logs = get_agent_logs_by_agent_type(customer_id, cosmos_agent_name)
                    
            except Exception as e:
                print(f"⚠️ Error fetching CosmosDB logs for {agent_type}: {e}")
        
        # If we have real logs from CosmosDB, format and return them            if cosmos_logs:
                log_text = f"📊 **Application Progress Update**\n\n"
                log_text += f"**Customer:** {customer_id}\n\n"
            
            # Create HTML table format for better display, wrapped in a div with no extra spacing
            log_text += '<div class="agent-logs-container">'
            log_text += '<table class="agent-logs-table">'
            log_text += '<thead><tr><th>#</th><th>Details</th><th>Date</th></tr></thead>'
            log_text += '<tbody>'
            
            for i, log in enumerate(cosmos_logs, 1):
                description = log['description']
                timestamp = log['timestamp']
                log_text += f'<tr><td>{i}</td><td>{description}</td><td>{timestamp}</td></tr>'
            
            log_text += '</tbody></table></div>'
            
            log_text += f"*Current status as of {datetime.datetime.now().strftime('%B %d, %Y')}*"
            
            # Add guidance for next agent
            next_agent_name = None
            for agent_key, current_name, next_name in AGENT_WORKFLOW_ORDER:
                if agent_key == agent_type:
                    next_agent_name = next_name
                    break
            
            if next_agent_name:
                log_text += f"\n\n**Next Step:** Select **{next_agent_name}** for the next updates."
            else:
                log_text += f"\n\n**Workflow Complete:** This is the final step in the loan processing workflow."
            
            return log_text
        else:
            print(f"📋 No CosmosDB data found for {agent_type}")
            return f"📋 **No Data Available**\n\nNo work logs found for this agent and customer {customer_id}."

@app.route('/api/applications/search')
def search_applications():
    application_id = request.args.get('application_id')
    customer_id = request.args.get('customer_id')
    search_type = request.args.get('search_type', 'application_id')
    
    if not application_id and not customer_id:
        return jsonify({'error': 'Either application_id or customer_id is required'}), 400
    
    # Search through existing applications
    found_application = None
    
    for app_id, app_data in application_workflows.items():
        match_found = False
        
        if search_type == 'application_id' and application_id:
            if app_id.lower() == application_id.lower():
                match_found = True
        elif search_type == 'customer_id' and customer_id:
            if app_data.get('customer_id', '').lower() == customer_id.lower():
                match_found = True
        elif search_type == 'both':
            if (application_id and app_id.lower() == application_id.lower()) and \
               (customer_id and app_data.get('customer_id', '').lower() == customer_id.lower()):
                match_found = True
        
        if match_found:
            found_application = app_data
            break
    
    if found_application:
        # Fetch CosmosDB logs for this customer and pre-populate all agent data
        customer_id = found_application.get('customer_id')
        cosmos_logs = []
        logs_by_agent = {}
        agent_details = {}
        
        if customer_id:
            try:
                cosmos_logs = get_agent_work_logs(customer_id)
                
                # Group logs by agent and prepare detailed agent information
                for log in cosmos_logs:
                    agent_name = log['agent_name']
                    print(f"🔍 Processing agent: '{agent_name}' for customer {customer_id}")
                    if agent_name not in logs_by_agent:
                        logs_by_agent[agent_name] = []
                    
                    logs_by_agent[agent_name].append({
                        'status': log['status'],
                        'description': log['description'],
                        'timestamp': log['timestamp']
                    })
                
                print(f"📋 Available agents in logs: {list(logs_by_agent.keys())}")
                
                # Pre-populate agent details with work history for all agents
                agent_name_mapping = {
                    'Pre-Qualification Agent': 'pre_qualification',
                    'Document Checker Agent': 'document_checker',
                    'Application Assist Agent': 'application_assist',
                    'Valuation Agent': 'valuation',
                    'Credit Assessor Agent': 'credit_assessor',
                    'Underwriting agent': 'Underwriting',  # Exact match for CosmosDB format (lowercase)
                    'Offer Generation Agent': 'offer_generation',
                    'Customer Communication Agent': 'customer_communication',
                    'Audit Agent': 'audit'
                }
                
                print(f"🗺️ Agent name mapping: {agent_name_mapping}")
                
                # Create detailed agent information for each agent
                for cosmos_agent_name, agent_type in agent_name_mapping.items():
                    agent_info = banking_system.agents.get(agent_type, {})
                    agent_logs = logs_by_agent.get(cosmos_agent_name, [])
                    
                    print(f"🔍 Processing mapping: '{cosmos_agent_name}' -> '{agent_type}' (found {len(agent_logs)} logs)")
                    
                    # Format the work history text for this agent
                    work_history_text = ""
                    if agent_logs:
                        work_history_text = f"📊 **Application Progress Update**\n\n"
                        work_history_text += f"**Customer:** {customer_id}\n\n"
                        
                        # Create HTML table format for better display, wrapped in a div with no extra spacing
                        work_history_text += '<div class="agent-logs-container">'
                        work_history_text += '<table class="agent-logs-table">'
                        work_history_text += '<thead><tr><th>#</th><th>Details</th><th>Date</th></tr></thead>'
                        work_history_text += '<tbody>'
                        
                        for i, log in enumerate(agent_logs, 1):
                            description = log['description']
                            timestamp = log['timestamp']
                            work_history_text += f'<tr><td>{i}</td><td>{description}</td><td>{timestamp}</td></tr>'
                        
                        work_history_text += '</tbody></table></div>'
                        
                        work_history_text += f"\n*Current status as of {datetime.datetime.now().strftime('%B %d, %Y')}*"
                        
                        # Add guidance for next agent
                        next_agent_name = None
                        for agent_key, current_name, next_name in AGENT_WORKFLOW_ORDER:
                            if agent_key == agent_type:
                                next_agent_name = next_name
                                break
                        
                        if next_agent_name:
                            work_history_text += f"\n\n**Next Step:** Select **{next_agent_name}** for the next updates."
                        else:
                            work_history_text += f"\n\n**Workflow Complete:** This is the final step in the loan processing workflow."
                        
                        print(f"✅ Generated work history for {agent_type}: {len(agent_logs)} entries")
                    else:
                        work_history_text = f"📋 **No recent updates found**\n\nNo progress updates available for customer {customer_id} for this agent."
                        print(f"❌ No logs found for {agent_type} (cosmos name: {cosmos_agent_name})")
                    
                    agent_details[agent_type] = {
                        'agent_info': agent_info,
                        'cosmos_agent_name': cosmos_agent_name,
                        'work_logs': agent_logs,
                        'work_history_text': work_history_text,
                        'has_data': len(agent_logs) > 0,
                        'activity_count': len(agent_logs)
                    }
                    
                print(f"📊 Loaded {len(cosmos_logs)} CosmosDB entries for customer {customer_id}")
                print(f"🔍 Pre-populated {len(agent_details)} agents with work history")
                
                # Store agent details in the found application for future use
                found_application['agent_details'] = agent_details
                application_workflows[found_application['id']] = found_application
                
            except Exception as e:
                print(f"⚠️ Error loading CosmosDB logs: {e}")
        
        return jsonify({
            'success': True,
            'application': found_application,
            'cosmos_logs': cosmos_logs,
            'logs_by_agent': logs_by_agent,
            'agent_details': agent_details,
            'message': f'Application found: {found_application["id"]} with {len(cosmos_logs)} work log entries pre-loaded for all agents'
        })
    else:
        # Create a demo application if none found (for testing purposes)
        if application_id or customer_id:
            demo_customer_id = customer_id if customer_id else (f"CUST{application_id[-4:]}" if application_id else "CUST0001")
            demo_app_id = banking_system.create_application(demo_customer_id)
            demo_app = application_workflows[demo_app_id]
            
            # If specific application ID was requested, update it
            if application_id:
                # Remove the old entry and create with new ID
                del application_workflows[demo_app_id]
                demo_app['id'] = application_id.upper()
                application_workflows[application_id.upper()] = demo_app
                
                # Update agent responses as well
                if demo_app_id in agent_responses:
                    agent_responses[application_id.upper()] = agent_responses[demo_app_id]
                    del agent_responses[demo_app_id]
            
            # Also load CosmosDB data for the demo application
            cosmos_logs = []
            logs_by_agent = {}
            agent_details = {}
            
            try:
                cosmos_logs = get_agent_work_logs(demo_customer_id)
                
                # Group logs by agent and prepare detailed agent information
                for log in cosmos_logs:
                    agent_name = log['agent_name']
                    if agent_name not in logs_by_agent:
                        logs_by_agent[agent_name] = []
                    
                    logs_by_agent[agent_name].append({
                        'status': log['status'],
                        'description': log['description'],
                        'timestamp': log['timestamp']
                    })
                
                # Pre-populate agent details with work history for all agents
                agent_name_mapping = {
                    'Pre-Qualification Agent': 'pre_qualification',
                    'Document Checker Agent': 'document_checker',
                    'Application Assist Agent': 'application_assist',
                    'Valuation Agent': 'valuation',
                    'Credit Assessor Agent': 'credit_assessor',
                    'Underwriting agent': 'Underwriting',  # Updated to match CosmosDB format
                    'Underwriting Agent': 'Underwriting',   # Keep both for backward compatibility
                    'Offer Generation Agent': 'offer_generation',
                    'Customer Communication Agent': 'customer_communication',
                    'Audit Agent': 'audit'
                }
                
                # Create detailed agent information for each agent
                for cosmos_agent_name, agent_type in agent_name_mapping.items():
                    agent_info = banking_system.agents.get(agent_type, {})
                    agent_logs = logs_by_agent.get(cosmos_agent_name, [])
                    
                    # Format the work history text for this agent
                    work_history_text = ""
                    if agent_logs:
                        work_history_text = f"📊 **Application Progress Update**\n\n"
                        work_history_text += f"**Customer:** {demo_customer_id}\n\n"
                        
                        # Create HTML table format for better display, wrapped in a div with no extra spacing
                        work_history_text += '<div class="agent-logs-container">'
                        work_history_text += '<table class="agent-logs-table">'
                        work_history_text += '<thead><tr><th>#</th><th>Details</th><th>Date</th></tr></thead>'
                        work_history_text += '<tbody>'
                        
                        for i, log in enumerate(agent_logs, 1):
                            description = log['description']
                            timestamp = log['timestamp']
                            work_history_text += f'<tr><td>{i}</td><td>{description}</td><td>{timestamp}</td></tr>'
                        
                        work_history_text += '</tbody></table></div>'
                        
                        work_history_text += f"\n*Current status as of {datetime.datetime.now().strftime('%B %d, %Y')}*"
                        
                        # Add guidance for next agent
                        next_agent_name = None
                        for agent_key, current_name, next_name in AGENT_WORKFLOW_ORDER:
                            if agent_key == agent_type:
                                next_agent_name = next_name
                                break
                        
                        if next_agent_name:
                            work_history_text += f"\n\n**Next Step:** Select **{next_agent_name}** for the next updates."
                        else:
                            work_history_text += f"\n\n**Workflow Complete:** This is the final step in the loan processing workflow."
                    else:
                        work_history_text = f"📋 **No recent updates found**\n\nNo progress updates available for customer {demo_customer_id}."
                    
                    agent_details[agent_type] = {
                        'agent_info': agent_info,
                        'cosmos_agent_name': cosmos_agent_name,
                        'work_logs': agent_logs,
                        'work_history_text': work_history_text,
                        'has_data': len(agent_logs) > 0,
                        'activity_count': len(agent_logs)
                    }
                
                # Store agent details in the application
                demo_app['agent_details'] = agent_details
                
            except Exception as e:
                print(f"⚠️ Error loading CosmosDB data for demo application: {e}")
            
            return jsonify({
                'success': True,
                'application': demo_app,
                'cosmos_logs': cosmos_logs,
                'logs_by_agent': logs_by_agent,
                'agent_details': agent_details,
                'message': f'Demo application created: {demo_app["id"]} with {len(cosmos_logs)} work log entries pre-loaded'
            })
        
        return jsonify({
            'success': False,
            'error': 'No application found with the provided details'
        }), 404

if __name__ == '__main__':
    print("🚀 Starting Flask-SocketIO server...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
