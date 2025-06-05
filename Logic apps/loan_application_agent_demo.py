# pip install azure-ai-projects~=1.0.0b7
# pip install requests
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import time
import json
import sys

# Import our custom modules
from custom_agent_functions import submit_loan_application, check_loan_status, trigger_logic_app_workflow, reduce_interest_rate
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
    print("💼 Interactive Loan Application Agent with Logic App Integration 💼")
    print("This agent can help you apply for loans, check application status,")
    print("and trigger various banking workflows through Logic Apps")
    print("Type 'exit' or 'quit' to end the conversation")
    print("="*70)
    
    # Create a new thread for this conversation
    thread = create_new_thread()
    print(f"\n🔄 Starting a new conversation thread (ID: {thread.id})")
    
    # Get all custom agent tools
    agent_tools = get_all_custom_agent_tools()
    
    # System instructions for the agent
    system_instruction = """
    You are a helpful banking assistant specializing in loan applications and processing.
    
    IMPORTANT INSTRUCTIONS FOR USING TOOLS:
    
    1. Submit Loan Application Tool:
       - ONLY use the submit_loan_application tool when a user EXPLICITLY wants to apply for a new loan
       - Before using this tool, you MUST collect ALL required information:
         * applicant_name: The full name of the applicant
         * loan_amount: The amount requested in dollars (number)
         * loan_type: One of: mortgage, personal, auto, education, business, or other
         * credit_score: A number between 300-850 
         * contact_email: A valid email address for communications
       - If any information is missing, ask for it specifically before using the tool
    
    2. Check Loan Status Tool:
       - ONLY use the check_loan_status tool when a user EXPLICITLY asks about the status of their loan application
       - Before using this tool, you MUST collect:
         * application_id: The ID of their loan application
         * applicant_name: The name of the applicant for verification
       - Always ask for this information if not provided
       
    3. Logic App Trigger Tool:
       - Use the trigger_logic_app_workflow tool when a customer needs to perform an action that matches 
         one of the available workflows: "loan_approval", "account_creation", or "document_processing"
       - You MUST select the appropriate workflow_name based on the customer's request
       - You MUST collect all required information for the input_data parameter based on the workflow
       - For loan_approval workflow: Collect customerName, loanId, and approvalType
       - For account_creation workflow: Collect customerName, accountType, and initialDeposit
       - For document_processing workflow: Collect customerId, documentType, and documentUrl
       - Always verify all required information is collected before using this tool
    
    4. Interest Rate Reduction Tool:
       - ONLY use the reduce_interest_rate tool when a user EXPLICITLY asks to reduce their loan interest rate
       - You MUST detect any phrases related to interest rate reduction, such as "lower my rate", "reduce my interest", etc.
       - Before using this tool, you MUST collect ALL required information:
         * customer_id: The customer's ID number
         * loan_id: The specific loan ID for which they want a lower rate
         * credit_score: The customer's current credit score (number between 300-850)
       - Always ask for any missing information before proceeding
       - The tool will automatically set the reason as "reduce_interest_rate"
       - Explain to the customer that their request will be reviewed based on their credit score
    
    5. General Guidelines:
       - Be professional, courteous, and helpful at all times
       - Explain the loan application process when asked
       - Only use tools when the user's request clearly matches a tool's purpose
       - If the user asks about something unrelated to loans, politely redirect them
       - Always verify you have collected all required information before using any tool
    """
    
    # Send an initial greeting message to start the conversation
    initial_message = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content="Hello, I'm interested in learning about your banking services."
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
            print("\n👋 Thank you for using our banking services. Goodbye!")
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

# Start the interactive loan application agent
if __name__ == "__main__":
    try:
        interact_with_loan_application_agent()
    except KeyboardInterrupt:
        print("\n\n👋 Program interrupted. Exiting gracefully...")
        sys.exit(0)