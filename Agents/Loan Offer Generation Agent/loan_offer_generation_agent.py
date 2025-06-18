# pip install azure-ai-projects==1.0.0b10
# pip install pyodbc requests
import pyodbc
import json
import math
import requests
from datetime import datetime, timedelta
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Azure SQL Database connection configuration
SERVER = "global-trust-bank.database.windows.net"
DATABASE = "Global_Trust_Bank"
USERNAME = "Password_is_Pa_ss_12_3_add_at_inbetween_dont_include_underscore"
PASSWORD = "Pass@123"

# Loan Assessment Parameters
LOAN_PARAMETERS = {
    "HOME_LOAN": {
        "min_credit_score": 650,
        "max_ltv_ratio": 0.85,  # Loan to Value ratio
        "min_income_multiplier": 3.5,
        "max_tenure_years": 30,
        "base_interest_rate": 8.5,
        "processing_fee_percent": 0.5,
        "insurance_percent": 0.25
    },
    "INTEREST_RATE_FACTORS": {
        "credit_score_excellent": -0.5,  # 750+
        "credit_score_good": 0,          # 650-749
        "credit_score_fair": 0.5,        # 600-649
        "existing_customer": -0.25,
        "high_income": -0.25,            # Income > 100k
        "employment_stable": -0.25,      # Employment > 3 years
        "risk_category_low": -0.25,
        "risk_category_high": 0.75
    }
}

def get_azure_sql_connection():
    """
    Establishes connection to Azure SQL Database
    """
    try:
        # Check available drivers
        available_drivers = [driver for driver in pyodbc.drivers() if 'SQL Server' in driver]
        print(f"Available ODBC drivers: {available_drivers}")
        
        if not available_drivers:
            print("No SQL Server ODBC drivers found!")
            return None
        
        # Prefer newer drivers
        preferred_drivers = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server", 
            "SQL Server"
        ]
        
        driver = None
        for preferred in preferred_drivers:
            if preferred in available_drivers:
                driver = preferred
                break
        
        if not driver:
            driver = available_drivers[0]
            
        print(f"Using driver: {driver}")
        
        # Build connection string
        if "18" in driver:
            conn_str = f"Driver={{{driver}}};Server=tcp:{SERVER},1433;Database={DATABASE};Uid={USERNAME};Pwd={PASSWORD};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30;"
        else:
            conn_str = f"Driver={{{driver}}};Server=tcp:{SERVER},1433;Database={DATABASE};Uid={USERNAME};Pwd={PASSWORD};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        
        connection = pyodbc.connect(conn_str)
        print("Successfully connected to Azure SQL Database!")
        return connection
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error connecting to Azure SQL Database: {error_msg}")
        
        if "40615" in error_msg or "not allowed to access" in error_msg:
            print("\n🔥 FIREWALL ISSUE DETECTED 🔥")
            print("Please add your IP address to Azure SQL Server firewall rules.")
            
        return None

def get_customer_data(customer_id):
    """
    Retrieves comprehensive customer data for loan assessment
    """
    connection = get_azure_sql_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        
        # Comprehensive customer data query
        query = """
        SELECT 
            m.Customer_ID, m.Name, m.Age, m.Annual_Income_Range, m.Risk_Category,
            m.KYC_Status, m.Fraud_Flag, m.Customer_Since,
            e.Employment_Type, e.Employment_Status, e.Monthly_Income, e.Other_Income,
            e.Total_Monthly_Income, e.Work_Experience_Years, e.Employer_Name,
            b.Account_Balance, b.Average_Monthly_Balance, b.Account_Type,
            b.Customer_Category, b.Account_Status,
            l.Credit_Score, l.Loan_Status, l.Loan_Amount as Existing_Loan_Amount,
            l.EMI as Existing_EMI, l.Loan_Type as Existing_Loan_Type
        FROM Master_Customer_Data m
        LEFT JOIN Employment_Info e ON m.Customer_ID = e.Customer_ID
        LEFT JOIN Bank_Info b ON m.Customer_ID = b.Customer_ID
        LEFT JOIN Loan_Info l ON m.Customer_ID = l.Customer_ID
        WHERE m.Customer_ID = ?
        """
        
        cursor.execute(query, customer_id)
        result = cursor.fetchone()
        
        if not result:
            return None
        
        # Convert to dictionary
        columns = [column[0] for column in cursor.description]
        customer_data = dict(zip(columns, result))
        
        # Get transaction history for additional assessment
        transaction_query = """
        SELECT COUNT(*) as Transaction_Count,
               AVG(Amount) as Avg_Transaction_Amount,
               SUM(CASE WHEN Amount > 0 THEN Amount ELSE 0 END) as Total_Credits,
               SUM(CASE WHEN Amount < 0 THEN ABS(Amount) ELSE 0 END) as Total_Debits
        FROM Transaction_History 
        WHERE Customer_ID = ? AND Transaction_Date >= DATEADD(month, -6, GETDATE())
        """
        
        cursor.execute(transaction_query, customer_id)
        trans_result = cursor.fetchone()
        
        if trans_result:
            trans_columns = [column[0] for column in cursor.description]
            transaction_data = dict(zip(trans_columns, trans_result))
            customer_data.update(transaction_data)
        
        return customer_data
        
    except Exception as e:
        print(f"Error fetching customer data: {str(e)}")
        return None
    finally:
        connection.close()

def assess_loan_eligibility(customer_data, collateral_info, requested_loan_amount):
    """
    Comprehensive loan eligibility assessment
    """
    assessment = {
        "eligible": False,
        "reasons": [],
        "risk_factors": [],
        "positive_factors": [],
        "recommended_amount": 0,
        "max_eligible_amount": 0
    }
    
    # Basic eligibility checks
    if not customer_data:
        assessment["reasons"].append("Customer data not found")
        return assessment
    
    # Skip KYC and document verification - assume these are handled separately
    print("ℹ️  Note: KYC and document verification assumed to be completed separately")
    
    # Credit Score check
    credit_score = customer_data.get("Credit_Score", 0) or 0
    if credit_score < LOAN_PARAMETERS["HOME_LOAN"]["min_credit_score"]:
        assessment["reasons"].append(f"Credit score {credit_score} below minimum {LOAN_PARAMETERS['HOME_LOAN']['min_credit_score']}")
        return assessment
    
    # Income verification
    monthly_income = customer_data.get("Total_Monthly_Income", 0) or customer_data.get("Monthly_Income", 0) or 0
    if monthly_income <= 0:
        assessment["reasons"].append("Income information not available")
        return assessment
    
    # Calculate maximum eligible amount based on income
    max_emi = monthly_income * 0.4  # 40% of income as max EMI
    tenure_months = LOAN_PARAMETERS["HOME_LOAN"]["max_tenure_years"] * 12
    base_rate = LOAN_PARAMETERS["HOME_LOAN"]["base_interest_rate"] / 100 / 12
    
    # Calculate max loan amount based on EMI capacity
    max_loan_by_income = max_emi * ((1 - (1 + base_rate) ** -tenure_months) / base_rate)
    
    # Calculate max loan based on collateral (LTV ratio)
    property_value = collateral_info.get("property_value", 0)
    max_loan_by_ltv = property_value * LOAN_PARAMETERS["HOME_LOAN"]["max_ltv_ratio"]
    
    # Maximum eligible amount is minimum of both
    max_eligible = min(max_loan_by_income, max_loan_by_ltv)
    assessment["max_eligible_amount"] = max_eligible
    
    # Check if requested amount is within limits
    if requested_loan_amount > max_eligible:
        assessment["reasons"].append(f"Requested amount ₹{requested_loan_amount:,.2f} exceeds maximum eligible ₹{max_eligible:,.2f}")
        assessment["recommended_amount"] = max_eligible * 0.9  # Recommend 90% of max
    else:
        assessment["eligible"] = True
        assessment["recommended_amount"] = requested_loan_amount
    
    # Risk assessment - these are informational, not blocking
    risk_category = customer_data.get("Risk_Category", "").upper()
    if risk_category == "HIGH":
        assessment["risk_factors"].append("High risk customer category")
    elif risk_category == "LOW":
        assessment["positive_factors"].append("Low risk customer category")
    
    # Employment stability
    work_experience = customer_data.get("Work_Experience_Years", 0) or 0
    if work_experience >= 3:
        assessment["positive_factors"].append(f"Stable employment ({work_experience} years)")
    else:
        assessment["risk_factors"].append(f"Limited work experience ({work_experience} years)")
    
    # Existing customer relationship
    if customer_data.get("Customer_Since"):
        assessment["positive_factors"].append("Existing customer relationship")
    
    # Account balance and banking behavior
    account_balance = customer_data.get("Account_Balance", 0) or 0
    avg_balance = customer_data.get("Average_Monthly_Balance", 0) or 0
    
    if account_balance >= monthly_income * 3:
        assessment["positive_factors"].append("Strong account balance")
    elif account_balance < monthly_income:
        assessment["risk_factors"].append("Low account balance")
    
    # Additional positive factors for better assessment
    if credit_score >= 750:
        assessment["positive_factors"].append("Excellent credit score")
    elif credit_score >= 700:
        assessment["positive_factors"].append("Good credit score")
    
    if monthly_income >= 100000:
        assessment["positive_factors"].append("High monthly income")
    elif monthly_income >= 50000:
        assessment["positive_factors"].append("Good monthly income")
    
    # If no major blocking issues and we have income + credit score, approve
    if monthly_income > 0 and credit_score >= LOAN_PARAMETERS["HOME_LOAN"]["min_credit_score"]:
        assessment["eligible"] = True
        if not assessment["recommended_amount"]:
            assessment["recommended_amount"] = min(requested_loan_amount, max_eligible)
    
    return assessment

def calculate_interest_rate(customer_data, base_rate=8.5):
    """
    Calculate personalized interest rate based on customer profile
    """
    final_rate = base_rate
    rate_factors = []
    
    # Credit score adjustments
    credit_score = customer_data.get("Credit_Score", 0) or 0
    if credit_score >= 750:
        adjustment = LOAN_PARAMETERS["INTEREST_RATE_FACTORS"]["credit_score_excellent"]
        final_rate += adjustment
        rate_factors.append(f"Excellent credit score ({credit_score}): {adjustment:+.2f}%")
    elif credit_score >= 650:
        adjustment = LOAN_PARAMETERS["INTEREST_RATE_FACTORS"]["credit_score_good"]
        final_rate += adjustment
        rate_factors.append(f"Good credit score ({credit_score}): {adjustment:+.2f}%")
    elif credit_score > 0:  # Only apply fair credit if we have a score
        adjustment = LOAN_PARAMETERS["INTEREST_RATE_FACTORS"]["credit_score_fair"]
        final_rate += adjustment
        rate_factors.append(f"Fair credit score ({credit_score}): {adjustment:+.2f}%")
    else:
        rate_factors.append("Credit score not available - using base rate")
    
    # Existing customer benefit
    if customer_data.get("Customer_Since"):
        adjustment = LOAN_PARAMETERS["INTEREST_RATE_FACTORS"]["existing_customer"]
        final_rate += adjustment
        rate_factors.append(f"Existing customer: {adjustment:+.2f}%")
    
    # High income benefit
    monthly_income = customer_data.get("Total_Monthly_Income", 0) or customer_data.get("Monthly_Income", 0) or 0
    if monthly_income > 100000:
        adjustment = LOAN_PARAMETERS["INTEREST_RATE_FACTORS"]["high_income"]
        final_rate += adjustment
        rate_factors.append(f"High income: {adjustment:+.2f}%")
    
    # Employment stability
    work_experience = customer_data.get("Work_Experience_Years", 0) or 0
    if work_experience >= 3:
        adjustment = LOAN_PARAMETERS["INTEREST_RATE_FACTORS"]["employment_stable"]
        final_rate += adjustment
        rate_factors.append(f"Stable employment: {adjustment:+.2f}%")
    
    # Risk category
    risk_category = customer_data.get("Risk_Category", "").upper()
    if risk_category == "LOW":
        adjustment = LOAN_PARAMETERS["INTEREST_RATE_FACTORS"]["risk_category_low"]
        final_rate += adjustment
        rate_factors.append(f"Low risk category: {adjustment:+.2f}%")
    elif risk_category == "HIGH":
        adjustment = LOAN_PARAMETERS["INTEREST_RATE_FACTORS"]["risk_category_high"]
        final_rate += adjustment
        rate_factors.append(f"High risk category: {adjustment:+.2f}%")
    
    # Ensure we have at least one rate factor
    if not rate_factors:
        rate_factors.append("Standard rate applied - limited customer data available")
    
    return max(final_rate, 7.0), rate_factors  # Minimum 7% rate

def calculate_loan_details(loan_amount, interest_rate, tenure_years):
    """
    Calculate detailed loan terms including EMI, total payment, etc.
    """
    monthly_rate = interest_rate / 100 / 12
    tenure_months = tenure_years * 12
    
    # EMI calculation using formula: P * r * (1+r)^n / ((1+r)^n - 1)
    emi = loan_amount * monthly_rate * (1 + monthly_rate) ** tenure_months / ((1 + monthly_rate) ** tenure_months - 1)
    
    total_payment = emi * tenure_months
    total_interest = total_payment - loan_amount
    
    # Processing fee and insurance
    processing_fee = loan_amount * LOAN_PARAMETERS["HOME_LOAN"]["processing_fee_percent"] / 100
    insurance_premium = loan_amount * LOAN_PARAMETERS["HOME_LOAN"]["insurance_percent"] / 100
    
    return {
        "loan_amount": loan_amount,
        "interest_rate": interest_rate,
        "tenure_months": tenure_months,
        "tenure_years": tenure_years,
        "emi": emi,
        "total_payment": total_payment,
        "total_interest": total_interest,
        "processing_fee": processing_fee,
        "insurance_premium": insurance_premium,
        "total_upfront_cost": processing_fee + insurance_premium
    }

def generate_loan_offer(customer_id, collateral_json, requested_amount=None):
    """
    Main function to generate comprehensive loan offer
    """
    print("\n" + "="*80)
    print("🏦 GLOBAL TRUST BANK - HOME LOAN ASSESSMENT")
    print("="*80)
    
    # Parse collateral information
    try:
        if isinstance(collateral_json, str):
            collateral_info = json.loads(collateral_json)
        else:
            collateral_info = collateral_json
    except:
        print("❌ Error: Invalid collateral JSON format")
        return None
    
    print(f"📋 Customer ID: {customer_id}")
    print(f"🏠 Property Value: ₹{collateral_info.get('property_value', 0):,.2f}")
    print(f"💰 Requested Amount: ₹{requested_amount:,.2f}" if requested_amount else "💰 Calculating maximum eligible amount...")
    
    # Get customer data
    print("\n🔍 Fetching customer data...")
    customer_data = get_customer_data(customer_id)
    
    if not customer_data:
        print("❌ Customer not found or error fetching data")
        return None
    
    print(f"✅ Customer found: {customer_data.get('Name', 'Unknown')}")
    
    # If no requested amount, calculate maximum eligible
    if not requested_amount:
        # Quick calculation for max amount
        monthly_income = customer_data.get("Total_Monthly_Income", 0) or customer_data.get("Monthly_Income", 0) or 0
        max_emi = monthly_income * 0.4
        base_rate = LOAN_PARAMETERS["HOME_LOAN"]["base_interest_rate"] / 100 / 12
        tenure_months = LOAN_PARAMETERS["HOME_LOAN"]["max_tenure_years"] * 12
        max_by_income = max_emi * ((1 - (1 + base_rate) ** -tenure_months) / base_rate)
        max_by_ltv = collateral_info.get("property_value", 0) * LOAN_PARAMETERS["HOME_LOAN"]["max_ltv_ratio"]
        requested_amount = min(max_by_income, max_by_ltv) * 0.9
      # Assess eligibility
    print("\n🔍 Assessing loan eligibility...")
    eligibility = assess_loan_eligibility(customer_data, collateral_info, requested_amount)
    
    # Even if not fully eligible, try to provide alternative offers
    if not eligibility["eligible"] and eligibility["reasons"]:
        print("\n⚠️  LOAN ASSESSMENT RESULTS")
        print("Issues identified:")
        for reason in eligibility["reasons"]:
            print(f"  • {reason}")
        
        # If we have a recommended amount, proceed with that
        if eligibility["recommended_amount"] > 0:
            print(f"\n💡 Alternative offer available for ₹{eligibility['recommended_amount']:,.2f}")
            print("Proceeding with alternative loan assessment...")
        else:
            print("\n❌ Unable to provide loan offer at this time")
            return None
    elif eligibility["eligible"]:
        print("✅ Customer is eligible for the requested loan amount")
      # Use recommended amount if available, otherwise use requested amount
    final_amount = eligibility["recommended_amount"] if eligibility["recommended_amount"] > 0 else requested_amount
    
    # Calculate interest rate
    print("\n💹 Calculating personalized interest rate...")
    final_rate, rate_factors = calculate_interest_rate(customer_data)
    
    # Calculate loan details for different tenure options
    tenure_options = [15, 20, 25, 30]
    loan_options = []
    
    for tenure in tenure_options:
        if tenure <= LOAN_PARAMETERS["HOME_LOAN"]["max_tenure_years"]:
            loan_details = calculate_loan_details(final_amount, final_rate, tenure)
            loan_options.append(loan_details)
    
    # Generate AI-powered loan offer summary
    offer_summary = generate_ai_loan_summary(customer_data, collateral_info, loan_options[2], eligibility, rate_factors)  # Use 25-year option for summary
    
    # Display comprehensive loan offer
    display_loan_offer(customer_data, collateral_info, loan_options, eligibility, rate_factors, offer_summary)
    
    return {
        "customer_data": customer_data,
        "eligibility": eligibility,
        "loan_options": loan_options,
        "final_rate": final_rate,
        "rate_factors": rate_factors,
        "offer_summary": offer_summary
    }

def generate_ai_loan_summary(customer_data, collateral_info, loan_details, eligibility, rate_factors):
    """
    Generate AI-powered loan offer summary and recommendations
    """
    try:
        # Initialize AI client
        project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str="eastus2.api.azureml.ms;aee23923-3bba-468d-8dcd-7c4bc1ce218f;rg-ronakofficial1414-9323_ai;ronakofficial1414-8644")
        
        agent = project_client.agents.get_agent("asst_UViec1zMTXPMHlyzawp0lei2")
        thread = project_client.agents.create_thread()
        
        # Prepare data for AI analysis
        customer_summary = f"""
        Customer: {customer_data.get('Name', 'N/A')}
        Age: {customer_data.get('Age', 'N/A')}
        Monthly Income: ₹{customer_data.get('Total_Monthly_Income', 0):,.2f}
        Credit Score: {customer_data.get('Credit_Score', 'N/A')}
        Employment: {customer_data.get('Employment_Type', 'N/A')} - {customer_data.get('Work_Experience_Years', 'N/A')} years
        Risk Category: {customer_data.get('Risk_Category', 'N/A')}
        Account Balance: ₹{customer_data.get('Account_Balance', 0):,.2f}
        """
        
        loan_summary = f"""
        Property Value: ₹{collateral_info.get('property_value', 0):,.2f}
        Loan Amount: ₹{loan_details['loan_amount']:,.2f}
        Interest Rate: {loan_details['interest_rate']:.2f}%
        EMI: ₹{loan_details['emi']:,.2f}
        Tenure: {loan_details['tenure_years']} years
        Total Payment: ₹{loan_details['total_payment']:,.2f}
        """
        ai_prompt = f"""As RDJ, a senior loan officer at Global Trust Bank, provide a professional loan offer summary for this home loan application:

{customer_summary}

{loan_summary}

Eligibility Factors:
- Positive: {', '.join(eligibility['positive_factors'])}
- Risk Factors: {', '.join(eligibility['risk_factors'])}

Interest Rate Factors:
{chr(10).join(rate_factors)}

Please provide:
1. Executive Summary of the loan offer
2. Key benefits for the customer
3. Risk mitigation strategies
4. Recommendations for loan terms
5. Next steps for the customer

Sign off as "RDJ, Senior Loan Officer". Keep it professional but customer-friendly, highlighting the value proposition."""
        
        message = project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=ai_prompt
        )
        
        run = project_client.agents.create_and_process_run(
            thread_id=thread.id,
            agent_id=agent.id)
        
        messages = project_client.agents.list_messages(thread_id=thread.id)
        
        # Get AI response
        for message in messages.data:
            if message.role == "assistant":
                for content in message.content:
                    if hasattr(content, 'text'):
                        return content.text.value
        
        return "AI summary not available"
        
    except Exception as e:
        return f"AI summary error: {str(e)}"

def display_loan_offer(customer_data, collateral_info, loan_options, eligibility, rate_factors, ai_summary):
    """
    Display comprehensive loan offer and send email
    """
    print("\n" + "="*80)
    print("🎉 LOAN OFFER APPROVED!")
    print("="*80)
    
    print(f"\n👤 CUSTOMER DETAILS:")
    print(f"   Name: {customer_data.get('Name', 'N/A')}")
    print(f"   Customer ID: {customer_data.get('Customer_ID', 'N/A')}")
    print(f"   Credit Score: {customer_data.get('Credit_Score', 'N/A')}")
    print(f"   Monthly Income: ₹{customer_data.get('Total_Monthly_Income', 0):,.2f}")
    print(f"   Employment: {customer_data.get('Employment_Type', 'N/A')}")
    
    print(f"\n🏠 PROPERTY DETAILS:")
    print(f"   Property Value: ₹{collateral_info.get('property_value', 0):,.2f}")
    print(f"   Property Type: {collateral_info.get('property_type', 'Residential')}")
    print(f"   Location: {collateral_info.get('location', 'N/A')}")
    
    print(f"\n💰 LOAN OPTIONS:")
    print("─" * 80)
    print(f"{'Tenure':<8} {'Loan Amount':<15} {'Interest Rate':<13} {'EMI':<15} {'Total Payment':<15}")
    print("─" * 80)
    
    for option in loan_options:
        print(f"{option['tenure_years']:<8} ₹{option['loan_amount']:>12,.0f} {option['interest_rate']:>11.2f}% ₹{option['emi']:>13,.0f} ₹{option['total_payment']:>13,.0f}")
    
    print("\n📊 INTEREST RATE BREAKDOWN:")
    print(f"   Base Rate: {LOAN_PARAMETERS['HOME_LOAN']['base_interest_rate']:.2f}%")
    for factor in rate_factors:
        print(f"   {factor}")
    print(f"   Final Rate: {loan_options[0]['interest_rate']:.2f}%")
    
    print(f"\n💳 ADDITIONAL COSTS:")
    print(f"   Processing Fee: ₹{loan_options[0]['processing_fee']:,.2f}")
    print(f"   Insurance Premium: ₹{loan_options[0]['insurance_premium']:,.2f}")
    print(f"   Total Upfront Cost: ₹{loan_options[0]['total_upfront_cost']:,.2f}")
    
    print(f"\n✅ POSITIVE FACTORS:")
    for factor in eligibility['positive_factors']:
        print(f"   • {factor}")
    
    if eligibility['risk_factors']:
        print(f"\n⚠️  RISK FACTORS:")
        for factor in eligibility['risk_factors']:
            print(f"   • {factor}")
    
    print(f"\n🤖 AI LOAN OFFICER SUMMARY:")
    print("─" * 80)
    print(ai_summary)
    print("─" * 80)
    
    print(f"\n📋 NEXT STEPS:")
    print("   1. Submit required documents")
    print("   2. Property valuation by bank-approved valuers")
    print("   3. Legal verification of property documents")
    print("   4. Final loan approval and disbursement")
    
    print(f"\n⏰ OFFER VALIDITY: 30 days from {datetime.now().strftime('%d-%m-%Y')}")
    print("="*80)
    
    # Send email via Logic App
    email_body = format_loan_offer_email(customer_data, collateral_info, loan_options, eligibility, rate_factors, ai_summary)
    customer_id = customer_data.get('Customer_ID', 'Unknown')
    
    # Send email
    email_sent = send_loan_offer_email(customer_id, email_body)
    
    if email_sent:
        print("\n✅ Loan offer email has been sent to the customer!")
    else:
        print("\n⚠️  Loan offer displayed locally. Email sending encountered an issue.")
    
    print("="*80)

def send_loan_offer_email(customer_id, email_body):
    """
    Send loan offer email to Logic App
    """
    logic_app_url = "https://demo1414.azurewebsites.net:443/api/agent/triggers/When_a_HTTP_request_is_received/invoke?api-version=2022-05-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=HZ0I3n6VpNoP0Ijw691jeFXYwOcT6OtQhJopwfpYvn4"
    
    payload = {
        "customer_id": customer_id,
        "stage": "email",
        "email_body": email_body,
        "condition": "approved"
    }
    
    try:
        print("\n📧 Sending loan offer email via Logic App...")
        response = requests.post(logic_app_url, json=payload, timeout=30)
        
        if response.status_code == 200 or response.status_code == 202:
            print("✅ Email sent successfully via Logic App!")
            return True
        else:
            print(f"⚠️  Email sending failed. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⚠️  Email sending timed out. The email may still be processed.")
        return False
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return False

def format_loan_offer_email(customer_data, collateral_info, loan_options, eligibility, rate_factors, ai_summary):
    """
    Format the loan offer as an HTML email body
    """
    # Clean up AI summary - remove markdown formatting and keep only relevant parts
    clean_ai_summary = ai_summary.replace("**", "").replace("###", "").replace("##", "").replace("#", "")
    clean_ai_summary = clean_ai_summary.replace("*", "").replace("---", "")
    
    email_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Home Loan Offer - Global Trust Bank</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background-color: #f9f9f9; }}
        .email-container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; margin: -30px -30px 30px -30px; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .approval-badge {{ background-color: #28a745; color: white; padding: 10px 20px; border-radius: 20px; display: inline-block; margin: 20px 0; font-weight: bold; }}
        .section {{ margin: 25px 0; }}
        .section-title {{ color: #1e3c72; font-size: 18px; font-weight: bold; margin-bottom: 15px; padding-bottom: 5px; border-bottom: 2px solid #e0e0e0; }}
        .details-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 15px 0; }}
        .detail-item {{ padding: 10px; background-color: #f8f9fa; border-left: 4px solid #1e3c72; }}
        .detail-label {{ font-weight: bold; color: #1e3c72; }}
        .detail-value {{ color: #333; }}
        .loan-options-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        .loan-options-table th, .loan-options-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .loan-options-table th {{ background-color: #1e3c72; color: white; }}
        .loan-options-table tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .ai-summary {{ background-color: #e8f4f8; padding: 20px; border-radius: 8px; border-left: 4px solid #17a2b8; margin: 15px 0; font-style: italic; }}
        .next-steps {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; }}
        .next-steps ol {{ margin: 0; padding-left: 20px; }}
        .next-steps li {{ margin: 8px 0; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 2px solid #e0e0e0; text-align: center; color: #666; }}
        .signature {{ margin: 20px 0; }}
        .contact-info {{ background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .validity {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .recommended-option {{ background-color: #e8f5e8; border: 2px solid #28a745; }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>GLOBAL TRUST BANK</h1>
            <h2>HOME LOAN OFFER</h2>
        </div>
        
        <p>Dear <strong>{customer_data.get('Name', 'Valued Customer')}</strong>,</p>
        
        <div class="approval-badge">
            LOAN APPLICATION APPROVED
        </div>
        
        <p>We are pleased to inform you that your home loan application has been <strong>APPROVED</strong>!</p>
        
        <div class="section">
            <div class="section-title">Customer Details</div>
            <div class="details-grid">
                <div class="detail-item">
                    <div class="detail-label">Name:</div>
                    <div class="detail-value">{customer_data.get('Name', 'N/A')}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Customer ID:</div>
                    <div class="detail-value">{customer_data.get('Customer_ID', 'N/A')}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Credit Score:</div>
                    <div class="detail-value">{customer_data.get('Credit_Score', 'N/A')}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Monthly Income:</div>
                    <div class="detail-value">₹{customer_data.get('Total_Monthly_Income', 0):,.2f}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Employment:</div>
                    <div class="detail-value">{customer_data.get('Employment_Type', 'N/A')}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">Property Details</div>
            <div class="details-grid">
                <div class="detail-item">
                    <div class="detail-label">Property Value:</div>
                    <div class="detail-value">₹{collateral_info.get('property_value', 0):,.2f}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Property Type:</div>
                    <div class="detail-value">{collateral_info.get('property_type', 'Residential')}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Location:</div>
                    <div class="detail-value">{collateral_info.get('location', 'N/A')}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">Loan Options</div>
            <table class="loan-options-table">
                <thead>
                    <tr>
                        <th>Tenure (Years)</th>
                        <th>Loan Amount</th>
                        <th>Interest Rate</th>
                        <th>Monthly EMI</th>
                        <th>Total Payment</th>
                    </tr>
                </thead>
                <tbody>"""

    for option in loan_options:
        row_class = "recommended-option" if option['tenure_years'] == 25 else ""
        email_body += f"""
                    <tr class="{row_class}">
                        <td>{option['tenure_years']}</td>
                        <td>₹{option['loan_amount']:,.0f}</td>
                        <td>{option['interest_rate']:.2f}%</td>
                        <td>₹{option['emi']:,.0f}</td>
                        <td>₹{option['total_payment']:,.0f}</td>
                    </tr>"""

    email_body += f"""
                </tbody>
            </table>
            <p><small><em>Note: The highlighted option (25 years) is our recommended tenure for optimal balance between EMI affordability and total cost.</em></small></p>
        </div>
        
        <div class="section">
            <div class="section-title">Additional Costs</div>
            <div class="details-grid">
                <div class="detail-item">
                    <div class="detail-label">Processing Fee:</div>
                    <div class="detail-value">₹{loan_options[0]['processing_fee']:,.2f}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Insurance Premium:</div>
                    <div class="detail-value">₹{loan_options[0]['insurance_premium']:,.2f}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Total Upfront Cost:</div>
                    <div class="detail-value" style="font-weight: bold;">₹{loan_options[0]['total_upfront_cost']:,.2f}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">Loan Officer Summary</div>
            <div class="ai-summary">
                {clean_ai_summary.replace(chr(10), '<br>')}
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">Next Steps</div>
            <div class="next-steps">
                <ol>
                    <li>Submit required documents</li>
                    <li>Property valuation by bank-approved valuers</li>
                    <li>Legal verification of property documents</li>
                    <li>Final loan approval and disbursement</li>
                </ol>
            </div>
        </div>
        
        <div class="validity">
            <strong>OFFER VALIDITY:</strong> 30 days from {datetime.now().strftime('%d-%m-%Y')}
        </div>
        
        <div class="footer">
            <div class="signature">
                <p><strong>Best Regards,</strong></p>
                <p><strong>RDJ</strong><br>
                Senior Loan Officer<br>
                Global Trust Bank</p>
            </div>
            
            <div class="contact-info">
                <strong>Contact Information:</strong><br>
                Email: loans@globaltrustbank.com<br>
                Phone: +91-11-4567-8900
            </div>
            
            <p><small>This is an automated loan offer generated by Global Trust Bank's AI-powered loan assessment system.</small></p>
        </div>
    </div>
</body>
</html>
"""    
    return email_body

def main():
    """
    Main function to run the Loan Assessment Agent
    """
    print("🏦 GLOBAL TRUST BANK - HOME LOAN ASSESSMENT AGENT")
    print("="*60)
    
    while True:
        print("\n🔍 Loan Assessment Options:")
        print("1. Assess loan for Customer ID with collateral")
        print("2. Quick eligibility check")
        print("3. Exit")
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == "1":
            customer_id = input("\n📋 Enter Customer ID: ").strip()
            
            print("\n🏠 Enter Collateral Information:")
            print("Example: {'property_value': 5000000, 'property_type': 'Apartment', 'location': 'Mumbai'}")
            
            collateral_input = input("Collateral JSON: ").strip()
            
            requested_amount_input = input("💰 Requested Loan Amount (press Enter for maximum eligible): ").strip()
            requested_amount = float(requested_amount_input) if requested_amount_input else None
            
            if customer_id and collateral_input:
                generate_loan_offer(customer_id, collateral_input, requested_amount)
            else:
                print("❌ Please provide valid Customer ID and collateral information")
        
        elif choice == "2":
            customer_id = input("\n📋 Enter Customer ID for quick check: ").strip()
            if customer_id:
                customer_data = get_customer_data(customer_id)
                if customer_data:
                    print(f"\n✅ Customer: {customer_data.get('Name', 'N/A')}")
                    print(f"   Credit Score: {customer_data.get('Credit_Score', 'N/A')}")
                    print(f"   Monthly Income: ₹{customer_data.get('Total_Monthly_Income', 0):,.2f}")
                    print(f"   Risk Category: {customer_data.get('Risk_Category', 'N/A')}")
                    
                    # Quick eligibility estimate
                    monthly_income = customer_data.get('Total_Monthly_Income', 0) or 0
                    if monthly_income > 0:
                        max_emi = monthly_income * 0.4
                        estimated_max_loan = max_emi * 240  # Rough estimate for 20 years
                        print(f"   Estimated Max Loan: ₹{estimated_max_loan:,.2f}")
                else:
                    print("❌ Customer not found")
        
        elif choice == "3":
            print("👋 Thank you for using Global Trust Bank Loan Assessment Agent!")
            break
        
        else:
            print("❌ Invalid option. Please select 1, 2, or 3.")

if __name__ == "__main__":
    main()
