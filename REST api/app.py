import streamlit as st
import requests
from datetime import datetime

# Configure the page
st.set_page_config(
    page_title="Loan Processing Portal",
    page_icon="🏦",
    layout="wide"
)

# Custom CSS for basic styling
st.markdown("""
    <style>
    .card {
        padding: 20px;
        border-radius: 10px;
        background-color: #f8f9fa;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .message {
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 10px;
        max-width: 85%;
    }
    .user-message {
        background-color: #e1ffc7;
        margin-left: auto;
    }
    .assistant-message {
        background-color: #f1f1f1;
        margin-right: auto;
    }
    </style>
""", unsafe_allow_html=True)

BASE_URL = "http://localhost:8000"

# Initialize all session state variables
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'show_chat' not in st.session_state:
    st.session_state.show_chat = False
if 'chat_input' not in st.session_state:
    st.session_state.chat_input = ""

# Simple navigation with tabs
tabs = st.tabs([
    "🏠 Home",
    "📝 Apply for Loan",
    "🔍 View Loan Details", 
    "✉️ Submit Loan",
    "✅ Loan Decisions",
    "🤖 AI Assistant"
])

# 1. Home Tab
with tabs[0]:
    st.markdown("### 👋 Welcome to the Loan Processing Portal")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("""
    This portal allows you to:
    * 📝 Submit new loan applications
    * 🔍 View existing applications
    * ✅ Submit applications for review
    * 📋 Make decisions on loan applications
    * 🤖 Get AI assistance
    
    Use the tabs above to navigate through different features.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Show sample loan application process
    st.markdown("### How It Works")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 1. Apply")
        st.write("Fill out the loan form")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 2. Submit")
        st.write("Submit for review")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 3. Review")
        st.write("Wait for processing")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 4. Decision")
        st.write("Get your result")
        st.markdown('</div>', unsafe_allow_html=True)

# 2. Apply for Loan Tab
with tabs[1]:
    st.header("📝 Apply for Loan")
    with st.form("loan_application_form"):
        applicant_name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        employment_type = st.selectbox("Employment Type", 
            ["Salaried", "Self-Employed", "Business Owner", "Other"],
            key="apply_employment"
        )
        monthly_income = st.number_input("Monthly Income ($)", 
            min_value=0.0, 
            step=100.0,
            key="apply_income"
        )
        loan_amount = st.number_input("Loan Amount ($)", 
            min_value=1000.0, 
            step=500.0,
            key="apply_amount"
        )
        loan_term = st.number_input("Loan Term (Months)", 
            min_value=1, 
            max_value=360,
            key="apply_term"
        )
        loan_purpose = st.text_area("Loan Purpose")
        submitted = st.form_submit_button("Submit Application")
        
        if submitted:
            if all([applicant_name, email, phone, loan_amount, loan_purpose]):
                data = {
                    "applicant_name": applicant_name,
                    "email": email,
                    "phone": phone,
                    "employment_type": employment_type,
                    "monthly_income": monthly_income,
                    "loan_amount": loan_amount,
                    "loan_term_months": loan_term,
                    "loan_purpose": loan_purpose
                }
                response = requests.post(f"{BASE_URL}/api/loan/apply", json=data)
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ Application submitted successfully! Your loan ID is: {result['id']}")
                else:
                    st.error(f"Error: {response.json()['detail']}")
            else:
                st.warning("Please fill all required fields")

# 3. View Loan Details Tab
with tabs[2]:
    st.header("🔍 View Loan Details")
    view_id = st.number_input("Enter Loan ID", min_value=1, step=1, key="view_loan_details_id")
    if st.button("View Details", key="view_details_btn"):
        response = requests.get(f"{BASE_URL}/api/loan/{view_id}")
        if response.status_code == 200:
            loan_data = response.json()
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Applicant Information")
                st.write(f"**Name:** {loan_data['applicant_name']}")
                st.write(f"**Email:** {loan_data['email']}")
                st.write(f"**Phone:** {loan_data['phone']}")
                st.write(f"**Employment:** {loan_data['employment_type']}")
            
            with col2:
                st.markdown("### Loan Details")
                st.write(f"**Amount:** ${loan_data['loan_amount']:,.2f}")
                st.write(f"**Term:** {loan_data['loan_term_months']} months")
                st.write(f"**Status:** {loan_data['status']}")
                st.write(f"**Purpose:** {loan_data['loan_purpose']}")
            
            if loan_data['status'] == 'REJECTED' and loan_data.get('rejection_reason'):
                st.error(f"**Rejection Reason:** {loan_data['rejection_reason']}")
        else:
            st.error(f"Error: {response.json()['detail']}")

# 4. Submit Loan Tab
with tabs[3]:
    st.header("✉️ Submit Loan for Review")
    submit_id = st.number_input("Enter Loan ID", min_value=1, step=1, key="submit_review_id")
    if st.button("Submit for Review", key="submit_review_btn"):     
        response = requests.post(f"{BASE_URL}/api/loan/{submit_id}/submit")
        if response.status_code == 200:
            st.success("✅ Loan application submitted for review!")
            loan_response = requests.get(f"{BASE_URL}/api/loan/{submit_id}")
            if loan_response.status_code == 200:
                loan_data = loan_response.json()
                st.info(f"Current Status: {loan_data['status']}")
        else:
            st.error(f"Error: {response.json()['detail']}")

# 5. Loan Decisions Tab
with tabs[4]:
    st.header("✅ Loan Decisions")
    loan_id = st.number_input("Enter Loan ID", min_value=1, step=1, key="decision_loan_id")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("View Application", key="view_for_decision_btn"):
            response = requests.get(f"{BASE_URL}/api/loan/{loan_id}")
            if response.status_code == 200:
                loan_data = response.json()
                st.markdown("### Application Details")
                st.write(f"**Applicant:** {loan_data['applicant_name']}")
                st.write(f"**Amount:** ${loan_data['loan_amount']:,.2f}")
                st.write(f"**Purpose:** {loan_data['loan_purpose']}")
                st.write(f"**Status:** {loan_data['status']}")
            else:
                st.error("Loan not found")    
    with col2:
        st.markdown("### Actions")
        if st.button("Approve", key="approve_btn", type="primary"):
            response = requests.post(f"{BASE_URL}/api/loan/{loan_id}/approve")
            if response.status_code == 200:
                result = response.json()
                loan_details = result.get('loan_details', {})
                st.success("✅ Loan application approved!")
                st.markdown("### Approval Details")
                st.write(f"**Applicant:** {loan_details.get('applicant_name', 'N/A')}")
                st.write(f"**Amount:** ${loan_details.get('loan_amount', 0):,.2f}")
                st.write(f"**Status:** {loan_details.get('status', 'APPROVED')}")
                st.write(f"**Approved at:** {loan_details.get('approved_at', 'N/A')}")
        
        rejection_reason = st.text_area("Rejection Reason", key="reject_reason")
        if st.button("Reject", key="reject_btn"):
            if rejection_reason:
                response = requests.post(
                    f"{BASE_URL}/api/loan/{loan_id}/reject",
                    json={"rejection_reason": rejection_reason}
                )
                if response.status_code == 200:
                    result = response.json()
                    loan_details = result.get('loan_details', {})
                    st.error("❌ Loan application rejected")
                    st.markdown("### Rejection Details")
                    st.write(f"**Applicant:** {loan_details.get('applicant_name', 'N/A')}")
                    st.write(f"**Amount:** ${loan_details.get('loan_amount', 0):,.2f}")
                    st.write(f"**Status:** {loan_details.get('status', 'REJECTED')}")
                    st.write(f"**Reason:** {loan_details.get('rejection_reason', 'N/A')}")
                    st.write(f"**Rejected at:** {loan_details.get('rejected_at', 'N/A')}")
            else:
                st.warning("⚠️ Please provide a rejection reason")

# 6. AI Assistant Tab
with tabs[5]:
    st.header("🤖 AI Loan Assistant")
    
    # Display chat history
    for msg in st.session_state.chat_messages:
        div_class = "user-message" if msg["role"] == "user" else "assistant-message"
        st.markdown(f'<div class="message {div_class}">{msg["content"]}</div>', unsafe_allow_html=True)
    
    # Example commands
    with st.expander("💡 Example commands"):
        st.markdown("""
        **New Application**
        ```
        Apply for a $25000 home loan with 12 month term, 
        email: john@example.com, phone: 1234567890, 
        monthly income: $5000, employment type: Salaried
        ```
        
        **Check Application**
        ```
        View loan 13
        Submit loan 13
        Check status of loan 13
        ```
        """)
      # Chat input
    user_input = st.text_area("Type your message...", key="ai_chat_input")
    if st.button("Send", key="ai_send_btn"):
        if user_input:
            # Add user message
            st.session_state.chat_messages.append({
                "role": "user",
                "content": user_input
            })
            
            # Call AI agent
            try:
                response = requests.post(
                    "http://localhost:8001/agent",
                    json={"instruction": user_input}
                )
                if response.status_code == 200:
                    result = response.json()
                    response_data = result.get("response", {})

                    if isinstance(response_data, dict):
                        if "detail" in response_data:
                            error_msg = response_data["detail"]
                            if "not recognized" in error_msg.lower():
                                # Handle unrecognized instructions more naturally
                                assistant_message = """👋 I understand you're trying to interact with me. I can help you with:
                                
• Applying for new loans
• Checking loan status and details
• Submitting applications
• Understanding loan requirements
• Answering your questions about the process

What would you like to know about?"""
                            elif "must be in SUBMITTED state" in error_msg.lower():
                                assistant_message = """I notice you're trying to take action on a loan application. Just to clarify the process:

1. First, the loan must be submitted for review using 'Submit Loan'
2. Then it can be approved or rejected by our review team
3. The current application needs to be submitted before we can process the decision

Would you like me to help you submit this application first?"""
                            else:
                                assistant_message = f"I understand what you're trying to do, but there seems to be an issue: {error_msg}. How can I help you proceed?"
                        else:
                            # Format the response data in a more conversational way
                            if "loan_amount" in response_data:
                                details = []
                                if "applicant_name" in response_data:
                                    details.append(f"• Applicant: {response_data['applicant_name']}")
                                if "loan_amount" in response_data:
                                    details.append(f"• Amount: ${response_data['loan_amount']:,.2f}")
                                if "status" in response_data:
                                    details.append(f"• Status: {response_data['status']}")
                                if "rejection_reason" in response_data and response_data.get('status') == 'REJECTED':
                                    details.append(f"• Rejection Reason: {response_data['rejection_reason']}")
                                
                                assistant_message = "Here are the loan details you asked for:\n" + "\n".join(details)
                                
                                # Add contextual suggestions based on status
                                if response_data.get('status') == 'DRAFT':
                                    assistant_message += "\n\nThis application is still in draft. Would you like me to help you submit it for review?"
                                elif response_data.get('status') == 'REJECTED':
                                    assistant_message += "\n\nI see this loan was rejected. Would you like to discuss the reason or explore other loan options?"
                            else:
                                assistant_message = result.get("response", "I'm here to help! What would you like to know about our loan services?")
                    
                    # Add assistant response
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": assistant_message
                    })
                    st.rerun()
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.markdown("</div></div>", unsafe_allow_html=True)





