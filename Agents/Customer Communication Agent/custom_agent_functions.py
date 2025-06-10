"""
Custom Agent Functions Module

This module contains functions that can be called by an AI agent to perform
specific operations by integrating with Azure Logic Apps. Each function
represents a capability that can be exposed as a tool to the agent.
"""

import os
import requests
import json
from typing import Dict, Any, Optional, List


def submit_loan_application(applicant_name: str, loan_amount: float, loan_type: str, credit_score: int, contact_email: str) -> Dict[str, Any]:
    """
    Submits a new loan application via Logic App and returns the application ID.

    :param applicant_name (str): The full name of the loan applicant.
    :param loan_amount (float): The requested loan amount in dollars.
    :param loan_type (str): The type of loan (e.g., 'mortgage', 'personal', 'auto', 'education').
    :param credit_score (int): The applicant's credit score (typically between 300-850).
    :param contact_email (str): The email address for communications about the loan.
    :return: A dictionary containing the application_id and status of the submission.
    :rtype: Dict[str, Any]
    """
    # Logic App endpoint - replace with your actual Logic App URL
    api_url = "https://demo1414.azurewebsites.net:443/api/agent/triggers/When_a_HTTP_request_is_received/invoke?api-version=2022-05-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=HZ0I3n6VpNoP0Ijw691jeFXYwOcT6OtQhJopwfpYvn4"
    
    print(f"Submitting new {loan_type} loan application for {applicant_name}...")

    try:
        # Make the HTTP POST API call with the correct JSON payload
        response = requests.post(
            api_url,
            json={
                "applicantName": applicant_name,
                "loanAmount": loan_amount,
                "loanType": loan_type,
                "creditScore": credit_score,
                "contactEmail": contact_email
            },
            headers={"Content-Type": "application/json"},
        )
        
        # Generate a consistent application ID based on inputs
        application_id = "APP" + str(hash(applicant_name + str(loan_amount)))[-8:]
        
        # Return a standard response without waiting for Logic App completion
        result = {
            "application_id": application_id,
            "status": "submitted",
            "message": "Your loan application has been submitted to Global Trust Bank. You will receive updates via your registered email ID."
        }
        
        print(f"Loan application submitted with ID: {application_id}")
        return result
        
    except Exception as e:
        print(f"Error submitting loan application: {str(e)}")
        return {
            "status": "error",
            "message": "There was an issue submitting your application. Please try again later or contact customer support."
        }


def check_loan_status(application_id: str, applicant_name: str) -> Dict[str, Any]:
    """
    Checks the status of an existing loan application via Logic App.

    :param application_id (str): The unique identifier for the loan application.
    :param applicant_name (str): The name of the applicant for verification.
    :return: A dictionary containing the current status and details of the application.
    :rtype: Dict[str, Any]
    """
    # Logic App endpoint - replace with your actual Logic App URL for status checking
    api_url = "https://demo1414.azurewebsites.net:443/api/agent/triggers/When_a_HTTP_request_is_received/invoke?api-version=2022-05-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=HZ0I3n6VpNoP0Ijw691jeFXYwOcT6OtQhJopwfpYvn4"
    
    print(f"Checking status of loan application {application_id}...")

    try:
        # Make the HTTP POST API call with the correct JSON payload
        response = requests.post(
            api_url,
            json={
                "applicationId": application_id,
                "applicantName": applicant_name
            },
            headers={"Content-Type": "application/json"},
        )
        
        # Simulate a status response based on the application_id value
        # In a real implementation, this would parse the actual response from the Logic App
        status_mapping = {
            "0": "submitted",
            "1": "under_review",
            "2": "approved",
            "3": "denied",
            "4": "pending_documents"
        }
        
        # Get the last character of the application_id to simulate different statuses
        last_char = application_id[-1]
        simulated_status = status_mapping.get(last_char, "under_review")
        
        result = {
            "application_id": application_id,
            "status": simulated_status,
            "last_updated": "2025-05-21T14:30:00Z",  # Use current date in format
            "next_steps": get_next_steps_for_status(simulated_status),
            "estimated_completion": get_estimated_completion(simulated_status),
            "message": "Your status inquiry has been processed. The latest information has been sent to your registered email ID."
        }
        
        print(f"Loan application status check completed for ID: {application_id}")
        return result
        
    except Exception as e:
        print(f"Error checking loan status: {str(e)}")
        return {
            "status": "error",
            "application_id": application_id,
            "message": "There was an issue retrieving your application status. Please try again later or contact customer support."
        }


def get_next_steps_for_status(status: str) -> str:
    """Helper function to get next steps based on application status"""
    status_steps = {
        "submitted": "Your application has been received. Our team will begin reviewing it shortly.",
        "under_review": "Your application is currently being reviewed by our loan officers. No action needed at this time.",
        "approved": "Congratulations! Your loan has been approved. Please check your email for documents to sign.",
        "denied": "We regret to inform you that your application was not approved. Please contact our customer service for more details.",
        "pending_documents": "We need additional documentation. Please upload the requested documents through our portal."
    }
    return status_steps.get(status, "Please contact customer service for assistance with your application.")


def get_estimated_completion(status: str) -> Optional[str]:
    """Helper function to provide estimated completion date based on status"""
    if status == "submitted":
        return "2025-05-20"
    elif status == "under_review":
        return "2025-05-25"
    elif status == "pending_documents":
        return "2025-06-05"
    else:
        return None


def trigger_logic_app_workflow(workflow_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Triggers a specific Logic App workflow by name with the provided input data.
    This is a general-purpose tool that can trigger any configured Logic App workflow.

    :param workflow_name (str): The name of the Logic App workflow to trigger.
                               Currently supported workflows: 'loan_approval', 'account_creation', 'document_processing'
    :param input_data (Dict[str, Any]): The input data to send to the Logic App workflow as JSON
    :return: A dictionary containing a standard success message
    :rtype: Dict[str, Any]
    """
    # Map of workflow names to their corresponding Logic App URLs
    workflow_urls = {
        "loan_approval": "https://demo1414.azurewebsites.net:443/api/agent/triggers/When_a_HTTP_request_is_received/invoke?api-version=2022-05-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=HZ0I3n6VpNoP0Ijw691jeFXYwOcT6OtQhJopwfpYvn4",
        "account_creation": "https://demo1414.azurewebsites.net:443/api/agent/triggers/When_a_HTTP_request_is_received/invoke?api-version=2022-05-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=HZ0I3n6VpNoP0Ijw691jeFXYwOcT6OtQhJopwfpYvn4",
        "document_processing": "https://demo1414.azurewebsites.net:443/api/agent/triggers/When_a_HTTP_request_is_received/invoke?api-version=2022-05-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=HZ0I3n6VpNoP0Ijw691jeFXYwOcT6OtQhJopwfpYvn4"
    }
    
    # Verify the workflow name is valid
    if workflow_name not in workflow_urls:
        return {
            "status": "error",
            "message": f"Unknown workflow: '{workflow_name}'. Supported workflows are: {', '.join(workflow_urls.keys())}"
        }
    
    # Get the URL for the specified workflow
    api_url = workflow_urls[workflow_name]
    
    print(f"Triggering Logic App workflow: {workflow_name}")
    print(f"Input data: {json.dumps(input_data, indent=2)}")

    try:
        # Make the HTTP POST API call with the provided input data
        requests.post(
            api_url,
            json=input_data,
            headers={"Content-Type": "application/json"},
        )
        
        # Return standard success message without waiting for or processing the Logic App response
        workflow_messages = {
            "loan_approval": "Your loan approval request has been submitted to Global Trust Bank.",
            "account_creation": "Your account creation request has been submitted to Global Trust Bank.",
            "document_processing": "Your documents have been submitted to Global Trust Bank for processing."
        }
        
        # Get appropriate message based on workflow type
        base_message = workflow_messages.get(
            workflow_name, 
            f"Your {workflow_name} request has been submitted to Global Trust Bank."
        )
        
        result = {
            "status": "success",
            "workflow": workflow_name,
            "message": f"{base_message} You will receive updates via your registered email ID."
        }
        
        print(f"Workflow {workflow_name} triggered successfully")
        return result
        
    except Exception as e:
        error_result = {
            "status": "error",
            "workflow": workflow_name,
            "message": "There was an issue processing your request. Please try again later or contact customer support."
        }
        print(f"Error triggering workflow {workflow_name}: {str(e)}")
        return error_result


def reduce_interest_rate(customer_id: str, loan_id: str, credit_score: int) -> Dict[str, Any]:
    """
    Submits a request to reduce the interest rate on an existing loan based on customer ID, 
    loan ID, and credit score. The request is processed via Logic App.

    :param customer_id (str): The unique ID of the customer requesting interest rate reduction.
    :param loan_id (str): The unique identifier of the loan for which interest rate reduction is requested.
    :param credit_score (int): The customer's current credit score, used to determine eligibility.
    :return: A dictionary containing the status and message about the interest rate reduction request.
    :rtype: Dict[str, Any]
    """
    # Logic App endpoint - using the same endpoint as other functions
    api_url = "https://demo1414.azurewebsites.net:443/api/full_agent/triggers/When_a_HTTP_request_is_received/invoke?api-version=2022-05-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=X7G_qnOpbOPymhWtZaej9XtzT65Ce7dQCqwPRpxKvJI"
    
    print(f"Processing interest rate reduction request for customer {customer_id}, loan {loan_id}...")

    try:
        # Make the HTTP POST API call with the requested parameters and fixed reason
        response = requests.post(
            api_url,
            json={
                "customerId": customer_id,
                "loanId": loan_id,
                "creditScore": credit_score,
                "reason": "reduce_interest_rate"  # Fixed reason as requested
            },
            headers={"Content-Type": "application/json"},
        )
        
        # Return a standard response without waiting for Logic App completion
        result = {
            "status": "submitted",
            "customer_id": customer_id,
            "loan_id": loan_id,
            "message": "Your interest rate reduction request has been submitted to Global Trust Bank. You will receive updates via your registered email ID."
        }
        
        # Provide additional information based on credit score
        if credit_score >= 750:
            result["eligibility"] = "high"
            result["details"] = "Based on your excellent credit score, you have a high chance of approval."
        elif credit_score >= 650:
            result["eligibility"] = "medium"
            result["details"] = "Based on your good credit score, your request will be reviewed carefully."
        else:
            result["eligibility"] = "review_needed"
            result["details"] = "Your request will require additional review by our team."
        
        print(f"Interest rate reduction request submitted for customer {customer_id}")
        return result
        
    except Exception as e:
        print(f"Error submitting interest rate reduction: {str(e)}")
        return {
            "status": "error",
            "customer_id": customer_id,
            "loan_id": loan_id,
            "message": "There was an issue submitting your interest rate reduction request. Please try again later or contact customer support."
        }


def trigger_campaign(intent: str, subject: str, body: str) -> Dict[str, Any]:
    """
    Triggers a marketing campaign via Logic App when the user requests to run a campaign.

    :param intent (str): Must be "campaign" for this function
    :param subject (str): The subject line for the campaign email
    :param body (str): The body content for the campaign email
    :return: A dictionary containing the status and message about the campaign trigger
    :rtype: Dict[str, Any]
    """
    # Logic App endpoint for campaign/contest functionality
    api_url = "https://demo1414.azurewebsites.net:443/api/insurance/triggers/When_a_HTTP_request_is_received/invoke?api-version=2022-05-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=qXa1nInAJlaj5dq3qMS7hO3ccFf8hd09dDU_Ab46S5s"
    
    print(f"Triggering campaign with intent: {intent}, subject: {subject}...")

    try:
        # Make the HTTP POST API call with the required parameters
        response = requests.post(
            api_url,
            json={
                "intent": intent,
                "subject": subject,
                "body": body
            },
            headers={"Content-Type": "application/json"},
        )
        
        # Return a standard response without waiting for Logic App completion
        result = {
            "status": "submitted",
            "intent": intent,
            "subject": subject,
            "message": "Your campaign request has been submitted to Global Trust Bank. The marketing team will begin processing your campaign shortly. You will receive updates via your registered email ID."
        }
        
        print(f"Campaign triggered successfully with intent: {intent}")
        return result
        
    except Exception as e:
        print(f"Error triggering campaign: {str(e)}")
        return {
            "status": "error",
            "intent": intent,
            "message": "There was an issue processing your campaign request. Please try again later or contact customer support."
        }


def trigger_contest(intent: str, subject: str, body: str) -> Dict[str, Any]:
    """
    Triggers a contest via Logic App when the user requests to run a contest.

    :param intent (str): Must be "contest" for this function
    :param subject (str): The subject line for the contest email
    :param body (str): The body content for the contest email
    :return: A dictionary containing the status and message about the contest trigger
    :rtype: Dict[str, Any]
    """
    # Logic App endpoint for campaign/contest functionality
    api_url = "https://demo1414.azurewebsites.net:443/api/insurance/triggers/When_a_HTTP_request_is_received/invoke?api-version=2022-05-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=qXa1nInAJlaj5dq3qMS7hO3ccFf8hd09dDU_Ab46S5s"
    
    print(f"Triggering contest with intent: {intent}, subject: {subject}...")

    try:
        # Make the HTTP POST API call with the required parameters
        response = requests.post(
            api_url,
            json={
                "intent": intent,
                "subject": subject,
                "body": body
            },
            headers={"Content-Type": "application/json"},
        )
        
        # Return a standard response without waiting for Logic App completion
        result = {
            "status": "submitted",
            "intent": intent,
            "subject": subject,
            "message": "Your contest request has been submitted to Global Trust Bank. The marketing team will begin setting up your contest shortly. You will receive updates via your registered email ID."
        }
        
        print(f"Contest triggered successfully with intent: {intent}")
        return result
        
    except Exception as e:
        print(f"Error triggering contest: {str(e)}")
        return {
            "status": "error",
            "intent": intent,
            "message": "There was an issue processing your contest request. Please try again later or contact customer support."
        }


def send_mail(customer_id: str, stage: str, condition: str = None) -> Dict[str, Any]:
    """
    Sends customer communication email for loan process stage updates via Logic App.
    This function is used by the Customer Communication Agent to notify customers
    about their current stage in the loan process.

    :param customer_id (str): The unique ID of the customer
    :param stage (str): The current stage of the loan process 
                       ('application', 'document_submission', 'verification', 'document_approval', 'approval', 'loan_letter')
    :param condition (str, optional): The condition status for document approval stage. 
                                     Only required for stage 4 (document_approval). Must be 'true' or 'false'.
    :return: A dictionary containing the status and message about the email send operation
    :rtype: Dict[str, Any]
    """
    # Logic App endpoint for customer communication
    api_url = "https://demo1414.azurewebsites.net:443/api/agent/triggers/When_a_HTTP_request_is_received/invoke?api-version=2022-05-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=HZ0I3n6VpNoP0Ijw691jeFXYwOcT6OtQhJopwfpYvn4"
    
    print(f"Sending customer communication email for customer {customer_id} at stage: {stage}...")
    
    # Validate that condition is provided for document_approval stage
    if stage == "document_approval" and condition is None:
        return {
            "status": "error",
            "customer_id": customer_id,
            "stage": stage,
            "message": "Condition parameter is required for document approval stage. Please provide 'true' or 'false'."
        }
    
    # Validate that condition is only provided for document_approval stage
    if stage != "document_approval" and condition is not None:
        return {
            "status": "error",
            "customer_id": customer_id,
            "stage": stage,
            "message": "Condition parameter should only be provided for document approval stage."
        }

    try:
        # Prepare the payload - include condition only for document_approval stage
        payload = {
            "customerId": customer_id,
            "stage": stage
        }
        
        # Add condition only for document_approval stage
        if stage == "document_approval" and condition is not None:
            payload["condition"] = condition
        
        # Make the HTTP POST API call with customer ID, stage, and condition (if applicable)
        response = requests.post(
            api_url,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        
        # Return a standard response
        result = {
            "status": "submitted",
            "customer_id": customer_id,
            "stage": stage,
            "message": "Thank you for using Global Trust Bank services you will be notified via mail"
        }
        
        # Add condition to result if it was provided
        if condition is not None:
            result["condition"] = condition
        
        print(f"Customer communication email sent successfully for customer {customer_id}")
        return result
        
    except Exception as e:
        print(f"Error sending customer communication email: {str(e)}")
        return {
            "status": "error",
            "customer_id": customer_id,
            "stage": stage,
            "message": "There was an issue sending the communication email. Please try again later or contact customer support."
        }


# List of available functions that can be used as agent tools
available_functions = [submit_loan_application, check_loan_status, trigger_logic_app_workflow, reduce_interest_rate, trigger_campaign, trigger_contest, send_mail]