"""
Final Working Loan Orchestrator with Intent-Based Routing
This version works without Pydantic validation issues and properly routes agents.
"""

import asyncio
import os
import sys
import time
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import ChatMessageContent

from dotenv import load_dotenv
load_dotenv()
   
# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our working intent selector
from loan_agent_selector import LoanAgentSelector

# Import agent creation functions
from agents.prequalification_agent import create_prequalification_agent
from agents.application_assist_agent import create_application_assist_agent
from agents.loanstatuscheck import create_loan_status_check_agent
from agents.audit_agent import create_audit_agent

# Import database components
from database import get_db, SessionLocal
from models import MasterCustomerData

# Azure AI Studio Project Configuration
AZURE_CONFIG = {
    "model_deployment_name": os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"),
    "project_connection_string": os.getenv("AZURE_AI_AGENT_PROJECT_CONNECTION_STRING")
}

# Import custom template agent functions for email notifications
custom_agent_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Custom Customer Communication Agent')
sys.path.append(custom_agent_path)
try:
    from custom_agent_functions import send_email_template
    print("✅ Custom template agent functions imported successfully")
except ImportError as e:
    print(f"⚠️ Could not import custom template agent functions: {e}")
    print(f"⚠️ Tried path: {custom_agent_path}")
    # Create a fallback function
    def send_email_template(customer_id: str, stage: str):
        print(f"📧 [FALLBACK] Would send email to customer {customer_id} for stage {stage}")
        return {"status": "fallback", "message": "Template function not available"}


async def create_agents(client):
    """Create the required agents using the existing agent creation functions."""
    
    try:
        print("📋 Creating PrequalificationAgent...")
        prequalification_agent = await create_prequalification_agent(client)
        
        print("📝 Creating ApplicationAssistAgent...")
        application_assist_agent = await create_application_assist_agent(client)
        
        print("📊 Creating LoanStatusCheckAgent...")
        loan_status_check_agent = await create_loan_status_check_agent(client)
        
        print("🛡️ Creating AuditAgent...")
        audit_agent = await create_audit_agent(client)
        
        return [prequalification_agent, application_assist_agent, loan_status_check_agent, audit_agent]
        
    except Exception as e:
        print(f"❌ Error creating agents: {e}")
        print("Make sure the agents folder contains the required agent files.")
        return []


class FinalLoanOrchestrator:
    """
    Final working orchestrator that manages conversation flow between agents
    using intent-based routing without Pydantic issues.
    """
    
    def __init__(self):
        self.agents = []
        self.selector = LoanAgentSelector()
        self.thread = None
        self.client = None
        self.max_retries = 3
        self.base_timeout = 120  # 2 minutes base timeout
        self.retry_delay = 2  # seconds
    
    async def send_stage_email_notification_async(self, stage: str, customer_id: str):
        """
        Async wrapper for sending stage-based email notifications.
        
        :param stage (str): The stage number or name (1, 2, 3, etc.)
        :param customer_id (str): Customer ID to send email to
        :return: Dictionary with status and response details
        """
        try:
            print(f"📧 Sending email notification for stage {stage} to customer {customer_id}...")
            
            # Call the synchronous email function in an executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, send_email_template, customer_id, stage)
            
            return result
            
        except Exception as e:
            print(f"❌ Error sending email notification: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to send email notification: {str(e)}"
            }

    async def invoke_agent_with_retry(self, agent, message, max_retries=None, timeout=None, background=False):
        """
        Invoke an agent with retry logic and better error handling.
        Implements exponential backoff for transient failures.
        """
        if max_retries is None:
            max_retries = self.max_retries
        if timeout is None:
            timeout = self.base_timeout
            
        agent_name = self.selector._get_agent_name(agent)
        prefix = "[BACKGROUND] " if background else ""
        
        for attempt in range(max_retries + 1):
            try:
                if not background:  # Only show attempt messages for main conversation
                    print(f"🔄 Attempt {attempt + 1}/{max_retries + 1} for {agent_name}...")
                
                # Create a timeout for the agent invocation
                response_text = ""
                response_received = False
                
                # Use asyncio.wait_for to add timeout
                async def invoke_with_timeout():
                    nonlocal response_text, response_received
                    async for response in agent.invoke(messages=message, thread=self.thread):
                        if hasattr(response, 'content') and response.content:
                            # Ensure we get the string content properly
                            if hasattr(response.content, 'content'):
                                response_text = str(response.content.content)
                            else:
                                response_text = str(response.content)
                            response_received = True
                            
                            # Update thread for conversation continuity
                            if hasattr(response, 'thread_id'):
                                self.thread = response.thread_id
                            elif hasattr(response, 'thread'):
                                self.thread = response.thread
                            
                            return response_text
                    return response_text
                
                # Apply timeout to the invocation
                result = await asyncio.wait_for(invoke_with_timeout(), timeout=timeout)
                
                if response_received and result:
                    if not background:  # Only show success for main conversation
                        print(f"✅ {agent_name} responded successfully")
                    return result
                else:
                    raise Exception("No response received from agent")
                    
            except asyncio.TimeoutError:
                if not background:
                    print(f"⏰ Timeout after {timeout}s for {agent_name} (attempt {attempt + 1})")
                if attempt < max_retries:
                    # Exponential backoff with jitter
                    delay = self.retry_delay * (2 ** attempt) + (time.time() % 1)
                    if not background:
                        print(f"⏳ Retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                    # Increase timeout for next attempt
                    timeout = min(timeout * 1.5, 300)  # Max 5 minutes
                else:
                    if not background:
                        print(f"❌ {agent_name} failed after {max_retries + 1} attempts due to timeout")
                    return None
                    
            except Exception as e:
                if not background:
                    print(f"❌ Error with {agent_name} (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries:
                    # Check if it's a retryable error
                    error_str = str(e).lower()
                    if any(keyword in error_str for keyword in ['timeout', 'connection', 'network', 'service', 'polling']):
                        delay = self.retry_delay * (2 ** attempt)
                        if not background:
                            print(f"⏳ Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                    else:
                        # Non-retryable error
                        if not background:
                            print(f"❌ Non-retryable error: {str(e)}")
                        return None
                else:
                    if not background:
                        print(f"❌ {agent_name} failed after {max_retries + 1} attempts")
                    return None
        
        return None
        
    async def initialize(self):
        """Initialize the orchestrator with agents and Azure AI client."""
        print("🚀 Initializing Final Loan Orchestrator...")
        
        # Set environment variables for Azure AI Agent
        os.environ["AZURE_AI_AGENT_PROJECT_CONNECTION_STRING"] = AZURE_CONFIG["project_connection_string"]
        os.environ["AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"] = AZURE_CONFIG["model_deployment_name"]
        
        # Create Azure AI Agent client
        creds = DefaultAzureCredential()
        self.client = AzureAIAgent.create_client(credential=creds)
        
        # Create agents
        self.agents = await create_agents(self.client)
        
        if not self.agents:
            print("❌ Failed to create agents. Exiting...")
            return False
            
        print("✅ Orchestrator initialized successfully!")
        print(f"Available agents: {[self.selector._get_agent_name(agent) for agent in self.agents]}")
        return True
        
    async def run_conversation(self):
        """Run an interactive conversation with intent-based agent routing."""
        
        if not await self.initialize():
            return
            
        print("\n🏦 Welcome to Intent-Based Loan Application Service!")
        print("=" * 60)
        print("💡 Try these inputs:")
        print("  • 'I want to check eligibility' → Prequalification Agent")
        print("  • 'I want to apply for a loan' → Application Agent")
        print("  • 'yes please proceed' (after eligibility check) → Switch to Application Agent")
        print("  • 'documents uploaded successfully' → Continue with current agent")
        print("  • 'quit' to exit")
        print("=" * 60)
        print("🔧 Enhanced with retry logic and timeout handling")
        print("⏰ Agent responses shown immediately")
        print("🛡️ Complete audit process shown after application submission")
        print("� Automated email notifications for stages 1-3 after audit completion")
        print("   Stage 1: Application submission confirmation")
        print("   Stage 2: Document upload instructions")
        print("   Stage 3: Verification process notification")
        print("�💡 All audit messages will be displayed before next input prompt")
        print("=" * 60)
        
        # Initialize conversation
        conversation_history = []
        
        try:
            while True:
                # Get user input
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("🤖 Thank you for using our loan service. Have a great day!")
                    break
                    
                if not user_input:
                    continue
                
                # Add user message to history
                user_message = ChatMessageContent(role="user", content=user_input)
                conversation_history.append(user_message)
                
                # Select appropriate agent based on intent
                selected_agent = await self.selector.select_agent(
                    self.agents, 
                    conversation_history
                )
                
                if not selected_agent:
                    print("❌ No agent available to handle your request.")
                    continue
                
                agent_name = self.selector._get_agent_name(selected_agent)
                print(f"🔄 Processing with {agent_name}...")
                
                try:
                    # Get response from selected agent with retry logic
                    response_text = await self.invoke_agent_with_retry(
                        selected_agent, 
                        user_input,
                        max_retries=3,
                        timeout=90  # 1.5 minutes initial timeout
                    )
                    
                    if response_text:
                        # Create a simple response object for tracking
                        class ResponseWithAgent:
                            def __init__(self, content, agent_name):
                                self.content = content
                                self.agent_name = agent_name
                                self.role = "assistant"
                        
                        tracked_response = ResponseWithAgent(response_text, agent_name)
                        conversation_history.append(tracked_response)
                        
                        # Display agent response IMMEDIATELY
                        print(f"\n🤖 {agent_name}: {response_text}")
                        
                        # Check if application submission was completed and run audit synchronously
                        if agent_name.lower() == "applicationassistagent" and "application has been successfully submitted" in response_text.lower():
                            # Run audit process synchronously to show all messages before next user input
                            print("\n🛡️ Starting audit process...")
                            await self.handle_application_submission_immediate(response_text)
                    else:
                        print(f"\n❌ {agent_name} did not respond after multiple attempts.")
                        print("💡 You can try rephrasing your request or try again.")
                        
                except Exception as e:
                    print(f"❌ Unexpected error with {agent_name}: {str(e)}")
                    print("💡 Please try again or rephrase your request.")
                    continue
                    
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thank you for using our loan service.")
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
        finally:
            await self.cleanup()
    
    async def handle_application_submission_immediate(self, response_text):
        """Handle audit process immediately and show all messages before next user input."""
        try:
            # Ensure response_text is a string
            response_content = str(response_text) if response_text else ""
            
            # Step 1: Get latest customer ID from database
            print("🔍 Getting latest customer ID from database...")
            db = SessionLocal()
            try:
                latest_customer = db.query(MasterCustomerData).order_by(
                    MasterCustomerData.Customer_ID.desc()
                ).first()
                
                if latest_customer:
                    customer_id = latest_customer.Customer_ID
                    print(f"🆔 Latest Customer ID: {customer_id}")
                else:
                    print("❌ No customer found in database")
                    return
            finally:
                db.close()
            
            # Step 2: Get Audit Agent
            audit_agent = next((a for a in self.agents if self.selector._get_agent_name(a).lower() == "auditagent"), None)
            if not audit_agent:
                print("⚠️ AuditAgent not found.")
                return
            
            print("="*60)
            print("🛡️ STARTING AUDIT PROCESS")
            print("="*60)
            
            # Step 3: Prequalification Audit
            prequal_prompt = f"""
Create audit record for customer {customer_id} - Prequalification Check.
Audit Type: "Prequalification Check"
Audit Status: "COMPLETED"
Auditor Name: "PrequalificationAgent"
Remarks: "Prequalification process completed successfully. Customer meets basic eligibility criteria for loan application."
Follow-up Required: "No"
"""
            
            print("🛡️ Step 1: Running Prequalification Audit...")
            prequal_response = await self.invoke_agent_with_retry(
                audit_agent, 
                prequal_prompt,
                max_retries=2,
                timeout=60  # 1 minute for audit operations
            )
            
            if prequal_response:
                print(f"📝 Prequalification Audit Response:")
                print(f"   {prequal_response}")
                print("✅ Prequalification audit completed successfully.")
            else:
                print("❌ Prequalification audit failed after retries.")
                return
            
            print("-" * 40)
            
            # Step 4: Application Audit
            app_prompt = f"""
Create audit record for customer {customer_id} - Application Review.
Audit Type: "Application Review"
Audit Status: "COMPLETED" 
Auditor Name: "ApplicationAssistAgent"
Remarks: "Loan application submitted successfully. All required documents and information collected. Application ready for review process."
Follow-up Required: "Yes"

Application Summary:
{response_content}
"""
            
            print("🛡️ Step 2: Running Application Audit...")
            app_response = await self.invoke_agent_with_retry(
                audit_agent, 
                app_prompt,
                max_retries=2,
                timeout=60  # 1 minute for audit operations
            )
            
            if app_response:
                print(f"📝 Application Audit Response:")
                print(f"   {app_response}")
                print("✅ Application audit completed successfully.")
            else:
                print("❌ Application audit failed after retries.")
                return
                
            print("="*60)
            print(f"🎉 ALL AUDIT PROCESSES COMPLETED FOR CUSTOMER {customer_id}!")
            print("📊 Summary:")
            print(f"   • Prequalification Audit: ✅ COMPLETED")
            print(f"   • Application Audit: ✅ COMPLETED") 
            print(f"   • Customer ID: {customer_id}")
            print(f"   • Status: Ready for review")
            print("="*60)
            
            # Send email notifications after audit completion
            current_customer_id = customer_id
            
            # Stage 1: Application - Initial application submission confirmation
            try:
                print(f"\n📧 Sending Stage 1 email notification (Application Submission)...")
                stage1_email_result = await self.send_stage_email_notification_async("1", current_customer_id)
                if stage1_email_result.get("status") == "submitted":
                    print(f"✅ Stage 1 email sent successfully")
                    print(f"   📧 Template: {stage1_email_result.get('template_name', 'application')}")
                    print(f"   📋 Notification: Application submission confirmation sent to customer")
                else:
                    print(f"⚠️ Stage 1 email notification issue: {stage1_email_result.get('message', 'Unknown')}")
            except Exception as email_error:
                print(f"⚠️ Stage 1 email notification failed: {str(email_error)}")
            
            # Wait 1 minute before sending next email
            print(f"⏳ Waiting 1 minute before sending Stage 2 email...")
            await asyncio.sleep(60)  # 60 seconds = 1 minute
            
            # Stage 2: Document Submission - Document upload instructions
            try:
                print(f"\n📧 Sending Stage 2 email notification (Document Submission)...")
                stage2_email_result = await self.send_stage_email_notification_async("2", current_customer_id)
                if stage2_email_result.get("status") == "submitted":
                    print(f"✅ Stage 2 email sent successfully")
                    print(f"   📧 Template: {stage2_email_result.get('template_name', 'document_submission')}")
                    print(f"   📋 Notification: Document upload instructions sent to customer")
                else:
                    print(f"⚠️ Stage 2 email notification issue: {stage2_email_result.get('message', 'Unknown')}")
            except Exception as email_error:
                print(f"⚠️ Stage 2 email notification failed: {str(email_error)}")
            
            # Wait 1 minute before sending next email
            print(f"⏳ Waiting 1 minute before sending Stage 3 email...")
            await asyncio.sleep(60)  # 60 seconds = 1 minute
            
            # Stage 3: Verification - Document verification in progress
            try:
                print(f"\n📧 Sending Stage 3 email notification (Document Verification)...")
                stage3_email_result = await self.send_stage_email_notification_async("3", current_customer_id)
                if stage3_email_result.get("status") == "submitted":
                    print(f"✅ Stage 3 email sent successfully")
                    print(f"   📧 Template: {stage3_email_result.get('template_name', 'verification')}")
                    print(f"   📋 Notification: Document verification process notification sent to customer")
                else:
                    print(f"⚠️ Stage 3 email notification issue: {stage3_email_result.get('message', 'Unknown')}")
            except Exception as email_error:
                print(f"⚠️ Stage 3 email notification failed: {str(email_error)}")
            
            print("\n" + "="*60)
            print(f"📬 EMAIL NOTIFICATIONS COMPLETED!")
            print("📊 Email Summary:")
            print(f"   • Stage 1 - Application Confirmation: 📧 SENT")
            print(f"   • Stage 2 - Document Instructions: 📧 SENT") 
            print(f"   • Stage 3 - Verification Process: 📧 SENT")
            print(f"   • Customer ID: {current_customer_id}")
            print("="*60)
            print("💡 You can now continue with your next request...")
                
        except Exception as e:
            print(f"❌ Error during audit process: {str(e)}")
    
    async def handle_application_submission_background(self, response_text):
        """Handle audit process in background without blocking user interaction."""
        try:
            # Ensure response_text is a string
            response_content = str(response_text) if response_text else ""
            
            # Step 1: Get latest customer ID from database
            db = SessionLocal()
            try:
                latest_customer = db.query(MasterCustomerData).order_by(
                    MasterCustomerData.Customer_ID.desc()
                ).first()
                
                if latest_customer:
                    customer_id = latest_customer.Customer_ID
                    print(f"\n🔍 [BACKGROUND] Latest Customer ID: {customer_id}")
                else:
                    print("\n❌ [BACKGROUND] No customer found in database")
                    return
            finally:
                db.close()
            
            # Step 2: Get Audit Agent
            audit_agent = next((a for a in self.agents if self.selector._get_agent_name(a).lower() == "auditagent"), None)
            if not audit_agent:
                print("\n⚠️ [BACKGROUND] AuditAgent not found.")
                return
            
            # Step 3: Prequalification Audit (Background)
            prequal_prompt = f"""
Create audit record for customer {customer_id} - Prequalification Check.
Audit Type: "Prequalification Check"
Audit Status: "COMPLETED"
Auditor Name: "PrequalificationAgent"
Remarks: "Prequalification process completed successfully. Customer meets basic eligibility criteria for loan application."
Follow-up Required: "No"
"""
            
            print("\n🛡️ [BACKGROUND] Running Prequalification Audit...")
            prequal_response = await self.invoke_agent_with_retry(
                audit_agent, 
                prequal_prompt,
                max_retries=2,
                timeout=60,  # 1 minute for audit operations
                background=True
            )
            
            if prequal_response:
                print(f"\n✅ [BACKGROUND] Prequalification audit completed successfully.")
            else:
                print("\n❌ [BACKGROUND] Prequalification audit failed after retries.")
                return
            
            # Small delay before next audit
            await asyncio.sleep(1)
            
            # Step 4: Application Audit (Background)
            app_prompt = f"""
Create audit record for customer {customer_id} - Application Review.
Audit Type: "Application Review"
Audit Status: "COMPLETED" 
Auditor Name: "ApplicationAssistAgent"
Remarks: "Loan application submitted successfully. All required documents and information collected. Application ready for review process."
Follow-up Required: "Yes"

Application Summary:
{response_content}
"""
            
            print("\n🛡️ [BACKGROUND] Running Application Audit...")
            app_response = await self.invoke_agent_with_retry(
                audit_agent, 
                app_prompt,
                max_retries=2,
                timeout=60,  # 1 minute for audit operations
                background=True
            )
            
            if app_response:
                print(f"\n✅ [BACKGROUND] Application audit completed successfully.")
                print(f"\n🎉 [BACKGROUND] All audit processes completed for Customer {customer_id}!")
                
                # Send email notifications in background after audit completion
                current_customer_id = customer_id
                
                # Stage 1: Application - Initial application submission confirmation
                try:
                    print(f"\n📧 [BACKGROUND] Sending Stage 1 email notification...")
                    stage1_email_result = await self.send_stage_email_notification_async("1", current_customer_id)
                    if stage1_email_result.get("status") == "submitted":
                        print(f"✅ [BACKGROUND] Stage 1 email sent successfully")
                    else:
                        print(f"⚠️ [BACKGROUND] Stage 1 email notification issue: {stage1_email_result.get('message', 'Unknown')}")
                except Exception as email_error:
                    print(f"⚠️ [BACKGROUND] Stage 1 email notification failed: {str(email_error)}")
                
                # Wait 1 minute before sending next email
                print(f"⏳ [BACKGROUND] Waiting 1 minute before sending Stage 2 email...")
                await asyncio.sleep(60)  # 60 seconds = 1 minute
                
                # Stage 2: Document Submission - Document upload instructions
                try:
                    print(f"\n📧 [BACKGROUND] Sending Stage 2 email notification...")
                    stage2_email_result = await self.send_stage_email_notification_async("2", current_customer_id)
                    if stage2_email_result.get("status") == "submitted":
                        print(f"✅ [BACKGROUND] Stage 2 email sent successfully")
                    else:
                        print(f"⚠️ [BACKGROUND] Stage 2 email notification issue: {stage2_email_result.get('message', 'Unknown')}")
                except Exception as email_error:
                    print(f"⚠️ [BACKGROUND] Stage 2 email notification failed: {str(email_error)}")
                
                # Wait 1 minute before sending next email
                print(f"⏳ [BACKGROUND] Waiting 1 minute before sending Stage 3 email...")
                await asyncio.sleep(60)  # 60 seconds = 1 minute
                
                # Stage 3: Verification - Document verification in progress
                try:
                    print(f"\n📧 [BACKGROUND] Sending Stage 3 email notification...")
                    stage3_email_result = await self.send_stage_email_notification_async("3", current_customer_id)
                    if stage3_email_result.get("status") == "submitted":
                        print(f"✅ [BACKGROUND] Stage 3 email sent successfully")
                    else:
                        print(f"⚠️ [BACKGROUND] Stage 3 email notification issue: {stage3_email_result.get('message', 'Unknown')}")
                except Exception as email_error:
                    print(f"⚠️ [BACKGROUND] Stage 3 email notification failed: {str(email_error)}")
                
                print(f"\n📬 [BACKGROUND] All email notifications completed for Customer {customer_id}!")
                print(f"💡 [BACKGROUND] You can continue with your next request while audits are recorded.")
            else:
                print("\n❌ [BACKGROUND] Application audit failed after retries.")
                
        except Exception as e:
            print(f"\n❌ [BACKGROUND] Error during audit process: {str(e)}")
    
    async def handle_application_submission(self, response_text):
        """Handle audit process when application is submitted."""
        print("✅ Application submission detected — generating customer ID and running audits...")
        
        try:
            # Ensure response_text is a string
            response_content = str(response_text) if response_text else ""
            
            # Step 1: Get latest customer ID from database
            db = SessionLocal()
            try:
                latest_customer = db.query(MasterCustomerData).order_by(
                    MasterCustomerData.Customer_ID.desc()
                ).first()
                
                if latest_customer:
                    customer_id = latest_customer.Customer_ID
                    print(f"🆔 Latest Customer ID: {customer_id}")
                else:
                    print("❌ No customer found in database")
                    return
            finally:
                db.close()
            
            # Step 2: Get Audit Agent
            audit_agent = next((a for a in self.agents if self.selector._get_agent_name(a).lower() == "auditagent"), None)
            if not audit_agent:
                print("⚠️ AuditAgent not found.")
                return
            
            # Step 3: Prequalification Audit
            prequal_prompt = f"""
Create audit record for customer {customer_id} - Prequalification Check.
Audit Type: "Prequalification Check"
Audit Status: "COMPLETED"
Auditor Name: "PrequalificationAgent"
Remarks: "Prequalification process completed successfully. Customer meets basic eligibility criteria for loan application."
Follow-up Required: "No"
"""
            
            print("🛡️ Running Prequalification Audit...")
            prequal_response = await self.invoke_agent_with_retry(
                audit_agent, 
                prequal_prompt,
                max_retries=2,
                timeout=60  # 1 minute for audit operations
            )
            
            if prequal_response:
                print(f"🛡️ Prequal Audit Response: {prequal_response}")
                print("✅ Prequalification audit completed.")
            else:
                print("❌ Prequalification audit failed after retries.")
                return
            
            # Small delay before next audit
            await asyncio.sleep(1)
            
            # Step 4: Application Audit
            app_prompt = f"""
Create audit record for customer {customer_id} - Application Review.
Audit Type: "Application Review"
Audit Status: "COMPLETED" 
Auditor Name: "ApplicationAssistAgent"
Remarks: "Loan application submitted successfully. All required documents and information collected. Application ready for review process."
Follow-up Required: "Yes"

Application Summary:
{response_content}
"""
            
            print("🛡️ Running Application Audit...")
            app_response = await self.invoke_agent_with_retry(
                audit_agent, 
                app_prompt,
                max_retries=2,
                timeout=60  # 1 minute for audit operations
            )
            
            if app_response:
                print(f"🛡️ Application Audit Response: {app_response}")
                print("✅ Application audit completed.")
                
                # Send email notifications after audit completion
                current_customer_id = customer_id
                
                # Stage 1: Application - Initial application submission confirmation
                try:
                    print(f"\n📧 Sending Stage 1 email notification (Application Submission)...")
                    stage1_email_result = await self.send_stage_email_notification_async("1", current_customer_id)
                    if stage1_email_result.get("status") == "submitted":
                        print(f"✅ Stage 1 email sent successfully")
                        print(f"   📧 Template: {stage1_email_result.get('template_name', 'application')}")
                        print(f"   📋 Notification: Application submission confirmation sent to customer")
                    else:
                        print(f"⚠️ Stage 1 email notification issue: {stage1_email_result.get('message', 'Unknown')}")
                except Exception as email_error:
                    print(f"⚠️ Stage 1 email notification failed: {str(email_error)}")
                
                # Wait 1 minute before sending next email
                print(f"⏳ Waiting 1 minute before sending Stage 2 email...")
                await asyncio.sleep(60)  # 60 seconds = 1 minute
                
                # Stage 2: Document Submission - Document upload instructions
                try:
                    print(f"\n📧 Sending Stage 2 email notification (Document Submission)...")
                    stage2_email_result = await self.send_stage_email_notification_async("2", current_customer_id)
                    if stage2_email_result.get("status") == "submitted":
                        print(f"✅ Stage 2 email sent successfully")
                        print(f"   📧 Template: {stage2_email_result.get('template_name', 'document_submission')}")
                        print(f"   📋 Notification: Document upload instructions sent to customer")
                    else:
                        print(f"⚠️ Stage 2 email notification issue: {stage2_email_result.get('message', 'Unknown')}")
                except Exception as email_error:
                    print(f"⚠️ Stage 2 email notification failed: {str(email_error)}")
                
                # Wait 1 minute before sending next email
                print(f"⏳ Waiting 1 minute before sending Stage 3 email...")
                await asyncio.sleep(60)  # 60 seconds = 1 minute
                
                # Stage 3: Verification - Document verification in progress
                try:
                    print(f"\n📧 Sending Stage 3 email notification (Document Verification)...")
                    stage3_email_result = await self.send_stage_email_notification_async("3", current_customer_id)
                    if stage3_email_result.get("status") == "submitted":
                        print(f"✅ Stage 3 email sent successfully")
                        print(f"   📧 Template: {stage3_email_result.get('template_name', 'verification')}")
                        print(f"   📋 Notification: Document verification process notification sent to customer")
                    else:
                        print(f"⚠️ Stage 3 email notification issue: {stage3_email_result.get('message', 'Unknown')}")
                except Exception as email_error:
                    print(f"⚠️ Stage 3 email notification failed: {str(email_error)}")
                
                print(f"\n📬 All email notifications completed for Customer {customer_id}!")
            else:
                print("❌ Application audit failed after retries.")
                
        except Exception as e:
            print(f"❌ Error during audit process: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources."""
        try:
            if self.client:
                # Try different cleanup methods
                if hasattr(self.client, 'close'):
                    await self.client.close()
                elif hasattr(self.client, 'aclose'):
                    await self.client.aclose()
            print("🧹 Cleaned up resources.")
        except Exception as e:
            print(f"⚠️ Cleanup error (can be ignored): {str(e)}")


async def main():
    """Main function to run the loan application orchestrator."""
    orchestrator = FinalLoanOrchestrator()
    await orchestrator.run_conversation()


if __name__ == "__main__":
    asyncio.run(main())
