from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import uuid
import datetime
import json
import sys
import os
from azure.cosmos import CosmosClient, exceptions

# Add the parent directory to Python path to import the underwriting agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

def get_agent_work_logs(customer_id):
    """Fetch agent work logs from CosmosDB for a specific customer"""
    if not cosmos_container:
        print("⚠️ CosmosDB not available, returning empty logs")
        return []
    
    try:
        # SQL query to get agent activity for a specific customer (removed ORDER BY)
        query = """
        SELECT 
            c.id AS agent_name,
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
        
        # Sort the results in Python after fetching
        items.sort(key=lambda x: x.get('timestamp', ''))
        
        print(f"📊 Found {len(items)} work log entries for customer {customer_id}")
        return items
        
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
            c.id AS agent_name,
            c.customer_id,
            log.status,
            log.description,
            log.timestamp
        FROM c
        JOIN log IN c.work_log
        WHERE c.customer_id = @customer_id AND c.id = @agent_name
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
        
        # Sort the results in Python after fetching
        items.sort(key=lambda x: x.get('timestamp', ''))
        
        return items
        
    except Exception as e:
        print(f"❌ Error fetching agent-specific logs: {e}")
        return []

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
                'name': '📋 Application Process',
                'color': '#22c55e',
                'description': 'Initial application and document processing',
                'agents': {
                    'pre_qualification': {
                        'name': 'Rajesh Kumar - Eligibility Specialist',
                        'status': 'available',
                        'description': 'Senior eligibility officer specializing in customer assessment',
                        'icon': '🎯',
                        'color': '#3b82f6',
                        'capabilities': ['Income verification', 'Credit score check', 'Eligibility assessment']
                    },
                    'document_checker': {
                        'name': 'Priya Sharma - Document Specialist',
                        'status': 'available', 
                        'description': 'Lead document verification officer with KYC expertise',
                        'icon': '📋',
                        'color': '#8b5cf6',
                        'capabilities': ['KYC validation', 'Document verification', 'Compliance check']
                    },
                    'application_assist': {
                        'name': 'Amit Patel - Customer Relations',
                        'status': 'available',
                        'description': 'Customer service manager for application assistance',
                        'icon': '🤝',
                        'color': '#06b6d4',
                        'capabilities': ['Application guidance', 'Form completion', 'Customer support']
                    }
                }
            },
            'ASSESSMENT_PROCESS': {
                'name': '📊 Assessment Process',
                'color': '#f59e0b',
                'description': 'Comprehensive financial and risk assessment',
                'agents': {
                    'valuation': {
                        'name': 'Suresh Reddy - Property Valuer',
                        'status': 'available',
                        'description': 'Certified property valuation expert',
                        'icon': '🏠',
                        'color': '#10b981',
                        'capabilities': ['Property valuation', 'Market analysis', 'Asset assessment']
                    },
                    'credit_assessor': {
                        'name': 'Meera Singh - Credit Analyst',
                        'status': 'available',
                        'description': 'Senior credit analyst with 10+ years experience',
                        'icon': '📊',
                        'color': '#f59e0b',
                        'capabilities': ['Credit analysis', 'Financial modeling', 'Risk scoring']
                    },
                    'underwriting': {
                        'name': 'Vikram Joshi - Risk Manager',
                        'status': 'available',
                        'description': 'Chief underwriter and risk assessment specialist',
                        'icon': '🔍',
                        'color': '#ef4444',
                        'capabilities': ['Risk assessment', 'Policy compliance', 'Decision modeling']
                    },
                    'approver': {
                        'name': 'Anita Gupta - Branch Manager',
                        'status': 'available',
                        'description': 'Senior branch manager with loan approval authority',
                        'icon': '✅',
                        'color': '#22c55e',
                        'capabilities': ['Final approval', 'Policy adherence', 'Decision authority']
                    }
                }
            },
            'POST_PROCESS': {
                'name': '📄 Post Process',
                'color': '#3b82f6',
                'description': 'Loan finalization and customer communication',
                'agents': {
                    'offer_generation': {
                        'name': 'Ravi Agarwal - Loan Officer',
                        'status': 'available',
                        'description': 'Senior loan documentation officer',
                        'icon': '📄',
                        'color': '#8b5cf6',
                        'capabilities': ['Offer creation', 'Terms calculation', 'Document generation']
                    },
                    'customer_communication': {
                        'name': 'Kavya Nair - Relationship Manager',
                        'status': 'available',
                        'description': 'Customer relationship and communication specialist',
                        'icon': '📞',
                        'color': '#06b6d4',
                        'capabilities': ['Customer notifications', 'Status updates', 'Communication management']
                    },
                    'post_processing': {
                        'name': 'Deepak Malhotra - Operations Manager',
                        'status': 'available',
                        'description': 'Post-approval processing and documentation specialist',
                        'icon': '⚙️',
                        'color': '#64748b',
                        'capabilities': ['Documentation', 'System setup', 'Process completion']
                    }
                }
            },
            'CROSS_FUNCTIONAL': {
                'name': '🔒 Cross Functional',
                'color': '#9333ea',
                'description': 'Oversight and compliance monitoring',
                'agents': {
                    'audit': {
                        'name': 'Sanjay Kapoor - Compliance Officer',
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
                'name': 'Initial Assessment',
                'category': 'APPLICATION_PROCESS',
                'agents': ['pre_qualification'],
                'description': 'Customer eligibility and initial requirements assessment',
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
                'name': 'Application Processing',
                'category': 'APPLICATION_PROCESS',
                'agents': ['application_assist'],
                'description': 'Complete application form processing and validation',
                'required': True
            },
            {
                'name': 'Property Valuation',
                'category': 'ASSESSMENT_PROCESS',
                'agents': ['valuation'],
                'description': 'Asset and collateral valuation assessment',
                'required': False
            },
            {
                'name': 'Credit Analysis',
                'category': 'ASSESSMENT_PROCESS',
                'agents': ['credit_assessor'],
                'description': 'Comprehensive credit history and financial analysis',
                'required': True
            },
            {
                'name': 'Risk Assessment',
                'category': 'ASSESSMENT_PROCESS',
                'agents': ['underwriting'],
                'description': 'Advanced risk modeling and underwriting analysis',
                'required': True
            },
            {
                'name': 'Final Approval',
                'category': 'ASSESSMENT_PROCESS',
                'agents': ['approver'],
                'description': 'Final loan approval decision and terms setting',
                'required': True
            },
            {
                'name': 'Offer Creation',
                'category': 'POST_PROCESS',
                'agents': ['offer_generation'],
                'description': 'Loan offer document generation and terms finalization',
                'required': True
            },
            {
                'name': 'Customer Notification',
                'category': 'POST_PROCESS',
                'agents': ['customer_communication'],
                'description': 'Customer communication and status updates',
                'required': True
            },
            {
                'name': 'Final Processing',
                'category': 'POST_PROCESS',
                'agents': ['post_processing'],
                'description': 'Final documentation and loan account setup',
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
            'overall_progress': 45,  # Set to 45% as requested
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
    return render_template('index.html')

@app.route('/api/applications')
def get_applications():
    return jsonify({
        'applications': list(application_workflows.values()),
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
            print(f"📋 No CosmosDB data available for {agent_type}, using fallback")
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
                    'underwriting': 'Underwriting Agent',
                    'approver': 'Approval Agent',
                    'offer_generation': 'Offer Generation Agent',
                    'customer_communication': 'Customer Communication Agent',
                    'post_processing': 'Post Processing Agent',
                    'audit': 'Audit Agent'
                }
                
                cosmos_agent_name = agent_name_mapping.get(agent_type)
                if cosmos_agent_name:
                    cosmos_logs = get_agent_logs_by_agent_type(customer_id, cosmos_agent_name)
                    
            except Exception as e:
                print(f"⚠️ Error fetching CosmosDB logs for {agent_type}: {e}")
        
        # If we have real logs from CosmosDB, format and return them
        if cosmos_logs:
            log_text = f"� **Application Progress Update**\n\n"
            log_text += f"**Customer:** {customer_id}\n"
            log_text += f"**Recent Updates:** {len(cosmos_logs)} items\n\n"
            
            for i, log in enumerate(cosmos_logs, 1):
                log_text += f"**Update {i}:**\n"
                log_text += f"• **Status:** {log['status']}\n"
                log_text += f"• **Details:** {log['description']}\n"
                log_text += f"• **Date:** {log['timestamp']}\n"
                log_text += "-" * 50 + "\n"
            
            log_text += f"\n*Current status as of {datetime.datetime.now().strftime('%B %d, %Y')}*"
            return log_text
    
    # Fallback to mock responses if no CosmosDB data is available
    
    if agent_type == 'pre_qualification':
        return f"""🎯 **Pre-Qualification Analysis Complete**

**Customer Eligibility Assessment:**
• Income Verification: ✅ Verified (Monthly: ₹85,000)
• Employment Status: ✅ Stable (5+ years experience)
• Credit Score: ✅ Excellent (780/900)
• Existing EMIs: ₹12,000/month (DTI: 14%)

**Loan Eligibility:**
• Maximum Eligible Amount: ₹65,00,000
• Recommended Tenure: 20 years
• Estimated EMI: ₹52,000/month
• Interest Rate Band: 8.5% - 9.2%

**Next Steps:** Proceed to document verification stage."""

    elif agent_type == 'document_checker':
        return f"""📋 **Document Verification Summary**

**KYC Documents:**
• PAN Card: ✅ Verified (ABCDE1234F)
• Aadhaar: ✅ Verified & Linked
• Passport: ✅ Valid till 2030
• Address Proof: ✅ Current utility bill verified

**Income Documents:**
• Salary Slips: ✅ Last 3 months verified
• ITR: ✅ Last 2 years (₹12L, ₹14L annually)
• Form 16: ✅ Current year verified
• Bank Statements: ✅ 6 months analyzed

**Property Documents:**
• Sale Agreement: ✅ Verified
• Title Documents: ✅ Clear title
• Approvals: ✅ All sanctions in place

**Status:** All documents verified successfully. Compliance score: 98%"""

    elif agent_type == 'valuation':
        return f"""🏠 **Property Valuation Report**

**Property Details:**
• Type: 3BHK Apartment, 1250 sq ft
• Location: Prime residential area
• Age: Under construction (Ready in 6 months)
• Builder: Reputed developer with good track record

**Valuation Summary:**
• Agreement Value: ₹75,00,000
• Market Valuation: ₹78,50,000
• Bank Valuation: ₹76,00,000
• LTV Ratio: 85% (₹64,60,000 eligible)

**Market Analysis:**
• Recent sales in vicinity: ₹6,200/sq ft
• Appreciation trend: 8% annually
• Liquidity: High (Premium location)

**Recommendation:** Approve at bank valuation. Property is good collateral."""

    elif agent_type == 'credit_assessor':
        return f"""📊 **Credit Assessment Report**

**Credit Profile Analysis:**
• CIBIL Score: 780 (Excellent)
• Credit History: 8 years, clean record
• Active Credits: 2 (Credit card + Personal loan)
• Payment Behavior: 100% on-time payments

**Financial Strength:**
• Net Monthly Income: ₹75,000
• Monthly Obligations: ₹12,000
• Surplus Income: ₹63,000
• Proposed EMI: ₹52,000 (69% utilization)

**Risk Factors:**
• Industry: IT (Stable sector)
• Job Stability: ✅ 5+ years same company
• Co-applicant: Yes (Working spouse)

**Credit Decision:** APPROVE with standard terms. Low risk profile."""

    elif agent_type == 'underwriting':
        # Mock underwriting response
        return f"""🔍 **Comprehensive Underwriting Analysis**

**Risk Assessment Matrix:**
• Credit Risk: LOW (Score: 780, clean history)
• Income Risk: LOW (Stable IT sector, senior position)
• Property Risk: LOW (Prime location, reputed builder)
• Market Risk: MEDIUM (Current rate environment)

**Policy Compliance Check:**
• LTV Ratio: 85% ✅ (Within policy limit of 90%)
• FOIR: 69% ✅ (Within limit of 75%)
• Age Factor: ✅ (32 years, retirement coverage adequate)
• Insurance: ✅ (Life + Property insurance in place)

**Advanced Analytics:**
• Probability of Default: 0.8% (Very Low)
• Loss Given Default: 15% (Good recovery prospects)
• Expected Loss: ₹7,800 (Well within appetite)

**FINAL RECOMMENDATION:** **APPROVE** 
Loan Amount: ₹64,60,000 | Rate: 8.75% | Tenure: 20 years

*Analysis completed using standard underwriting guidelines*"""

    elif agent_type == 'approver':
        return f"""✅ **LOAN APPROVAL DECISION**

**Application Status: APPROVED** 🎉

**Approved Terms:**
• Loan Amount: ₹64,60,000
• Interest Rate: 8.75% (Floating)
• Tenure: 20 years (240 months)
• Monthly EMI: ₹56,847
• Processing Fee: ₹25,000 + GST

**Conditions:**
• Property insurance mandatory
• Life insurance for loan amount
• NACH mandate for EMI auto-debit
• Annual income proof submission

**Validity:** This approval is valid for 6 months from date of sanction.

**Next Steps:** Proceed to offer generation and documentation."""

    elif agent_type == 'offer_generation':
        return f"""📄 **Loan Offer Generated**

**GLOBAL TRUST BANK - HOME LOAN SANCTION LETTER**

Dear {application_workflows[app_id]['customer_id']},

We are pleased to inform you that your home loan application has been **APPROVED**.

**Loan Details:**
• Sanctioned Amount: ₹64,60,000
• Interest Rate: 8.75% p.a. (Floating)
• Tenure: 20 years
• EMI: ₹56,847 per month
• Processing Fee: ₹25,000 + GST (18%)

**Key Features:**
• No prepayment charges after 1 year
• Top-up facility available
• Online account management
• Doorstep service available

**Documents Required for Disbursal:**
• Original property documents
• Insurance policies
• NACH mandate form
• Loan agreement execution

Congratulations on your loan approval! 🏠"""

    elif agent_type == 'customer_communication':
        return f"""📞 **Customer Communication Update**

**Communication Timeline:**
• 10:30 AM: SMS sent - Loan approval notification
• 10:45 AM: Email sent - Detailed sanction letter
• 11:00 AM: WhatsApp sent - Welcome message with next steps
• 11:15 AM: Call attempted - Customer unavailable
• 11:30 AM: Voicemail left - Callback requested

**Customer Response:**
• Status: Acknowledged via SMS reply
• Feedback: "Very happy with the quick approval"
• Query: Asked about disbursement timeline
• Follow-up: Scheduled for tomorrow 2 PM

**Next Communications:**
• Legal document execution appointment
• Insurance advisor introduction
• Disbursement process explanation

**Customer Satisfaction Score:** 9/10 (Excellent)"""

    elif agent_type == 'post_processing':
        return f"""⚙️ **Post-Processing Status Update**

**Documentation Status:**
• Loan Agreement: ✅ Executed
• NACH Mandate: ✅ Activated
• Insurance Policies: ✅ In force
• Property Registration: 🔄 In progress

**System Setup:**
• Loan Account: ✅ Created (Account: 1234567890)
• Online Banking: ✅ Activated
• Mobile App Access: ✅ Enabled
• EMI Auto-debit: ✅ Scheduled for 5th of every month

**Disbursement Readiness:**
• Legal clearance: ✅ Complete
• Technical clearance: ✅ Complete
• Financial closure: ✅ Ready
• Disbursement amount: ₹64,60,000

**Timeline:** Disbursement scheduled for next working day post property registration."""

    elif agent_type == 'audit':
        return f"""🔒 **Audit Compliance Report**

**Process Compliance Review:**
• KYC Compliance: ✅ 100% Complete
• Credit Policy Adherence: ✅ All norms followed
• Documentation Standards: ✅ Met
• Approval Authority: ✅ Proper delegation followed

**Regulatory Compliance:**
• RBI Guidelines: ✅ Fully compliant
• RERA Compliance: ✅ Project registered
• Fair Practice Code: ✅ Adhered
• Customer Privacy: ✅ Protected

**Risk Management:**
• Credit Risk: ✅ Within appetite
• Operational Risk: ✅ Mitigated
• Legal Risk: ✅ Addressed
• Reputational Risk: ✅ Low

**Audit Opinion:** CLEAN - No compliance issues identified.
Process Quality Score: 96/100"""

    else:
        return f"Hello! I'm the {banking_system.agents[agent_type]['name']}. I'm ready to assist you with {message}. How can I help you today?"

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
                    'Underwriting Agent': 'underwriting',
                    'Approval Agent': 'approver',
                    'Offer Generation Agent': 'offer_generation',
                    'Customer Communication Agent': 'customer_communication',
                    'Post Processing Agent': 'post_processing',
                    'Audit Agent': 'audit'
                }
                
                # Create detailed agent information for each agent
                for cosmos_agent_name, agent_type in agent_name_mapping.items():
                    agent_info = banking_system.agents.get(agent_type, {})
                    agent_logs = logs_by_agent.get(cosmos_agent_name, [])
                    
                    # Format the work history text for this agent
                    work_history_text = ""
                    if agent_logs:
                        work_history_text = f"� **Application Progress Update**\n\n"
                        work_history_text += f"**Customer:** {customer_id}\n"
                        work_history_text += f"**Recent Updates:** {len(agent_logs)} items\n\n"
                        
                        for i, log in enumerate(agent_logs, 1):
                            work_history_text += f"**Update {i}:**\n"
                            work_history_text += f"• **Status:** {log['status']}\n"
                            work_history_text += f"• **Details:** {log['description']}\n"
                            work_history_text += f"• **Date:** {log['timestamp']}\n"
                            work_history_text += "-" * 50 + "\n"
                        
                        work_history_text += f"\n*Current status as of {datetime.datetime.now().strftime('%B %d, %Y')}*"
                    else:
                        work_history_text = f"📋 **No recent updates found**\n\nNo progress updates available for customer {customer_id}."
                    
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
            demo_customer_id = customer_id or f"CUST{application_id[-4:]}" if application_id else "CUST0001"
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
                    'Underwriting Agent': 'underwriting',
                    'Approval Agent': 'approver',
                    'Offer Generation Agent': 'offer_generation',
                    'Customer Communication Agent': 'customer_communication',
                    'Post Processing Agent': 'post_processing',
                    'Audit Agent': 'audit'
                }
                
                # Create detailed agent information for each agent
                for cosmos_agent_name, agent_type in agent_name_mapping.items():
                    agent_info = banking_system.agents.get(agent_type, {})
                    agent_logs = logs_by_agent.get(cosmos_agent_name, [])
                    
                    # Format the work history text for this agent
                    work_history_text = ""
                    if agent_logs:
                        work_history_text = f"� **Application Progress Update**\n\n"
                        work_history_text += f"**Customer:** {demo_customer_id}\n"
                        work_history_text += f"**Recent Updates:** {len(agent_logs)} items\n\n"
                        
                        for i, log in enumerate(agent_logs, 1):
                            work_history_text += f"**Update {i}:**\n"
                            work_history_text += f"• **Status:** {log['status']}\n"
                            work_history_text += f"• **Details:** {log['description']}\n"
                            work_history_text += f"• **Date:** {log['timestamp']}\n"
                            work_history_text += "-" * 50 + "\n"
                        
                        work_history_text += f"\n*Current status as of {datetime.datetime.now().strftime('%B %d, %Y')}*"
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
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
