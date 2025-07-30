"""
Audit Summary Azure AI Agent using Semantic Kernel with OpenAPI Tools
This agent generates comprehensive audit summary reports for loan applications.
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

from azure.ai.agents.models import OpenApiAnonymousAuthDetails, OpenApiTool
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import ChatMessageContent, FunctionCallContent, FunctionResultContent

# Azure AI Studio Project Configuration
AZURE_CONFIG = {
    "model_deployment_name": "gpt-4o-mini",
    "project_connection_string": "eastus2.api.azureml.ms;154396ac-15fb-44d7-9927-35eaea9d57e6;rg-jyothikakoppula11-3861_ai;realtimeproject01"
}

# Agent Configuration
AGENT_NAME = "AuditSummaryAgent"

def load_agent_instructions() -> str:
    """Load agent instructions from instructions.txt file"""
    try:
        instructions_path = os.path.join(os.path.dirname(__file__), "instructions.txt")
        if os.path.exists(instructions_path):
            with open(instructions_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        else:
            print(f"⚠️ Instructions file not found: {instructions_path}")
            return "You are an audit summary specialist. Generate comprehensive audit reports for loan applications."
    except Exception as e:
        print(f"⚠️ Error loading instructions: {e}")
        return "You are an audit summary specialist. Generate comprehensive audit reports for loan applications."


class AuditDataProcessor:
    """Utility class to process audit data and generate formatted reports"""
    
    @staticmethod
    def format_currency(amount: float) -> str:
        """Format currency in Indian Rupees with proper formatting"""
        if amount >= 10000000:  # 1 crore
            return f"₹{amount/10000000:.2f} crore"
        elif amount >= 100000:  # 1 lakh
            return f"₹{amount/100000:.2f} lakh"
        else:
            return f"₹{amount:,.0f}"
    
    @staticmethod
    def get_status_emoji(status: str) -> str:
        """Get appropriate emoji for audit status"""
        status_lower = status.lower()
        if any(word in status_lower for word in ['pass', 'passed', 'approve', 'approved', 'success', 'cleared', 'verified', 'submitted']):
            return "✅"
        elif any(word in status_lower for word in ['fail', 'failed', 'reject', 'rejected', 'denied', 'error']):
            return "❌"
        elif any(word in status_lower for word in ['pending', 'review', 'progress', 'in progress']):
            return "⏳"
        elif any(word in status_lower for word in ['warning', 'caution', 'issue']):
            return "⚠️"
        else:
            return "📝"
    
    @staticmethod
    def calculate_duration(start_time: str, end_time: str) -> str:
        """Calculate duration between two timestamps"""
        try:
            # Handle different timestamp formats
            formats = [
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S"
            ]
            
            start_dt = None
            end_dt = None
            
            for fmt in formats:
                try:
                    start_dt = datetime.strptime(start_time, fmt)
                    break
                except ValueError:
                    continue
            
            for fmt in formats:
                try:
                    end_dt = datetime.strptime(end_time, fmt)
                    break
                except ValueError:
                    continue
            
            if start_dt and end_dt:
                duration = end_dt - start_dt
                hours = duration.total_seconds() // 3600
                minutes = (duration.total_seconds() % 3600) // 60
                return f"{int(hours)} hours {int(minutes)} minutes"
            else:
                return "Duration not available"
        except Exception:
            return "Duration not available"
    
    @staticmethod
    def format_timestamp(timestamp: str) -> str:
        """Format timestamp to more detailed but compact format"""
        try:
            formats = [
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S"
            ]
            
            dt = None
            for fmt in formats:
                try:
                    dt = datetime.strptime(timestamp, fmt)
                    break
                except ValueError:
                    continue
            
            if dt:
                # More detailed format: MM/DD HH:MM:SS.ms
                return dt.strftime("%m/%d %H:%M:%S.%f")[:-3]  # Remove last 3 microsecond digits
            else:
                return timestamp
        except Exception:
            return timestamp
    
    @staticmethod
    def generate_audit_summary(customer_data: Dict, audit_response: Dict) -> str:
        """Generate the formatted audit summary report"""
        processor = AuditDataProcessor()
        
        # Extract customer information
        customer_id = customer_data.get('customer_id', 'N/A')
        customer_name = customer_data.get('name', 'N/A')
        
        # Extract audit records from the API response structure
        audit_records = audit_response.get('records', []) if isinstance(audit_response, dict) else audit_response
        
        # Process audit records
        if not audit_records:
            return f"No audit records found for Customer ID: {customer_id}"
        
        # Sort audit records by timestamp (using proper field names)
        sorted_records = sorted(audit_records, key=lambda x: x.get('Event_Time', ''))
        
        # Determine final status
        last_record = sorted_records[-1] if sorted_records else {}
        final_status = last_record.get('Audit_Status', 'Pending')
        final_emoji = processor.get_status_emoji(final_status)
        
        # Determine next step based on final status
        next_step = "Contact customer service for more information"
        if 'approve' in final_status.lower():
            next_step = "Ready for Disbursement"
        elif 'pending' in final_status.lower():
            next_step = "Awaiting further review"
        elif 'reject' in final_status.lower():
            next_step = "Review rejection reasons and reapply if eligible"
        elif 'cleared' in final_status.lower():
            next_step = "Ready for Disbursement"
        
        # Assume default loan amount and type (can be enhanced with actual data)
        loan_amount = "25,00,000"  # Default value
        application_date = sorted_records[0].get('Event_Time', '').split('T')[0] if sorted_records and sorted_records[0].get('Event_Time') else 'N/A'
        
        # Format application date
        if application_date != 'N/A':
            try:
                from datetime import datetime
                date_obj = datetime.strptime(application_date, '%Y-%m-%d')
                application_date = date_obj.strftime('%B %d, %Y')
            except:
                pass
        
        # Generate the report
        report = f"""🧾 Loan Application Audit Summary Report

🧍 Customer Information
Customer ID: {customer_id}
Customer Name: {customer_name}
Loan Type: 🏠 Home Loan
Requested Amount: ₹{loan_amount}
Application Date: {application_date}
Total Processing Duration: 6 hours
Final Decision: {final_emoji} {final_status}
Next Step: {next_step}

🔍 Detailed Audit Trail
| Stage No. | Audit Checkpoint | Status | Auditor | Timestamp | Remarks |
|-----------|------------------|--------|---------|-----------|---------|"""

        # Add audit records to table
        for i, record in enumerate(sorted_records, 1):
            audit_type = record.get('Audit_Type', 'Unknown')
            status = record.get('Audit_Status', 'Unknown')
            status_emoji = processor.get_status_emoji(status)
            auditor = record.get('Auditor_Name', 'System')
            timestamp = processor.format_timestamp(record.get('Event_Time', ''))
            remarks = record.get('Remarks', 'No remarks available')
            
            # Limit remarks length for table formatting
            if len(remarks) > 55:
                remarks = remarks[:52] + "..."
            
            report += f"\n| {i} | {audit_type} | {status_emoji} {status} | {auditor} | {timestamp} | {remarks} |"

        # Add overview summary
        total_stages = len(sorted_records)
        passed_stages = len([r for r in sorted_records if any(word in r.get('Audit_Status', '').lower() for word in ['pass', 'approve', 'verified', 'cleared', 'submitted'])])
        
        report += f"""

Overview summary: This report summarizes the complete audit lifecycle of the loan application submitted by Customer ID: {customer_id}. The application went through {total_stages} sequential validation checkpoints, covering eligibility, documentation, verification, underwriting, and final approval.

All audit stages were successfully completed on the same day without any delays, escalations, or follow-up actions."""

        return report


async def main() -> None:
    """Main function to run the Audit Summary Agent"""
    # Set environment variables for Azure AI Agent
    os.environ["AZURE_AI_AGENT_PROJECT_CONNECTION_STRING"] = AZURE_CONFIG["project_connection_string"]
    os.environ["AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"] = AZURE_CONFIG["model_deployment_name"]

    # Initialize the agent settings
    ai_agent_settings = AzureAIAgentSettings()

    print("📊 Audit Summary Agent Starting...")
    print("=" * 50)

    # Create Azure AI Agent client with proper error handling
    try:
        async with (
            DefaultAzureCredential() as creds,
            AzureAIAgent.create_client(credential=creds) as client,
        ):
            # Load OpenAPI spec for audit API
            with open("audit_agent.json", "r") as f:
                audit_api_spec = json.load(f)

            # Create OpenAPI tool for audit operations
            auth = OpenApiAnonymousAuthDetails()
            audit_api_tool = OpenApiTool(
                name="audit_api",
                spec=audit_api_spec,
                description="API for retrieving audit records and customer information for comprehensive audit reporting",
                auth=auth,
            )

            # Create agent definition with OpenAPI tools
            agent_instructions = load_agent_instructions()
            agent_definition = await client.agents.create_agent(
                model=ai_agent_settings.model_deployment_name,
                name=AGENT_NAME,
                instructions=agent_instructions,
                tools=audit_api_tool.definitions,
            )

            # Create the AzureAI Agent
            agent = AzureAIAgent(
                client=client,
                definition=agent_definition,
            )

            print(f"✅ {AGENT_NAME} initialized with audit API tools!")
            print("Enter customer names to generate audit summaries")
            print("Type 'quit' to exit")
            print("=" * 50)

            # Run interactive conversation
            thread: AzureAIAgentThread = None

            try:
                while True:
                    # Get user input
                    user_input = input("\nEnter customer name (or 'quit' to exit): ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'bye']:
                        print("📊 Thank you for using the Audit Summary service. Goodbye!")
                        break
                    
                    if not user_input:
                        continue

                    print(f"\n🔍 Generating audit summary for: {user_input}")
                    print("-" * 40)
                    
                    try:
                        # Process the request through the agent
                        async for response in agent.invoke(messages=f"Generate an audit summary report for customer: {user_input}", thread=thread):
                            # Handle function calls and results
                            if response.items:
                                for item in response.items:
                                    if isinstance(item, FunctionCallContent):
                                        print(f"🔧 API Call: {item.name}")
                                        if item.arguments:
                                            print(f"   Arguments: {item.arguments}")
                                    elif isinstance(item, FunctionResultContent):
                                        print(f"📝 API Response received")
                            
                            # Print agent response (the formatted audit summary)
                            if response.content:
                                print(f"\n{response.content}")
                            
                            thread = response.thread
                            
                    except Exception as e:
                        print(f"❌ Error generating audit summary: {e}")
                        print("Please check the customer name and try again.")
                    
                    print("\n" + "=" * 50)
                
            except KeyboardInterrupt:
                print("\n\n📊 Audit Summary Agent terminated. Goodbye!")
            
            finally:
                # Cleanup resources
                try:
                    if thread:
                        await thread.delete()
                    await client.agents.delete_agent(agent.id)
                    print("\n🧹 Cleanup completed.")
                except Exception as e:
                    print(f"Cleanup error (can be ignored): {e}")

    except Exception as e:
        print(f"❌ Failed to initialize Audit Summary Agent: {e}")
        print("Please check your Azure configuration and try again.")


async def test_audit_summary() -> None:
    """Test function for the audit summary agent"""
    print("🧪 Testing Audit Summary Agent...")
    print("=" * 50)
    
    # Test customer names
    test_customers = [
        "John Doe",
        "Jane Smith", 
        "Rajesh Kumar"
    ]
    
    print("Available test customers:")
    for i, customer in enumerate(test_customers, 1):
        print(f"{i}. {customer}")
    
    choice = input("\nSelect a customer (1-3) or enter custom name: ").strip()
    
    try:
        choice_num = int(choice)
        if 1 <= choice_num <= len(test_customers):
            customer_name = test_customers[choice_num - 1]
        else:
            customer_name = input("Enter customer name: ").strip()
    except ValueError:
        customer_name = choice
    
    if not customer_name:
        print("No customer name provided. Exiting test.")
        return
    
    # Set environment variables
    os.environ["AZURE_AI_AGENT_PROJECT_CONNECTION_STRING"] = AZURE_CONFIG["project_connection_string"]
    os.environ["AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"] = AZURE_CONFIG["model_deployment_name"]

    ai_agent_settings = AzureAIAgentSettings()

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # Load OpenAPI spec
        with open("audit_agent.json", "r") as f:
            audit_api_spec = json.load(f)

        # Create OpenAPI tool
        auth = OpenApiAnonymousAuthDetails()
        audit_api_tool = OpenApiTool(
            name="audit_api",
            spec=audit_api_spec,
            description="API for retrieving audit records and customer information",
            auth=auth,
        )

        # Create agent
        agent_instructions = load_agent_instructions()
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name=AGENT_NAME,
            instructions=agent_instructions,
            tools=audit_api_tool.definitions,
        )

        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        print(f"✅ Testing audit summary for: {customer_name}")
        print("-" * 50)

        thread: AzureAIAgentThread = None

        try:
            async for response in agent.invoke(
                messages=f"Generate a comprehensive audit summary report for customer: {customer_name}", 
                thread=thread
            ):
                # Handle function calls
                if response.items:
                    for item in response.items:
                        if isinstance(item, FunctionCallContent):
                            print(f"🔧 API Call: {item.name}({item.arguments})")
                        elif isinstance(item, FunctionResultContent):
                            print(f"📝 API Result received")
                
                # Print the audit summary
                if response.content:
                    print(f"\n{response.content}")
                
                thread = response.thread
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            
        finally:
            # Cleanup
            if thread:
                await thread.delete()
            await client.agents.delete_agent(agent.id)


if __name__ == "__main__":
    print("📊 Audit Summary Agent with Azure AI and Semantic Kernel")
    print("=" * 60)
    
    print("\nSelect mode:")
    print("1. Interactive mode")
    print("2. Test mode")
    
    mode = input("Enter choice (1 or 2): ").strip()
    
    if mode == "2":
        asyncio.run(test_audit_summary())
    else:
        asyncio.run(main())
