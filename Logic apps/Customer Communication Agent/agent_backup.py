# pip install azure-ai-projects~=1.0.0b7
# pip install requests
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import time
import json
import sys

# Import our custom modules
from custom_agent_functions import submit_loan_application, check_loan_status, trigger_logic_app_workflow, reduce_interest_rate, trigger_campaign, trigger_contest, send_mail
from custom_agent_tools import get_all_custom_agent_tools

# Initialize the Azure AI Project client
project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str="eastus2.api.azureml.ms;aee23923-3bba-468d-8dcd-7c4bc1ce218f;rg-ronakofficial1414-9323_ai;ronakofficial1414-8644")

# Get the agent
agent = project_client.agents.get_agent("asst_eo3eOzKI2Sk7NlezVZU35rL8")

# Create a new thread for the conversation
def create_new_thread():
    """Create a new thread for the conversation"""
    return project_client.agents.create_thread()

def extract_message_content(text_message):
    """Extract the text content from a message"""
    try:
        if hasattr(text_message, 'text') and hasattr(text_message.text, 'value'):
            return text_message.text.value
        elif isinstance(text_message, dict) and 'text' in text_message and 'value' in text_message['text']:
            return text_message['text']['value']
        else:
            # Try to access as dictionary
            message_dict = text_message.as_dict() if hasattr(text_message, 'as_dict') else text_message
            if isinstance(message_dict, dict) and 'text' in message_dict and 'value' in message_dict['text']:
                return message_dict['text']['value']
    except Exception:
        pass
    
    # Fallback: return the string representation
    return str(text_message)

def display_latest_message(thread_id):
    """Display only the most recent assistant message"""
    messages = project_client.agents.list_messages(thread_id=thread_id)
    
    # Find the most recent assistant message
    latest_message = None
    for message in messages.text_messages:
        message_content = extract_message_content(message)
        latest_message = message_content
        break  # Only get the most recent message (first in the list)
    
    if latest_message:
        print(f"\n🤖 Agent: {latest_message}\n")
    else:
        print("\n🤖 Agent: No response received.\n")

def interact_with_loan_application_agent():
    print("="*70)
    print("💼 Customer Communication Agent for Loan Process 💼")
    print("This agent helps customers with communication during their loan process.")
    print("Please provide your customer ID and current stage in the loan process.")
    print("Available stages: Stage 1 (Application), Stage 2 (Document Submission)")
    print("Type 'exit' or 'quit' to end the conversation")
    print("="*70)
    
    # Create a new thread for this conversation
    thread = create_new_thread()
    print(f"\n🔄 Starting a new conversation thread (ID: {thread.id})")
    
    # Get all custom agent tools
    agent_tools = get_all_custom_agent_tools()
      # System instructions for the agent    system_instruction = """
    You are a Customer Communication Agent for Global Trust Bank specializing in loan process communication.
    
    Your primary purpose is to help customers with communication during their loan process by collecting their customer ID and current stage, then sending them appropriate updates via email.
    
    IMPORTANT INSTRUCTIONS FOR USING THE SEND MAIL TOOL:
    
    1. Send Mail Tool (PRIMARY FUNCTION):
       - This is your main and most important tool
       - ALWAYS use the send_mail tool when a customer provides their customer ID and loan process stage
       - You MUST collect the required pieces of information:
         * customer_id: The customer's unique ID number
         * stage: The current stage they are in
       - Available stages are:
         * "application" (Stage 1): For customers in the application stage
         * "document_submission" (Stage 2): For customers in the document submission stage
         * "verification" (Stage 3): For customers in the verification stage
         * "document_approval" (Stage 4): For customers in the document approval stage
         * "approval" (Stage 5): For customers in the approval stage
         * "loan_letter" (Stage 6): For customers in the loan letter stage
       
       - SPECIAL CASE FOR STAGE 4 (document_approval):
         * If the customer selects Stage 4 (document_approval), you MUST also ask for the condition
         * Ask: "Is the document approval condition met? Please answer with 'true' or 'false'."
         * The condition parameter should be either "true" or "false" 
         * Only ask for condition when stage is "document_approval" (Stage 4)
         * Do NOT ask for condition for any other stages
       
       - Stage mapping:
         * If customer mentions "stage 1" or "application", use "application"
         * If customer mentions "stage 2" or "document submission", use "document_submission"
         * If customer mentions "stage 3" or "verification", use "verification"
         * If customer mentions "stage 4" or "document approval", use "document_approval"
         * If customer mentions "stage 5" or "approval", use "approval"
         * If customer mentions "stage 6" or "loan letter", use "loan_letter"
       
       - After using this tool, ALWAYS respond with: "Thank you for using Global Trust Bank services you will be notified via mail"
       - If any required information is missing, ask for it specifically before using the tool
    
    2. General Guidelines:
       - Be professional, courteous, and helpful at all times
       - Your main focus is customer communication for loan processes
       - Always ask for customer ID and stage if not provided
       - Explain the available stages if the customer is unsure:
         * Stage 1: Application stage - for customers who have submitted their loan application
         * Stage 2: Document submission stage - for customers who need to submit additional documents
         * Stage 3: Verification stage - for customers in the verification process
         * Stage 4: Document approval stage - for customers awaiting document approval (requires condition)
         * Stage 5: Approval stage - for customers who have received approval
         * Stage 6: Loan letter stage - for customers receiving their loan letter
       - Only use the send_mail tool - avoid using other tools unless specifically requested
       - Keep conversations focused on loan process communication
       - If customers ask about unrelated topics, politely redirect them to the loan communication process
    
    3. Conversation Flow:
       - Greet the customer warmly
       - Ask for their customer ID if not provided
       - Ask which stage they are currently in if not specified
       - If they select Stage 4 (document_approval), ask for the condition (true/false)
       - Use the send_mail tool once you have all required information
       - Provide the standard response after successful email sending
    
    Remember: Your primary goal is to collect customer ID, stage information, and condition (only for Stage 4), then use the send_mail tool to notify them via email.
    """
      # Send an initial greeting message to start the conversation
    initial_message = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content="Hello, I need help with communication during my loan process."
    )
    
    print("\n⏳ Agent is thinking...")
    
    # Process the initial message with system instructions but no tools yet
    # Using create_and_process_run instead of create_run + process_run
    run = project_client.agents.create_and_process_run(
        thread_id=thread.id,
        agent_id=agent.id,
        instructions=system_instruction
    )
    
    # Display the agent's initial response
    display_latest_message(thread.id)
    
    # Start the conversation loop
    while True:
        # Get user input
        user_message = input("👤 You: ")
        
        if user_message.lower() in ['exit', 'quit']:
            print("\n👋 Thank you for using our  services. Goodbye!")
            break
        
        # Send message to the agent
        message = project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=user_message
        )
        
        print("\n⏳ Agent is processing your request...")
        
        # Create run with all custom tools and system instructions
        # Using create_run but not process_run yet
        run = project_client.agents.create_run(
            thread_id=thread.id,
            agent_id=agent.id,
            tools=agent_tools,
            instructions=system_instruction
        )
        
        # Monitor the run until it completes or requires action
        run_status = None
        while run_status not in ["completed", "requires_action", "failed", "cancelled", "expired"]:
            # Get the current run status
            run = project_client.agents.get_run(run_id=run.id, thread_id=thread.id)
            run_status = run.status
            
            # If still in progress, wait a bit before checking again
            if run_status == "in_progress":
                time.sleep(1)
        
        # Check if the run requires action (tool use)
        if run_status == "requires_action" and hasattr(run, "required_action"):
            # Handle tool calls
            tool_outputs = []
            
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                try:
                    # Parse the function arguments
                    args = json.loads(tool_call.function.arguments)
                    
                    # Handle different tool types
                    if tool_call.function.name == "submit_loan_application":
                        print(f"\n📝 Processing loan application for {args.get('applicant_name')}...")
                        
                        # Call the function with the provided arguments
                        result = submit_loan_application(
                            applicant_name=args.get("applicant_name"),
                            loan_amount=args.get("loan_amount"),
                            loan_type=args.get("loan_type"),
                            credit_score=args.get("credit_score"),
                            contact_email=args.get("contact_email")
                        )
                        
                        # Add the result to tool outputs
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(result)
                        })
                        
                    elif tool_call.function.name == "check_loan_status":
                        print(f"\n🔍 Checking status of loan application {args.get('application_id')}...")
                        
                        # Call the function with the provided arguments
                        result = check_loan_status(
                            application_id=args.get("application_id"),
                            applicant_name=args.get("applicant_name")
                        )
                        
                        # Add the result to tool outputs
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(result)
                        })
                        
                    elif tool_call.function.name == "trigger_logic_app_workflow":
                        workflow_name = args.get("workflow_name")
                        input_data = args.get("input_data", {})
                        
                        print(f"\n⚙️ Triggering Logic App workflow: {workflow_name}...")
                        
                        # Call the function with the provided arguments
                        result = trigger_logic_app_workflow(
                            workflow_name=workflow_name,
                            input_data=input_data
                        )                        
                        # Add the result to tool outputs
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(result)
                        })
                    
                    elif tool_call.function.name == "reduce_interest_rate":
                        customer_id = args.get("customer_id")
                        loan_id = args.get("loan_id")
                        credit_score = args.get("credit_score")
                        
                        print(f"\n📉 Processing interest rate reduction for customer {customer_id}, loan {loan_id}...")
                        
                        # Call the function with the provided arguments
                        result = reduce_interest_rate(
                            customer_id=customer_id,
                            loan_id=loan_id,
                            credit_score=credit_score
                        )
                          # Add the result to tool outputs
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(result)
                        })
                    
                    elif tool_call.function.name == "trigger_campaign":
                        intent = args.get("intent", "campaign")
                        subject = args.get("subject")
                        body = args.get("body")
                        
                        print(f"\n🎯 Triggering marketing campaign with intent: {intent}...")
                        
                        # Call the function with the provided arguments
                        result = trigger_campaign(
                            intent=intent,
                            subject=subject,
                            body=body
                        )
                        
                        # Add the result to tool outputs
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(result)
                        })
                    
                    elif tool_call.function.name == "trigger_contest":
                        intent = args.get("intent", "contest")
                        subject = args.get("subject")
                        body = args.get("body")
                        
                        print(f"\n🏆 Triggering contest with intent: {intent}...")
                        
                        # Call the function with the provided arguments
                        result = trigger_contest(
                            intent=intent,
                            subject=subject,
                            body=body
                        )
                        
                        # Add the result to tool outputs
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(result)
                        })
                      elif tool_call.function.name == "send_mail":
                        customer_id = args.get("customer_id")
                        stage = args.get("stage")
                        condition = args.get("condition")  # Get the condition parameter
                        
                        print(f"\n📧 Sending customer communication email for customer {customer_id} at stage: {stage}...")
                        
                        # Call the function with the provided arguments, including condition
                        result = send_mail(
                            customer_id=customer_id,
                            stage=stage,
                            condition=condition
                        )
                        
                        # Add the result to tool outputs
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(result)
                        })
                
                except Exception as e:
                    print(f"Error processing tool call: {str(e)}")
                    # Return error message to the agent
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps({"error": str(e)})
                    })
            
            # Submit tool outputs back to the agent if we have any
            if tool_outputs:
                # Submit the outputs - fixed method name from submit_tool_outputs to submit_tool_outputs_to_run
                run = project_client.agents.submit_tool_outputs_to_run(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
                
                # Monitor the run again after submitting tool outputs
                run_status = None
                while run_status not in ["completed", "requires_action", "failed", "cancelled", "expired"]:
                    # Get the current run status
                    run = project_client.agents.get_run(run_id=run.id, thread_id=thread.id)
                    run_status = run.status
                    
                    # If still in progress, wait a bit before checking again
                    if run_status == "in_progress":
                        time.sleep(1)
        
        # Display the latest message from the agent
        display_latest_message(thread.id)

# Start the interactive Customer Communication Agent
if __name__ == "__main__":
    try:
        interact_with_loan_application_agent()
    except KeyboardInterrupt:
        print("\n\n👋 Program interrupted. Exiting gracefully...")
        sys.exit(0)