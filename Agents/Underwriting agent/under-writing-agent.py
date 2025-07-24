# pip install azure-ai-projects==1.0.0b10 pyodbc
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import sys
import datetime
import pyodbc
import json
import os 


instructions_path = os.path.join(os.path.dirname(__file__), "instructions.txt")
with open(instructions_path, "r", encoding="utf-8") as f:
    instructions = f.read()
class CreditUnderwritingAgent:
    """Credit Underwriting Agent - Supervisory role in agent orchestration"""
    
    def __init__(self):
        self.project_client = None
        self.agent = None
        self.current_thread = None
        self.session_start_time = None
        self.db_connection = None
    
    def initialize_database_connection(self):
        """Initialize Azure SQL Database connection"""
        try:
            # Global Trust Bank Azure SQL Database connection
            server = 'XXXX'
            database = 'XXXX'
            username = 'XXXX'
            password = 'XXXX'
            driver = '{ODBC Driver 18 for SQL Server}'
            
            connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
            
            self.db_connection = pyodbc.connect(connection_string)
            print("✅ Connected to Global Trust Bank Database")
            return True
            
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            print("⚠️ Running in offline mode - database features disabled")
            return False
    
    def get_customer_data(self, customer_id):
        """Retrieve customer data from Global Trust Bank Database"""
        if not self.db_connection:
            return None
            
        try:
            cursor = self.db_connection.cursor()
            
            # Query to get comprehensive customer data for underwriting analysis
            query = """
            SELECT 
                m.Customer_ID,
                m.Name,
                m.Fathers_Name,
                m.DOB,
                m.Age,
                m.Gender,
                m.Marital_Status,
                m.Address,
                m.City,
                m.State,
                m.Pincode,
                m.Mobile,
                m.Alternate_Mobile,
                m.Email,
                m.PAN,
                m.Aadhaar,
                m.Nationality,
                m.Customer_Since,
                m.Risk_Category,
                m.Fraud_Flag,
                m.KYC_Status,
                m.Customer_Type,
                m.Annual_Income_Range,
                -- Employment Information
                e.Employment_Type,
                e.Employment_Category,
                e.Employer_Name,
                e.Designation,
                e.Work_Experience_Years,
                e.Monthly_Income,
                e.Other_Income,
                e.Total_Monthly_Income,
                e.Income_Verification,
                e.Employment_Status,
                e.Joining_Date,
                e.Previous_Employer,
                -- Bank Information  
                b.Bank_Name,
                b.Account_Number,
                b.Account_Type,
                b.Account_Balance,
                b.Average_Monthly_Balance,
                b.Account_Status,
                b.Customer_Category as Bank_Customer_Category,
                -- Loan Information
                l.Loan_Required,
                l.Loan_Amount,
                l.Loan_Purpose,
                l.EMI,
                l.Interest_Rate,
                l.Tenure_Months,
                l.Application_Date,
                l.Loan_Status,
                l.Credit_Score,
                l.Collateral_Required,
                l.Processing_Fee,
                l.Loan_Type,
                l.Insurance_Required,
                l.Document_Verifier_Name,
                l.Field_Agent_Name,
                l.Bank_Manager_Name,
                l.Loan_Officer_Name
            FROM Master_Customer_Data m
            LEFT JOIN Employment_Info e ON m.Customer_ID = e.Customer_ID
            LEFT JOIN Bank_Info b ON m.Customer_ID = b.Customer_ID
            LEFT JOIN Loan_Info l ON m.Customer_ID = l.Customer_ID
            WHERE m.Customer_ID = ?
            """
            
            cursor.execute(query, customer_id)
            row = cursor.fetchone()
            
            if not row:
                return None
                
            # Process the data into a structured format
            customer_data = {
                'personal_info': {},
                'employment_info': {},
                'bank_info': {},
                'loan_info': {},
                'risk_assessment': {},
                'transaction_summary': {}
            }
            
            # Extract personal information
            customer_data['personal_info'] = {
                'customer_id': row.Customer_ID,
                'name': row.Name,
                'fathers_name': row.Fathers_Name,
                'dob': row.DOB.strftime('%Y-%m-%d') if row.DOB else None,
                'age': row.Age,
                'gender': row.Gender,
                'marital_status': row.Marital_Status,
                'address': f"{row.Address}, {row.City}, {row.State} - {row.Pincode}",
                'mobile': row.Mobile,
                'alternate_mobile': row.Alternate_Mobile,
                'email': row.Email,
                'pan': row.PAN,
                'aadhaar': row.Aadhaar,
                'nationality': row.Nationality,
                'customer_since': row.Customer_Since.strftime('%Y-%m-%d') if row.Customer_Since else None,
                'kyc_status': row.KYC_Status,
                'customer_type': row.Customer_Type,
                'annual_income_range': row.Annual_Income_Range
            }
            
            # Extract employment information
            customer_data['employment_info'] = {
                'employment_type': row.Employment_Type,
                'employment_category': row.Employment_Category,
                'employer_name': row.Employer_Name,
                'designation': row.Designation,
                'work_experience_years': row.Work_Experience_Years,
                'monthly_income': float(row.Monthly_Income) if row.Monthly_Income else 0,
                'other_income': float(row.Other_Income) if row.Other_Income else 0,
                'total_monthly_income': float(row.Total_Monthly_Income) if row.Total_Monthly_Income else 0,
                'income_verification': row.Income_Verification,
                'employment_status': row.Employment_Status,
                'joining_date': row.Joining_Date.strftime('%Y-%m-%d') if row.Joining_Date else None,
                'previous_employer': row.Previous_Employer
            }
            
            # Extract bank information
            customer_data['bank_info'] = {
                'bank_name': row.Bank_Name,
                'account_number': row.Account_Number,
                'account_type': row.Account_Type,
                'account_balance': float(row.Account_Balance) if row.Account_Balance else 0,
                'average_monthly_balance': float(row.Average_Monthly_Balance) if row.Average_Monthly_Balance else 0,
                'account_status': row.Account_Status,
                'customer_category': row.Bank_Customer_Category
            }
            
            # Extract loan information
            customer_data['loan_info'] = {
                'loan_required': row.Loan_Required,
                'loan_amount': float(row.Loan_Amount) if row.Loan_Amount else 0,
                'loan_purpose': row.Loan_Purpose,
                'emi': float(row.EMI) if row.EMI else 0,
                'interest_rate': float(row.Interest_Rate) if row.Interest_Rate else 0,
                'tenure_months': row.Tenure_Months,
                'application_date': row.Application_Date.strftime('%Y-%m-%d') if row.Application_Date else None,
                'loan_status': row.Loan_Status,
                'credit_score': row.Credit_Score,
                'collateral_required': row.Collateral_Required,
                'processing_fee': float(row.Processing_Fee) if row.Processing_Fee else 0,
                'loan_type': row.Loan_Type,
                'insurance_required': row.Insurance_Required,
                'document_verifier': row.Document_Verifier_Name,
                'field_agent': row.Field_Agent_Name,
                'bank_manager': row.Bank_Manager_Name,
                'loan_officer': row.Loan_Officer_Name
            }
            
            # Extract risk assessment information
            customer_data['risk_assessment'] = {
                'risk_category': row.Risk_Category,
                'fraud_flag': row.Fraud_Flag,
                'credit_score': row.Credit_Score
            }
            
            # Get recent transaction summary
            trans_query = """
            SELECT COUNT(*) as transaction_count,
                   SUM(CASE WHEN Amount > 0 THEN Amount ELSE 0 END) as total_credits,
                   SUM(CASE WHEN Amount < 0 THEN ABS(Amount) ELSE 0 END) as total_debits,
                   AVG(Amount) as avg_transaction_amount
            FROM Transaction_History 
            WHERE Customer_ID = ? AND Transaction_Date >= DATEADD(month, -3, GETDATE())
            """
            
            cursor.execute(trans_query, customer_id)
            trans_row = cursor.fetchone()
            
            if trans_row:
                customer_data['transaction_summary'] = {
                    'transaction_count_3months': trans_row.transaction_count or 0,
                    'total_credits_3months': float(trans_row.total_credits) if trans_row.total_credits else 0,
                    'total_debits_3months': float(trans_row.total_debits) if trans_row.total_debits else 0,
                    'avg_transaction_amount': float(trans_row.avg_transaction_amount) if trans_row.avg_transaction_amount else 0
                }
            
            cursor.close()
            return customer_data
            
        except Exception as e:
            print(f"❌ Error retrieving customer data: {str(e)}")
            return None
    
    def analyze_credit_profile(self, customer_data):
        """Analyze customer credit profile and generate underwriting assessment"""
        if not customer_data:
            return "❌ No customer data available for analysis"
        
        analysis = {
            'customer_id': customer_data['personal_info']['customer_id'],
            'risk_assessment': {},
            'document_verification': {},
            'financial_analysis': {},
            'recommendations': {}
        }
        
        # Extract data from the actual database structure
        employment_info = customer_data['employment_info']
        loan_info = customer_data['loan_info']
        bank_info = customer_data['bank_info']
          # Calculate key ratios using actual database fields - handle None values
        monthly_income = employment_info.get('total_monthly_income', 0)
        if monthly_income is None:
            monthly_income = 0
            
        total_debt = 0  # Can be calculated from existing loans if needed
        loan_amount = loan_info.get('loan_amount', 0)
        if loan_amount is None:
            loan_amount = 0
        
        # DTI Ratio calculation - handle division by zero
        monthly_debt = total_debt / 12 if total_debt > 0 else 0
        dti_ratio = (monthly_debt / monthly_income * 100) if monthly_income > 0 else 0
        
        # Loan to Income ratio
        annual_income = monthly_income * 12
        lti_ratio = (loan_amount / annual_income * 100) if annual_income > 0 else 0
        
        analysis['financial_analysis'] = {
            'monthly_income': monthly_income,
            'total_debt': total_debt,
            'dti_ratio': round(dti_ratio, 2),
            'lti_ratio': round(lti_ratio, 2),
            'cibil_score': loan_info.get('credit_score', 0)
        }
        
        # Risk Assessment
        risk_score = 0
        risk_factors = []
          # CIBIL Score assessment - handle None values
        cibil_score = loan_info.get('credit_score', 0)
        if cibil_score is None:
            cibil_score = 0
        
        if cibil_score >= 750:
            risk_score += 25
        elif cibil_score >= 650:
            risk_score += 15
            risk_factors.append("Moderate credit score")
        else:
            risk_factors.append("Low credit score - High Risk")
        
        # DTI Ratio assessment
        if dti_ratio <= 30:
            risk_score += 25
        elif dti_ratio <= 50:
            risk_score += 15
            risk_factors.append("Moderate debt burden")
        else:
            risk_factors.append("High debt-to-income ratio - High Risk")
        
        # Employment stability - handle None values
        experience_years = employment_info.get('work_experience_years', 0)
        if experience_years is None:
            experience_years = 0
            
        if experience_years >= 3:
            risk_score += 20
        elif experience_years >= 1:
            risk_score += 10
            risk_factors.append("Limited work experience")
        else:
            risk_factors.append("Insufficient work experience - High Risk")
        
        # Document verification - based on actual database fields
        kyc_status = customer_data['personal_info'].get('kyc_status', 'Pending')
        pan_available = bool(customer_data['personal_info'].get('pan'))
        aadhaar_available = bool(customer_data['personal_info'].get('aadhaar'))
        income_verification = employment_info.get('income_verification', 'Pending')
        
        verified_docs_count = 0
        if kyc_status == 'Verified':
            verified_docs_count += 1
        if pan_available:
            verified_docs_count += 1
        if aadhaar_available:
            verified_docs_count += 1
        if income_verification == 'Verified':
            verified_docs_count += 1
            
        if verified_docs_count >= 3:
            risk_score += 20
        elif verified_docs_count >= 2:
            risk_score += 10
            risk_factors.append("Incomplete document verification")
        else:
            risk_factors.append("Missing critical documents - High Risk")
        
        # Income verification
        if monthly_income > 0:
            risk_score += 10
        else:
            risk_factors.append("Income not verified - High Risk")
        
        analysis['risk_assessment'] = {
            'risk_score': risk_score,
            'risk_category': 'Low Risk' if risk_score >= 80 else 'Medium Risk' if risk_score >= 60 else 'High Risk',
            'risk_factors': risk_factors
        }
          # Generate recommendations
        recommendations = []
        if risk_score >= 80:
            recommendations.append("✅ APPROVE - Low risk profile")
            recommendations.append(f"Recommended loan amount: ₹{loan_amount:,.2f}")
            recommendations.append("Standard interest rate applicable")
        elif risk_score >= 60:
            recommended_amount = min(loan_amount, annual_income * 3)
            recommendations.append("⚠️ CONDITIONAL APPROVAL - Medium risk")
            recommendations.append(f"Recommended loan amount: ₹{recommended_amount:,.2f}")
            recommendations.append("Higher interest rate or additional collateral required")
        else:
            recommendations.append("❌ REJECT - High risk profile")
            recommendations.append("Recommend customer to improve credit profile")
            recommendations.append("Consider reapplication after 6 months")
        
        analysis['recommendations'] = recommendations
        
        return analysis
    
    def initialize_agent(self):
        """Initialize the Azure AI agent and database connection"""
        try:
            # Initialize database connection
            self.initialize_database_connection()
            
            # Initialize AI agent
            self.project_client = AIProjectClient.from_connection_string(
                credential=DefaultAzureCredential(),
                conn_str="eastus2.api.azureml.ms;aee23923-3bba-468d-8dcd-7c4bc1ce218f;rg-ronakofficial1414-9323_ai;ronakofficial1414-8644")

            self.agent = self.project_client.agents.get_agent("asst_GIAVHYJZj8teaZ5MriOttU7g")
            self.session_start_time = datetime.datetime.now()
            return True
        except Exception as e:
            print(f"❌ Error initializing agent: {str(e)}")
            return False
    
    def create_new_thread(self):
        """Create a new conversation thread"""
        try:
            self.current_thread = self.project_client.agents.create_thread()
            print(f"✅ New conversation thread created: {self.current_thread.id}")
              # Send initial context message to establish the agent's role
            initial_context = instructions
            
            self.project_client.agents.create_message(
                thread_id=self.current_thread.id,
                role="user",
                content=initial_context
            )
            
            return True
        except Exception as e:
            print(f"❌ Error creating new thread: {str(e)}")
            return False
    
    def get_agent_response(self, user_message):
        """Send user message to agent and get response with customer data integration"""
        try:
            # Check if user is asking for customer analysis - expanded patterns
            import re
            customer_patterns = [
                r'analyze customer',
                r'customer id',
                r'get customer', 
                r'customer analysis',
                r'customer\s+\w*\d+',  # customer CUST0006, customer 123, etc.
                r'\w*\d+',  # CUST0006, 123456, etc. when mentioned alone
                r'assess.*customer',
                r'evaluate.*customer'
            ]
            
            # Check if any pattern matches
            for pattern in customer_patterns:
                if re.search(pattern, user_message.lower()):
                    return self.handle_customer_analysis(user_message)
              # Create system reminder about database capabilities
            system_reminder = f"""
            SYSTEM REMINDER: You have DIRECT DATABASE ACCESS to Global Trust Bank's SQL database.
            For any customer-related queries, use your database access tools to retrieve actual data.
            
            USER MESSAGE: {user_message}
            
            If this involves a customer ID, query the database automatically.
            """
            
            # Create message from user
            message = self.project_client.agents.create_message(
                thread_id=self.current_thread.id,
                role="user",
                content=system_reminder
            )

            # Process the message through the agent
            run = self.project_client.agents.create_and_process_run(
                thread_id=self.current_thread.id,
                agent_id=self.agent.id
            )
            
            # Get the latest messages
            messages = self.project_client.agents.list_messages(thread_id=self.current_thread.id)
            
            # Extract the response from text_messages
            if hasattr(messages, 'text_messages'):
                text_messages = list(messages.text_messages)
                
                if text_messages:
                    # Get the most recent message (should be the assistant's response)
                    latest_message = text_messages[0]  # Most recent is usually first
                      # Extract the text value from MessageTextContent object
                    if hasattr(latest_message, 'text') and hasattr(latest_message.text, 'value'):
                        return latest_message.text.value
            
            return "I'm sorry, I couldn't generate a response."
            
        except Exception as e:
            raise Exception(f"Error getting response: {str(e)}")    
    def handle_customer_analysis(self, user_message):
        """Handle customer data analysis requests"""
        try:
            # Extract customer ID from message - support multiple formats including full IDs
            import re
            
            # First try to find complete customer IDs like CUST0001, CUST0006, etc.
            customer_id_match = re.search(r'\b(CUST\d+)\b', user_message, re.IGNORECASE)
            
            if not customer_id_match:
                # Try patterns like "Customer ID 0001", "customer 0001", "ID 0001"
                customer_id_match = re.search(r'(?:customer\s*id|customer|id)[\s:]*(\d+)', user_message, re.IGNORECASE)
                if customer_id_match:
                    # Format as CUST + zero-padded number
                    customer_number = customer_id_match.group(1).zfill(4)  # Pad to 4 digits
                    customer_id = f"CUST{customer_number}"
                else:
                    # Fallback to standalone numbers and format them
                    standalone_match = re.search(r'\b(\d+)\b', user_message)
                    if standalone_match:
                        customer_number = standalone_match.group(1).zfill(4)
                        customer_id = f"CUST{customer_number}"
                    else:
                        customer_id_match = None
            else:
                customer_id = customer_id_match.group(1).upper()
            
            if not customer_id_match and 'customer_id' not in locals():
                return """🔍 **CUSTOMER ANALYSIS REQUEST**
                
Please provide a customer ID to analyze. 

**Format examples:**
• "Analyze customer CUST0006"
• "Customer ID 0001" (will be formatted as CUST0001)
• "Get customer 0006 analysis"
• "Analyze CUST0001"

**What I'll automatically retrieve and analyze:**
• KYC Documentation: PAN and Aadhaar status from database
• Income Verification: Recent salary, ITRs, and Form 16 status  
• Property Details: Relevant property documents (if applicable)
• Bank Statements: Last 3-6 months transaction history
• Credit History: CIBIL/credit score and previous loans
• Employment Details: Current status, tenure, and history
• Complete risk assessment and loan recommendations"""
              # Use the extracted customer_id  
            if not self.db_connection:
                return """❌ **Database Connection Not Available**
                
I'm currently running in offline mode. To perform customer analysis, I need:
• Azure SQL Database connection
• Customer data access
• Document verification system

Please ensure database connectivity is established."""
            
            print(f"🔄 Retrieving customer data for ID: {customer_id}")
            customer_data = self.get_customer_data(customer_id)
            
            if not customer_data:
                return f"""❌ **Customer Not Found**
                
Customer ID {customer_id} was not found in the database.

**Please verify:**
• Customer ID is correct (format: CUST0001, CUST0006, etc.)
• Customer exists in system
• Database access permissions

**Alternative actions:**
• Check customer ID format
• Contact system administrator  
• Verify customer registration status"""
            
            print("🔄 Performing credit analysis...")
            analysis = self.analyze_credit_profile(customer_data)
            
            # Get AI agent's professional analysis and recommendations
            print("🤖 Generating AI-powered underwriting analysis...")
            ai_analysis_prompt = f"""
            As a Senior Credit Underwriting Agent with database access, analyze this customer profile:
            
            CUSTOMER: {customer_data['personal_info']['name']} (ID: {customer_id})
            
            KEY FINANCIAL DATA:
            • Total Monthly Income: {self.safe_format_currency(customer_data['employment_info']['total_monthly_income'])}
            • Account Balance: {self.safe_format_currency(customer_data['bank_info']['account_balance'])}
            • Employment: {customer_data['employment_info']['employment_type']} - {self.safe_format_number(customer_data['employment_info']['work_experience_years'], 0)} years
            • Credit Score: {self.safe_format_number(customer_data['loan_info']['credit_score'], 'Not Available')}
            • KYC Status: {customer_data['personal_info']['kyc_status']}
            • Account Status: {customer_data['bank_info']['account_status']}
            
            AUTOMATED RISK ASSESSMENT:
            • Risk Score: {analysis['risk_assessment']['risk_score']}/100
            • Risk Category: {analysis['risk_assessment']['risk_category']}
            • Primary Risk Factors: {', '.join(analysis['risk_assessment']['risk_factors']) if analysis['risk_assessment']['risk_factors'] else 'None identified'}
              PROVIDE YOUR PROFESSIONAL UNDERWRITING SUMMARY:
            
            1. **CREDITWORTHINESS ASSESSMENT:** Overall evaluation of customer's ability to repay
            2. **KEY STRENGTHS:** Positive factors supporting loan approval
            3. **CONCERNS & WEAKNESSES:** Risk factors requiring attention
            4. **LOAN RECOMMENDATION:** Approve/Conditional/Reject with rationale
            5. **SUGGESTED TERMS:** If approved - loan amount, interest rate, tenure recommendations
            6. **CONDITIONS:** Any requirements before final approval
            7. **NEXT STEPS:** Specific actions needed for processing
            
            IMPORTANT: End your analysis with a clear one-line final recommendation:
            **📋 FINAL RECOMMENDATION:** [Provide ONE clear sentence: "APPROVE loan of ₹X at Y% interest" or "REJECT due to high risk factors" or "CONDITIONAL APPROVAL - pending KYC completion, recommend ₹X loan at Y% interest"]
            
            Keep your analysis professional, concise, and action-oriented. Focus on lending decision factors.
            """
            
            # Get AI agent's analysis
            ai_response = self.get_ai_agent_analysis(ai_analysis_prompt)
            
            # Format comprehensive response
            response = f"""
📊 **CREDIT UNDERWRITING ANALYSIS REPORT**
═══════════════════════════════════════════

**CUSTOMER:** {customer_data['personal_info']['name']} (ID: {customer_id})
**DATE:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🏷️ **PERSONAL INFORMATION**
• Name: {customer_data['personal_info']['name']}
• Father's Name: {customer_data['personal_info']['fathers_name']}
• Age: {customer_data['personal_info']['age']} years
• Gender: {customer_data['personal_info']['gender']}
• PAN: {customer_data['personal_info']['pan']}
• Aadhaar: {customer_data['personal_info']['aadhaar']}
• Phone: {customer_data['personal_info']['mobile']}
• Email: {customer_data['personal_info']['email']}
• Address: {customer_data['personal_info']['address']}
• KYC Status: {customer_data['personal_info']['kyc_status']}
• Customer Since: {customer_data['personal_info']['customer_since']}

💼 **EMPLOYMENT INFORMATION**
• Employment Type: {self.safe_format_number(customer_data['employment_info']['employment_type'], 'Not Specified')}
• Employer: {self.safe_format_number(customer_data['employment_info']['employer_name'], 'Not Specified')}
• Designation: {self.safe_format_number(customer_data['employment_info']['designation'], 'Not Specified')}
• Work Experience: {self.safe_format_number(customer_data['employment_info']['work_experience_years'], 0)} years
• Employment Status: {self.safe_format_number(customer_data['employment_info']['employment_status'], 'Unknown')}
• Income Verification: {self.safe_format_number(customer_data['employment_info']['income_verification'], 'Pending')}

💰 **FINANCIAL PROFILE**
• Monthly Income: {self.safe_format_currency(customer_data['employment_info']['monthly_income'])}
• Other Income: {self.safe_format_currency(customer_data['employment_info']['other_income'])}
• Total Monthly Income: {self.safe_format_currency(customer_data['employment_info']['total_monthly_income'])}
• Account Balance: {self.safe_format_currency(customer_data['bank_info']['account_balance'])}
• Average Monthly Balance: {self.safe_format_currency(customer_data['bank_info']['average_monthly_balance'])}
• Credit Score: {self.safe_format_number(customer_data['loan_info']['credit_score'], 'Not Available')}

🏦 **BANKING INFORMATION**
• Bank Name: {customer_data['bank_info']['bank_name']}
• Account Type: {customer_data['bank_info']['account_type']}
• Account Status: {customer_data['bank_info']['account_status']}
• Customer Category: {customer_data['bank_info']['customer_category']}

📋 **LOAN APPLICATION DETAILS**
• Loan Amount Requested: {self.safe_format_currency(customer_data['loan_info']['loan_amount'])}
• Loan Purpose: {self.safe_format_number(customer_data['loan_info']['loan_purpose'], 'Not Specified')}
• Loan Type: {self.safe_format_number(customer_data['loan_info']['loan_type'], 'Not Specified')}
• Proposed EMI: {self.safe_format_currency(customer_data['loan_info']['emi'])}
• Interest Rate: {self.safe_format_number(customer_data['loan_info']['interest_rate'], 'TBD')}%
• Tenure: {self.safe_format_number(customer_data['loan_info']['tenure_months'], 'TBD')} months
• Application Date: {self.safe_format_number(customer_data['loan_info']['application_date'], 'Not Available')}
• Current Status: {self.safe_format_number(customer_data['loan_info']['loan_status'], 'Pending')}
• Collateral Required: {self.safe_format_number(customer_data['loan_info']['collateral_required'], 'TBD')}
• Insurance Required: {self.safe_format_number(customer_data['loan_info']['insurance_required'], 'TBD')}

📊 **RISK ANALYSIS**
• Risk Score: {analysis['risk_assessment']['risk_score']}/100
• Risk Category: {analysis['risk_assessment']['risk_category']}
• DTI Ratio: {analysis['financial_analysis']['dti_ratio']}%
• LTI Ratio: {analysis['financial_analysis']['lti_ratio']}%

⚠️ **RISK FACTORS:**
{chr(10).join(f"• {factor}" for factor in analysis['risk_assessment']['risk_factors']) if analysis['risk_assessment']['risk_factors'] else "• No significant risk factors identified"}

✅ **UNDERWRITING RECOMMENDATIONS:**
{chr(10).join(f"• {rec}" for rec in analysis['recommendations'])}

� **TRANSACTION SUMMARY (Last 3 Months):**
• Total Transactions: {customer_data['transaction_summary']['transaction_count_3months']}
• Total Credits: ₹{customer_data['transaction_summary']['total_credits_3months']:,.2f}
• Total Debits: ₹{customer_data['transaction_summary']['total_debits_3months']:,.2f}
• Average Transaction: ₹{customer_data['transaction_summary']['avg_transaction_amount']:,.2f}

📄 **DOCUMENT VERIFICATION STATUS:**
• KYC Status: {customer_data['personal_info']['kyc_status']}
• PAN Card: {"✅ Available" if customer_data['personal_info']['pan'] else "❌ Missing"}
• Aadhaar Card: {"✅ Available" if customer_data['personal_info']['aadhaar'] else "❌ Missing"}
• Income Verification: {customer_data['employment_info']['income_verification']}

👥 **PROCESSING TEAM:**
• Document Verifier: {customer_data['loan_info']['document_verifier']}
• Field Agent: {customer_data['loan_info']['field_agent']}
• Bank Manager: {customer_data['loan_info']['bank_manager']}
• Loan Officer: {customer_data['loan_info']['loan_officer']}

🎯 **RISK ASSESSMENT SUMMARY:**
• Fraud Flag: {customer_data['risk_assessment']['fraud_flag']}
• Risk Category: {customer_data['risk_assessment']['risk_category']}

───────────────────────────────────────────
**SUPERVISOR NOTE:** This comprehensive analysis has been automatically generated from database records.
**NEXT STEPS:** Forward to Approval Agent with recommendation status.
**AUTOMATED ASSESSMENT:** All required documentation and verification details retrieved from database.

🤖 **AI AGENT'S PROFESSIONAL ANALYSIS:**
═══════════════════════════════════════════
{ai_response}
═══════════════════════════════════════════
"""
            return response
            
        except Exception as e:
            return f"❌ Error performing customer analysis: {str(e)}"

    def display_agent_capabilities(self):
        """Display the agent's capabilities and available commands"""
        capabilities = """
        🏦 CREDIT UNDERWRITING AGENT CAPABILITIES:
        
        � DATABASE ACCESS TOOLS:
        • Direct SQL database connectivity to Global Trust Bank
        • Automated customer data retrieval using Customer ID
        • Real-time access to all customer records and transaction history
        • No manual data entry required - everything automated
        
        �📋 DOCUMENT VERIFICATION (FROM DATABASE):
        • KYC validation (PAN, Aadhaar verification status)
        • Income proof analysis (salary slips, ITRs, Form 16 verification)
        • Property document verification (for secured loans)
        • Bank statement cross-checking (automated retrieval)
        
        📊 CREDITWORTHINESS ANALYSIS:
        • CIBIL/Credit score evaluation (from database records)
        • Income-to-loan ratio assessment
        • Debt-to-income (DTI) ratio computation
        • Transaction pattern analysis (last 3-6 months)
        
        ⚠️ RISK ASSESSMENT:
        • Internal credit scoring model application
        • Red flag identification (job changes, defaults)
        • Fraud detection and verification
        • Automated risk profiling
        
        💰 LOAN STRUCTURING:
        • Optimal loan amount recommendations
        • Tenure and interest rate suggestions
        • Collateral/guarantor requirements
        
        📝 CREDIT MEMO PREPARATION:
        • Automated financial summary compilation
        • Risk assessment documentation
        • Recommendation reports for approval
        
        🎯 SUPERVISORY FUNCTIONS:
        • Agent orchestration coordination
        • Process workflow management
        • Quality assurance oversight
        
        🚀 AUTOMATED COMMANDS:
        • 'Analyze customer CUST0006' - Full automated analysis
        • 'Customer ID CUST0006' - Alternative format
        • 'Assess CUST0006' - Quick assessment
        
        SPECIAL COMMANDS:
        • 'new conversation' - Start fresh thread
        • 'capabilities' - Show this menu
        • 'thread info' - Display current thread info
        • 'db status' - Check database connection
        • 'quit/exit/bye' - End session
        
        💡 KEY FEATURE: Just provide Customer ID - all data retrieved automatically!
        """
        print(capabilities)

    def get_thread_info(self):
        """Display current thread information"""
        if self.current_thread:
            duration = datetime.datetime.now() - self.session_start_time
            print(f"📍 Current Thread ID: {self.current_thread.id}")
            print(f"⏱️ Session Duration: {duration}")
        else:
            print("❌ No active conversation thread")
    
    def safe_format_currency(self, value):
        """Safely format currency values, handling None and non-numeric values"""
        if value is None:
            return "₹0.00"
        try:
            return f"₹{float(value):,.2f}"
        except (ValueError, TypeError):
            return "₹0.00"
    
    def safe_format_number(self, value, default="N/A"):
        """Safely format numeric values, handling None values"""
        if value is None:
            return default
        try:
            return str(value)
        except (ValueError, TypeError):
            return default

    def get_ai_agent_analysis(self, analysis_prompt):
        """Get AI agent's professional analysis of customer data"""
        try:
            # Create message for AI analysis
            message = self.project_client.agents.create_message(
                thread_id=self.current_thread.id,
                role="user",
                content=analysis_prompt
            )

            # Process the message through the agent
            run = self.project_client.agents.create_and_process_run(
                thread_id=self.current_thread.id,
                agent_id=self.agent.id
            )
            
            # Get the latest messages
            messages = self.project_client.agents.list_messages(thread_id=self.current_thread.id)
            
            # Extract the response from text_messages
            if hasattr(messages, 'text_messages'):
                text_messages = list(messages.text_messages)
                
                if text_messages:
                    # Get the most recent message (should be the assistant's response)
                    latest_message = text_messages[0]  # Most recent is usually first
                    
                    # Extract the text value from MessageTextContent object
                    if hasattr(latest_message, 'text') and hasattr(latest_message.text, 'value'):
                        return latest_message.text.value
            
            return "Unable to generate AI analysis at this time."
            
        except Exception as e:
            return f"Error generating AI analysis: {str(e)}"

def main():
    """Main conversational loop for Credit Underwriting Agent"""
    print("=" * 80)
    print("🏦 CREDIT UNDERWRITING AGENT - Supervisory Assistant with Database Integration")
    print("=" * 80)
    print("Welcome! I'm your Credit Underwriting Agent with supervisory capabilities.")
    print("I specialize in credit assessment, risk analysis, and agent orchestration.")
    print("\n🔍 **AUTOMATED DATABASE INTEGRATION**: Complete customer analysis with zero manual input!")
    print("Example: 'Analyze customer CUST0006' - Retrieves ALL data automatically:")
    print("  • KYC Documents (PAN/Aadhaar status)")
    print("  • Income Verification (Salary/ITR/Form 16)")
    print("  • Bank Statements (3-6 months history)")
    print("  • Credit History (CIBIL score, loans)")
    print("  • Employment Details (status, tenure)")
    print("  • Complete Risk Assessment & Recommendations")
    print("\nType 'capabilities' to see what I can help you with.")
    print("Type 'new conversation' to start a fresh thread.")
    print("Type 'quit', 'exit', or 'bye' to end the session.")
    print("-" * 80)
    
    # Initialize the agent
    agent = CreditUnderwritingAgent()
    
    try:
        print("🔄 Initializing Credit Underwriting Agent...")
        if not agent.initialize_agent():
            print("❌ Failed to initialize agent. Exiting...")
            return
        
        print("🔄 Creating new conversation thread...")
        if not agent.create_new_thread():
            print("❌ Failed to create conversation thread. Exiting...")
            return
            
        print("✅ Credit Underwriting Agent ready for supervision and analysis!")
        
        if agent.db_connection:
            print("✅ Database connection established - Customer analysis available")
        else:
            print("⚠️ Database connection not available - Running in offline mode")
        
        print("\n" + "="*80)
        print("🎯 **USAGE EXAMPLES:**")
        print("• 'Analyze customer CUST0006' - Complete automated credit analysis")
        print("• 'Customer ID CUST0006' - Alternative format for customer analysis")
        print("• 'What is DTI ratio?' - General underwriting questions")
        print("• 'Risk assessment process' - Underwriting methodology")
        print("• 'Document requirements' - KYC and verification info")
        print("="*80 + "\n")
        
        while True:
            # Get user input
            user_input = input("You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                print("\n👋 Thank you for using the Credit Underwriting Agent. Session ended.")
                break
            
            # Skip empty inputs
            if not user_input:
                continue
            
            # Handle special commands
            if user_input.lower() == 'capabilities':
                agent.display_agent_capabilities()
                continue
            elif user_input.lower() == 'new conversation':
                print("🔄 Starting new conversation thread...")
                if agent.create_new_thread():
                    print("✅ New conversation started successfully!")
                continue
            elif user_input.lower() == 'thread info':
                agent.get_thread_info()
                continue
            elif user_input.lower() in ['db status', 'database status']:
                if agent.db_connection:
                    print("✅ Database connection: Active")
                    print("🔍 Customer analysis: Available")
                else:
                    print("❌ Database connection: Not available")
                    print("⚠️ Running in offline mode")
                continue
            
            try:
                # Get response from agent
                print("🤔 Analyzing and processing...")
                response = agent.get_agent_response(user_input)
                print(f"\n🏦 Credit Underwriting Agent:\n{response}\n")
                print("-" * 80)
                
            except Exception as e:
                print(f"❌ Error getting response: {str(e)}")
                print("Please try again with a different question.\n")
                
    except KeyboardInterrupt:
        print("\n\n👋 Session interrupted. Goodbye!")
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
        sys.exit(1)
    finally:
        # Clean up database connection
        if agent.db_connection:
            try:
                agent.db_connection.close()
                print("🔄 Database connection closed.")
            except:
                pass

if __name__ == "__main__":
    main()