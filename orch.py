

import asyncio
import os
import json
import logging
import uuid
import hashlib
import random
import time

# Set up logging FIRST - before any Azure imports
import logging
import os
import sys
import json
import random
import asyncio

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Suppress Azure SDK logging completely
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.ERROR)
logging.getLogger('azure.identity').setLevel(logging.ERROR)
logging.getLogger('azure.ai.projects').setLevel(logging.ERROR)
logging.getLogger('azure.cosmos').setLevel(logging.ERROR)
logging.getLogger('semantic_kernel').setLevel(logging.ERROR)
logging.getLogger('loan_offer_generation_agent').setLevel(logging.ERROR)
logging.getLogger('root').setLevel(logging.ERROR)

from datetime import datetime, timezone
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MessageRole
from azure.cosmos.aio import CosmosClient
from azure.cosmos import exceptions

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.functions import KernelFunction, KernelArguments
from semantic_kernel.planners import FunctionCallingStepwisePlanner
from semantic_kernel.functions import kernel_function

from orch_config import *
from agents.identity_agent import create_identity_agent
from agents.income_agent import create_income_agent
from agents.gua import create_guarantor_agent
from agents.val_agent import create_valuation_agent
from agents.insp import create_collateral_inspection_agent
from agents.underwriting_agent import underwriting_agent
import sys

# Import custom template agent functions for email notifications
sys.path.append(os.path.join(os.path.dirname(__file__), 'Custom Customer Communication Agent'))
try:
    from custom_agent_functions import send_email_template
    print("✅ Custom template agent functions imported successfully")
except ImportError as e:
    print(f"⚠️ Could not import custom template agent functions: {e}")
    # Create a fallback function
    def send_email_template(customer_id: str, stage: str):
        print(f"📧 [FALLBACK] Would send email to customer {customer_id} for stage {stage}")
        return {"status": "fallback", "message": "Template function not available"}

# Import loan offer generation agent functions
sys.path.append(os.path.join(os.path.dirname(__file__), 'Loan Offer Generation Agent'))
try:
    from loan_offer_generation_agent import generate_loan_offer, assess_customer_loan
    print("✅ Loan offer generation agent functions imported successfully")
    LOAN_OFFER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Could not import loan offer generation agent functions: {e}")
    LOAN_OFFER_AVAILABLE = False
    
    # Create a fallback function
    def generate_loan_offer(customer_id: str, requested_amount=None):
        print(f"💰 [FALLBACK] Would generate loan offer for customer {customer_id}")
        return {
            "status": "fallback", 
            "eligibility": {"eligible": True, "recommended_amount": 500000, "max_eligible_amount": 1000000},
            "loan_options": [{"tenure_years": 25, "emi": 5000, "loan_amount": 500000, "interest_rate": 8.5}],
            "final_rate": 8.5,
            "collateral_info": {"property_value": 1000000, "property_type": "Residential"},
            "offer_summary": "Demo loan offer generated (fallback mode)"
        }
    
    def assess_customer_loan(customer_id: str, requested_amount=None):
        print(f"💰 [FALLBACK] Would assess loan for customer {customer_id}")
        return {"status": "fallback", "message": "Loan assessment function not available"}



# Azure config - using config values
ENDPOINT = ENDPOINT
RESOURCE_GROUP = RESOURCE_GROUP
SUBSCRIPTION_ID = SUBSCRIPTION_ID
PROJECT_NAME = PROJECT_NAME

# Azure OpenAI Configuration - from config
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", AZURE_OPENAI_DEPLOYMENT_NAME)
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", AZURE_OPENAI_ENDPOINT)
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", AZURE_OPENAI_API_KEY)

# Cosmos DB Configuration - from config
COSMOS_DB_ENDPOINT = COSMOS_DB_ENDPOINT
COSMOS_DB_KEY = COSMOS_DB_KEY
COSMOS_DB_DATABASE_NAME = COSMOS_DB_DATABASE_NAME
COSMOS_DB_CONTAINER_NAME = COSMOS_DB_CONTAINER_NAME

# Customer ID generation settings - from config
DEFAULT_CUSTOMER_ID_PREFIX = DEFAULT_CUSTOMER_ID_PREFIX

agent_results = {}
shared_context = {
    "applicant_name": "",
    "applicant_details": {},
    "risk_factors": [],
    "supporting_evidence": [],
    "recommendations": []
}

# Global customer tracking
current_customer_id = None

# --- Cosmos DB Service Class ---
class CosmosDBService:
    """Service class for managing Cosmos DB operations for loan verification data"""
    
    def __init__(self, endpoint=None, key=None, database_name=None, container_name=None):
        self.endpoint = endpoint or COSMOS_DB_ENDPOINT
        self.key = key or COSMOS_DB_KEY
        self.database_name = database_name or COSMOS_DB_DATABASE_NAME
        self.container_name = container_name or COSMOS_DB_CONTAINER_NAME
        self.cosmos_client = None
        self.database = None
        self.container = None
        
    async def initialize(self):
        """Initialize Cosmos DB client, database, and container"""
        try:
            print(f"🔗 Connecting to Cosmos DB...")
            print(f"   📍 Endpoint: {self.endpoint}")
            print(f"   🏷️  Database: {self.database_name}")
            print(f"   📦 Container: {self.container_name}")
            
            self.cosmos_client = CosmosClient(self.endpoint, self.key)
            print(f"🔑 Using account key authentication")
            
            self.database = await self.cosmos_client.create_database_if_not_exists(id=self.database_name)
            self.container = await self.database.create_container_if_not_exists(
                id=self.container_name,
                partition_key="/customer_id",
                offer_throughput=400
            )
            
            print(f"✅ Cosmos DB initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize Cosmos DB: {str(e)}")
            return False
    
    async def store_agent_result(self, customer_id: str, agent_name: str, agent_result: dict, 
                               applicant_name: str = None, additional_metadata: dict = None):
        """Store individual agent result to Cosmos DB with enhanced structure for underwriting data"""
        try:
            if not self.container:
                print("❌ Cosmos DB not initialized")
                return False
            
            # Create base document structure
            document = {
                "id": f"{customer_id}_{agent_name}",
                "customer_id": customer_id,
                "agent_name": agent_name,
                "applicant_name": applicant_name or "Unknown",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": agent_result.get("status", "unknown"),
                "summary": agent_result.get("summary", ""),
                "full_response": agent_result.get("full_response", ""),
                "processing_time_ms": agent_result.get("processing_time_ms", 0),
                "metadata": additional_metadata or {},
                "document_type": "agent_result"
            }
            
            # Add specialized fields for underwriting analysis
            if agent_name == "Underwriting Analysis" and additional_metadata:
                document.update({
                    "underwriting_data": {
                        "decision": additional_metadata.get("underwriting_decision"),
                        "risk_score": additional_metadata.get("risk_score"),
                        "risk_category": additional_metadata.get("risk_category"),
                        "confidence_level": additional_metadata.get("confidence_level"),
                        "verification_score": additional_metadata.get("verification_score"),
                        "financial_analysis": additional_metadata.get("financial_data", {}),
                        "risk_factors_count": additional_metadata.get("risk_factors_count", 0),
                        "recommendations_count": additional_metadata.get("recommendations_count", 0),
                        "analysis_timestamp": additional_metadata.get("analysis_timestamp")
                    },
                    "queryable_fields": {
                        "decision_category": additional_metadata.get("underwriting_decision", "").replace(" ", "_").lower(),
                        "risk_level": additional_metadata.get("risk_category", "").replace(" ", "_").lower(),
                        "risk_score_range": self._get_risk_score_range(additional_metadata.get("risk_score", 0)),
                        "income_bracket": self._get_income_bracket(additional_metadata.get("financial_data", {}).get("monthly_income", 0)),
                        "verification_completeness": "complete" if additional_metadata.get("verification_score", 0) >= 80 else "incomplete"
                    }
                })
            
            # Store document
            await self.container.create_item(body=document)
            print(f"✅ Stored {agent_name} result for customer {customer_id}")
            return True
            
        except exceptions.CosmosResourceExistsError:
            print(f"⚠️ Document already exists for {agent_name} - {customer_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to store {agent_name} result: {str(e)}")
            return False
    
    def _get_risk_score_range(self, risk_score: float) -> str:
        """Categorize risk score into ranges"""
        if risk_score >= 80: return "low_risk"
        elif risk_score >= 60: return "medium_risk"
        elif risk_score >= 40: return "high_risk"
        else: return "very_high_risk"
    
    def _get_income_bracket(self, monthly_income: float) -> str:
        """Categorize monthly income into brackets"""
        if monthly_income >= 200000: return "high_income"
        elif monthly_income >= 100000: return "upper_middle_income"
        elif monthly_income >= 50000: return "middle_income"
        elif monthly_income >= 25000: return "lower_middle_income"
        else: return "low_income"
    
    async def store_final_recommendation(self, customer_id: str, final_recommendation: dict, 
                                       all_agent_results: dict, shared_context: dict):
        """Store comprehensive final recommendation"""
        try:
            if not self.container:
                print("❌ Cosmos DB not initialized")
                return False
            
            document = {
                "id": f"{customer_id}_final_recommendation_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                "customer_id": customer_id,
                "applicant_name": shared_context.get("applicant_name", "Unknown"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "document_type": "final_recommendation",
                "recommendation": final_recommendation,
                "all_agent_results": all_agent_results,
                "shared_context": shared_context,
                "total_agents": len(all_agent_results),
                "successful_agents": sum(1 for r in all_agent_results.values() if r.get("status") == "passed"),
                "risk_factors_count": len(shared_context.get("risk_factors", [])),
                "evidence_count": len(shared_context.get("supporting_evidence", []))
            }
            
            await self.container.create_item(body=document)
            print(f"✅ Stored final recommendation for customer {customer_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to store final recommendation: {str(e)}")
            return False
    
    async def get_customer_results(self, customer_id: str):
        """Retrieve all results for a specific customer"""
        try:
            if not self.container:
                print("❌ Cosmos DB not initialized")
                return None
            
            query = "SELECT * FROM c WHERE c.customer_id = @customer_id ORDER BY c.timestamp DESC"
            parameters = [{"name": "@customer_id", "value": customer_id}]
            
            items = []
            async for item in self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ):
                items.append(item)
            
            return items
            
        except Exception as e:
            print(f"❌ Failed to retrieve customer results: {str(e)}")
            return None
    
    async def close(self):
        """Close Cosmos DB client"""
        if self.cosmos_client:
            await self.cosmos_client.close()

# Global Cosmos DB service instance
cosmos_service = CosmosDBService()

# --- Utility Functions ---
def load_instruction_from_file(filename: str) -> str:
    """Load instruction text from a file in the instructions directory"""
    try:
        instructions_dir = os.path.join(os.path.dirname(__file__), 'instructions')
        file_path = os.path.join(instructions_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"⚠️ Warning: Could not load instruction file {filename}: {e}")
        return f"Default instruction for {filename}"

def generate_customer_id(applicant_name: str = None) -> str:
    """Generate a unique customer ID in format CUST0001, CUST0002, etc."""
    import random
    
    # Generate a simple 4-digit sequential number
    customer_number = random.randint(1, 9999)
    customer_id = f"{DEFAULT_CUSTOMER_ID_PREFIX}{customer_number:04d}"
    
    return customer_id

def set_customer_id(customer_id: str = None, applicant_name: str = None):
    """Set the global customer ID for the current session"""
    global current_customer_id
    if customer_id:
        current_customer_id = customer_id
    else:
        current_customer_id = generate_customer_id(applicant_name)
    
    print(f"🆔 Customer ID set to: {current_customer_id}")
    return current_customer_id

# --- Semantic Kernel based Agent Runner ---
class AzureProjectAgentFunction:
    """Wrapper class to integrate Azure AI Project agents with Semantic Kernel"""
    
    def __init__(self, agent_id, project_client, name, key):
        self.agent_id = agent_id
        self.project_client = project_client
        self.name = name
        self.key = key
        
    async def invoke(self, prompt):
        """Invoke the agent with the given prompt and store results in Cosmos DB"""
        start_time = datetime.now()
        print(f"\n🤖 {self.name} Agent Starting...")
        print(f"📝 Query: {prompt[:150]}..." if len(prompt) > 150 else f"📝 Query: {prompt}")
        
        try:
            thread = self.project_client.agents.create_thread()
            _ = self.project_client.agents.create_message(
                thread_id=thread.id,
                role=MessageRole.USER,
                content=prompt
            )
            
            run = self.project_client.agents.create_and_process_run(
                thread_id=thread.id, 
                agent_id=self.agent_id
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if run.status == "failed":
                print(f"❌ {self.name} Agent failed")
                agent_result = {
                    "status": "failed", 
                    "summary": "Agent run failed or no response.",
                    "full_response": "",
                    "processing_time_ms": processing_time
                }
                agent_results[self.key] = agent_result
                
                # Store to Cosmos DB
                if current_customer_id:
                    await cosmos_service.store_agent_result(
                        current_customer_id, 
                        self.name, 
                        agent_result,
                        shared_context.get("applicant_name"),
                        {"run_status": run.status, "thread_id": thread.id}
                    )
                
                return {"success": False, "response": ""}
            
            response = self.project_client.agents.list_messages(
                thread_id=thread.id
            ).get_last_message_by_role(MessageRole.AGENT)
            
            if response:
                texts = [msg.text.value for msg in response.text_messages]
                full_response = "\n".join(texts)
                
                print(f"💬 {self.name} Agent Response:")
                print("-" * 60)
                print(full_response)
                print("-" * 60)
                
                agent_result = {
                    "status": "passed", 
                    "summary": full_response,
                    "full_response": full_response,
                    "processing_time_ms": processing_time
                }
                agent_results[self.key] = agent_result
                update_shared_context(self.key, full_response)
                
                # Store to Cosmos DB
                if current_customer_id:
                    await cosmos_service.store_agent_result(
                        current_customer_id, 
                        self.name, 
                        agent_result,
                        shared_context.get("applicant_name"),
                        {"run_status": run.status, "thread_id": thread.id, "response_length": len(full_response)}
                    )
                
                return {"success": True, "response": full_response}
            else:
                print(f"❌ {self.name} Agent: No response received")
                agent_result = {
                    "status": "no_response", 
                    "summary": "No message returned.",
                    "full_response": "",
                    "processing_time_ms": processing_time
                }
                agent_results[self.key] = agent_result
                
                # Store to Cosmos DB
                if current_customer_id:
                    await cosmos_service.store_agent_result(
                        current_customer_id, 
                        self.name, 
                        agent_result,
                        shared_context.get("applicant_name"),
                        {"run_status": run.status, "thread_id": thread.id}
                    )
                
                return {"success": False, "response": ""}
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            print(f"❌ {self.name} Agent error: {str(e)}")
            
            agent_result = {
                "status": "error", 
                "summary": f"Error occurred: {str(e)}",
                "full_response": "",
                "processing_time_ms": processing_time
            }
            agent_results[self.key] = agent_result
            
            # Store error to Cosmos DB
            if current_customer_id:
                await cosmos_service.store_agent_result(
                    current_customer_id, 
                    self.name, 
                    agent_result,
                    shared_context.get("applicant_name"),
                    {"error": str(e)}
                )
            
            return {"success": False, "response": ""}

async def run_agent_check_with_context(agent, base_prompt: str, name: str, key: str, project_client, previous_context=""):
    """Legacy function maintained for compatibility"""
    
    # Build enhanced prompt with previous agent findings
    context_prompt = ""
    if previous_context:
        context_prompt = f"\n\n--- PREVIOUS AGENT FINDINGS ---\n{previous_context}\n--- END PREVIOUS FINDINGS ---\n\n"
    
    # Add shared context information
    shared_info = ""
    if shared_context["applicant_name"]:
        shared_info += f"Applicant Name: {shared_context['applicant_name']}\n"
    if shared_context["risk_factors"]:
        shared_info += f"Known Risk Factors: {', '.join(shared_context['risk_factors'])}\n"
    if shared_context["supporting_evidence"]:
        shared_info += f"Supporting Evidence: {', '.join(shared_context['supporting_evidence'])}\n"
    
    if shared_info:
        context_prompt += f"--- SHARED CONTEXT ---\n{shared_info}--- END SHARED CONTEXT ---\n\n"
    
    enhanced_prompt = f"{base_prompt}{context_prompt}Please also consider the above context in your analysis and provide insights that might be relevant for subsequent verification steps."
    
    # Create agent function wrapper for this specific agent
    agent_func = AzureProjectAgentFunction(agent.id, project_client, name, key)
    result = await agent_func.invoke(enhanced_prompt)
    
    return result["success"], result.get("response", "")

def update_shared_context(agent_key: str, response: str):
    """Update shared context based on agent findings"""
    response_lower = response.lower()
    
    # Extract applicant name if found
    if agent_key == "identity" and not shared_context["applicant_name"]:
        lines = response.split('\n')
        for line in lines:
            if 'name' in line.lower() and ':' in line:
                potential_name = line.split(':')[-1].strip()
                if len(potential_name.split()) >= 2:
                    shared_context["applicant_name"] = potential_name
                    break
    
    # Identify risk factors
    risk_keywords = ['discrepancy', 'inconsistent', 'missing', 'insufficient', 'concern', 'risk', 'issue']
    for keyword in risk_keywords:
        if keyword in response_lower:
            risk_factor = f"{agent_key.title()}: {keyword} identified"
            if risk_factor not in shared_context["risk_factors"]:
                shared_context["risk_factors"].append(risk_factor)
    
    # Identify supporting evidence
    positive_keywords = ['verified', 'consistent', 'adequate', 'sufficient', 'valid', 'authentic']
    for keyword in positive_keywords:
        if keyword in response_lower:
            evidence = f"{agent_key.title()}: {keyword} documentation"
            if evidence not in shared_context["supporting_evidence"]:
                shared_context["supporting_evidence"].append(evidence)

def build_context_summary(up_to_agent: str):
    """Build summary of all previous agent findings for the next agent"""
    agent_order = ["identity", "income", "guarantor", "inspection", "valuation"]
    current_index = agent_order.index(up_to_agent)
    
    context_summary = ""
    for i in range(current_index):
        agent_key = agent_order[i]
        if agent_key in agent_results:
            context_summary += f"\n{agent_key.upper()} AGENT FINDINGS:\n"
            context_summary += f"{agent_results[agent_key]['summary']}\n"
            context_summary += "-" * 50 + "\n"
    
    return context_summary

# --- Summarize previous agent outputs and flag issues ---
def summarize_previous_agents(up_to_agent: str):
    agent_order = ["identity", "income", "guarantor", "inspection", "valuation"]
    current_index = agent_order.index(up_to_agent)
    summary_lines = []
    issue_found = False
    for i in range(current_index):
        agent_key = agent_order[i]
        if agent_key in agent_results:
            res = agent_results[agent_key]
            status = res['status'].lower()
            # Look for risk/issue keywords in summary
            summary_text = res['summary'].lower()
            risk_keywords = ['discrepancy', 'inconsistent', 'missing', 'insufficient', 'concern', 'risk', 'issue', 'fail', 'no_response']
            found_risk = any(kw in summary_text for kw in risk_keywords) or status != 'passed'
            if found_risk:
                issue_found = True
            summary_lines.append(f"{agent_key.title()} Check: {res['status'].capitalize()} - {'Issue found' if found_risk else 'No major issues'}.")
    if not summary_lines:
        return "No previous agent outputs to summarize.", False
    summary = "\n".join(summary_lines)
    return summary, issue_found

# --- Semantic Kernel Plugin Registration ---
class LoanVerificationPlugin:
    """A plugin for the Semantic Kernel containing functions for loan verification"""
    
    def __init__(self, project_client, agents):
        self.project_client = project_client
        self.agents = agents
    
    @kernel_function(
        description="Verify the identity of the loan applicant",
        name="verify_identity"
    )
    async def verify_identity(self, context: str = "") -> str:
        """Verify the identity of the loan applicant"""
        prompt = load_instruction_from_file("identity_verification_prompt.txt")
        
        if context:
            prompt = f"{prompt}\n\nPrevious context: {context}"
        
        agent_func = AzureProjectAgentFunction(
            self.agents["Identity"].id, self.project_client, "Identity Check", "identity"
        )
        result = await agent_func.invoke(prompt)
        
        return json.dumps(result)
    
    @kernel_function(
        description="Verify the income details of the loan applicant using previous identity findings",
        name="verify_income"
    )
    async def verify_income(self, identity_context: str = "") -> str:
        """Verify the income details of the loan applicant"""
        prompt = load_instruction_from_file("income_verification_prompt.txt")
        
        if identity_context:
            prompt = f"{prompt}\n\nIdentity verification context: {identity_context}"
        
        agent_func = AzureProjectAgentFunction(
            self.agents["Income"].id, self.project_client, "Income Check", "income"
        )
        result = await agent_func.invoke(prompt)
        
        return json.dumps(result)
    
    @kernel_function(
        description="Verify the guarantor information for the loan application using previous findings",
        name="verify_guarantor"
    )
    async def verify_guarantor(self, previous_context: str = "") -> str:
        """Verify the guarantor information for the loan application"""
        prompt = load_instruction_from_file("guarantor_verification_prompt.txt")
        
        if previous_context:
            prompt = f"{prompt}\n\nPrevious verification context: {previous_context}"
        
        agent_func = AzureProjectAgentFunction(
            self.agents["Guarantor"].id, self.project_client, "Guarantor Check", "guarantor"
        )
        result = await agent_func.invoke(prompt)
        
        return json.dumps(result)
    
    @kernel_function(
        description="Inspect the property collateral for the loan application using all previous findings",
        name="inspect_collateral"
    )
    async def inspect_collateral(self, verification_context: str = "") -> str:
        """Inspect the property collateral for the loan application"""
        prompt = load_instruction_from_file("collateral_inspection_prompt.txt")
        
        if verification_context:
            prompt = f"{prompt}\n\nPrevious verification findings: {verification_context}"
        
        agent_func = AzureProjectAgentFunction(
            self.agents["Inspection"].id, self.project_client, "Collateral Inspection Check", "inspection"
        )
        result = await agent_func.invoke(prompt)
        
        return json.dumps(result)
    
    @kernel_function(
        description="Evaluate the property valuation for the loan application using all verification findings",
        name="verify_valuation"
    )
    async def verify_valuation(self, all_context: str = "") -> str:
        """Evaluate the property valuation for the loan application"""
        prompt = load_instruction_from_file("valuation_verification_prompt.txt")
        
        if all_context:
            prompt = f"{prompt}\n\nAll previous verification findings: {all_context}"
        
        agent_func = AzureProjectAgentFunction(
            self.agents["Valuation"].id, self.project_client, "Valuation Check", "valuation"
        )
        result = await agent_func.invoke(prompt)
        
        return json.dumps(result)
    
    @kernel_function(
        description="Generate a comprehensive loan application summary and recommendation based on all agent findings",
        name="generate_final_recommendation"
    )
    async def generate_final_recommendation(self, all_results: str = "") -> str:
        """Generate final loan recommendation based on all verification results"""
        
        # Collect all agent results including underwriting and loan offer
        summary_parts = []
        total_issues = 0
        
        # Include all verification agents plus underwriting and loan offer
        all_agents = ["identity", "income", "guarantor", "inspection", "valuation", "underwriting", "loan_offer"]
        
        for agent_key in all_agents:
            if agent_key in agent_results:
                result = agent_results[agent_key]
                summary_parts.append(f"{agent_key.upper()}: {result['status']} - {result['summary'][:200]}...")
                
                # Count issues (skip loan_offer from issue counting since it's dependent on previous results)
                if agent_key != "loan_offer" and (result['status'] != 'passed' and result['status'] != 'completed' or 
                    any(risk_word in result['summary'].lower() for risk_word in ['risk', 'issue', 'concern', 'discrepancy', 'missing', 'failed', 'error'])):
                    total_issues += 1
        
        # Check underwriting decision for final recommendation
        underwriting_approved = False
        loan_offer_generated = False
        
        if "underwriting" in agent_results:
            underwriting_summary = agent_results["underwriting"]["summary"].lower()
            if "approved" in underwriting_summary or "conditional" in underwriting_summary:
                underwriting_approved = True
        
        if "loan_offer" in agent_results:
            loan_offer_summary = agent_results["loan_offer"]["summary"].lower()
            if "generated successfully" in loan_offer_summary or "completed" in agent_results["loan_offer"]["status"]:
                loan_offer_generated = True
        
        # Generate final recommendation based on underwriting and loan offer status
        if underwriting_approved and loan_offer_generated:
            recommendation = "APPROVED WITH LOAN OFFER - Complete verification and loan offer generated"
        elif underwriting_approved and not loan_offer_generated:
            recommendation = "APPROVED - Underwriting passed, loan offer pending"
        elif total_issues == 0:
            recommendation = "APPROVED - All verification steps passed successfully"
        elif total_issues <= 2:
            recommendation = "CONDITIONAL APPROVAL - Minor issues identified, review recommended"
        else:
            recommendation = "REJECTED - Multiple significant issues identified"
        
        # Include loan offer details if available
        loan_offer_details = {}
        if "loan_offer" in agent_results and agent_results["loan_offer"].get("offer_details"):
            loan_offer_details = agent_results["loan_offer"]["offer_details"]
        
        final_summary = {
            "applicant_name": shared_context.get("applicant_name", "Not identified"),
            "customer_id": current_customer_id,
            "recommendation": recommendation,
            "total_issues": total_issues,
            "underwriting_approved": underwriting_approved,
            "loan_offer_generated": loan_offer_generated,
            "loan_offer_details": loan_offer_details,
            "risk_factors": shared_context.get("risk_factors", []),
            "supporting_evidence": shared_context.get("supporting_evidence", []),
            "agent_summaries": summary_parts,
            "processing_timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(final_summary, indent=2)
    
    @kernel_function(
        description="Perform comprehensive underwriting analysis after all document verifications",
        name="perform_underwriting"
    )
    async def perform_underwriting(self, verification_context: str = "") -> str:
        """Perform underwriting analysis using all verification results"""
        print("\n🏦 Starting Underwriting Analysis...")
        
        try:
            # Initialize underwriting agent database connection
            underwriting_agent.initialize_database_connection()
            
            # Perform comprehensive underwriting analysis
            underwriting_result = underwriting_agent.perform_underwriting_analysis(
                customer_id=current_customer_id,
                verification_results=agent_results
            )
            
            # Store underwriting result in agent_results for consistency
            agent_results["underwriting"] = {
                "status": "completed",
                "summary": f"Underwriting Decision: {underwriting_result['underwriting_decision']['decision']} (Risk Score: {underwriting_result['risk_assessment']['risk_score']}/100)",
                "full_response": json.dumps(underwriting_result, indent=2),
                "processing_time_ms": 0
            }
            
            # Store to Cosmos DB with enhanced metadata
            if current_customer_id:
                try:
                    # Enhanced metadata for underwriting analysis
                    enhanced_metadata = {
                        "underwriting_decision": underwriting_result['underwriting_decision']['decision'],
                        "risk_score": underwriting_result['risk_assessment']['risk_score'],
                        "risk_category": underwriting_result['risk_assessment']['risk_category'],
                        "confidence_level": underwriting_result['underwriting_decision']['confidence'],
                        "verification_score": underwriting_result['verification_summary']['overall_verification_score'],
                        "total_agents_processed": underwriting_result['verification_summary']['total_agents'],
                        "passed_agents": underwriting_result['verification_summary']['passed_agents'],
                        "failed_agents": underwriting_result['verification_summary']['failed_agents'],
                        "financial_data": {
                            "monthly_income": underwriting_result['financial_analysis']['income_assessment'].get('monthly_income', 0),
                            "annual_income": underwriting_result['financial_analysis']['income_assessment'].get('annual_income', 0),
                            "income_stability": underwriting_result['financial_analysis']['income_assessment'].get('income_stability', 'Unknown'),
                            "emi_to_income_ratio": underwriting_result['financial_analysis']['ratios'].get('emi_to_income_ratio', 0),
                            "loan_to_income_ratio": underwriting_result['financial_analysis']['ratios'].get('loan_to_income_ratio', 0),
                            "affordability_status": underwriting_result['financial_analysis']['affordability'].get('affordability_status', 'Unknown')
                        },
                        "risk_factors_count": len(underwriting_result['risk_assessment'].get('risk_factors', [])),
                        "recommendations_count": len(underwriting_result.get('recommendations', [])),
                        "analysis_timestamp": underwriting_result['analysis_timestamp']
                    }
                    
                    # Store regular agent result
                    await cosmos_service.store_agent_result(
                        current_customer_id,
                        "Underwriting Analysis",
                        agent_results["underwriting"],
                        shared_context.get("applicant_name"),
                        enhanced_metadata
                    )
                    
                    print(f"✅ Stored Underwriting Analysis for customer {current_customer_id}")
                except Exception as e:
                    print(f"⚠️ Failed to store underwriting result: {str(e)}")
            
            # Display underwriting summary
            decision = underwriting_result['underwriting_decision']
            risk_assessment = underwriting_result['risk_assessment']
            
            print(f"\n📊 UNDERWRITING ANALYSIS COMPLETE")
            print("-" * 50)
            print(f"🎯 Decision: {decision['decision']}")
            print(f"📈 Risk Score: {risk_assessment['risk_score']}/100")
            print(f"🏷️  Risk Category: {risk_assessment['risk_category']}")
            print(f"✅ Confidence: {decision['confidence']}")
            
            if risk_assessment.get('risk_factors'):
                print(f"\n⚠️ Risk Factors:")
                for factor in risk_assessment['risk_factors']:
                    print(f"   • {factor}")
            
            print(f"\n💡 Recommendations:")
            for recommendation in underwriting_result.get('recommendations', []):
                print(f"   {recommendation}")
            
            print("-" * 50)
            
            return json.dumps(underwriting_result)
            
        except Exception as e:
            print(f"❌ Underwriting analysis failed: {str(e)}")
            
            # Create fallback result
            fallback_result = {
                "status": "error",
                "summary": f"Underwriting analysis failed: {str(e)}",
                "full_response": "",
                "processing_time_ms": 0
            }
            agent_results["underwriting"] = fallback_result
            
            return json.dumps({"error": str(e), "status": "failed"})
        
        finally:
            # Close underwriting agent database connection
            underwriting_agent.close_connection()
    
    @kernel_function(
        description="Generate comprehensive loan offer based on all verification and underwriting results",
        name="generate_loan_offer_with_context"
    )
    async def generate_loan_offer_with_context(self, underwriting_context: str = "") -> str:
        """Generate final loan offer based on all verification and underwriting results"""
        print("\n💰 Starting Loan Offer Generation...")
        
        try:
            # Check if underwriting was approved first
            underwriting_approved = False
            if "underwriting" in agent_results:
                underwriting_result = agent_results["underwriting"]
                if "approved" in underwriting_result.get("summary", "").lower():
                    underwriting_approved = True
                elif "conditional" in underwriting_result.get("summary", "").lower():
                    underwriting_approved = True  # Allow conditional approval
            
            if not underwriting_approved:
                print("❌ Loan offer cannot be generated - underwriting not approved")
                offer_result = {
                    "status": "rejected",
                    "summary": "Loan offer generation skipped - underwriting not approved",
                    "full_response": json.dumps({
                        "offer_status": "REJECTED",
                        "reason": "Application did not pass underwriting requirements",
                        "customer_id": current_customer_id
                    }),
                    "processing_time_ms": 0
                }
                agent_results["loan_offer"] = offer_result
                return json.dumps(offer_result)
            
            # Generate loan offer using the imported function
            print(f"✅ Underwriting approved - proceeding with loan offer generation")
            
            # Call the loan offer generation function
            if LOAN_OFFER_AVAILABLE:
                print("🔗 Using full loan offer generation system...")
                loan_offer_result = generate_loan_offer(current_customer_id)
            else:
                print("🔗 Using fallback loan offer generation...")
                loan_offer_result = generate_loan_offer(current_customer_id)
            
            if loan_offer_result:
                offer_summary = {
                    "status": "completed",
                    "summary": f"Loan offer generated successfully for customer {current_customer_id}",
                    "offer_details": {
                        "customer_id": current_customer_id,
                        "eligibility": loan_offer_result.get("eligibility", {}),
                        "loan_options": loan_offer_result.get("loan_options", []),
                        "final_rate": loan_offer_result.get("final_rate", 0),
                        "collateral_info": loan_offer_result.get("collateral_info", {}),
                        "offer_summary": loan_offer_result.get("offer_summary", "")
                    },
                    "processing_time_ms": 0
                }
                
                # Store loan offer result
                agent_results["loan_offer"] = offer_summary
                
                # Store to Cosmos DB
                if current_customer_id:
                    try:
                        await cosmos_service.store_agent_result(
                            current_customer_id,
                            "Loan Offer Generation",
                            offer_summary,
                            shared_context.get("applicant_name"),
                            {
                                "offer_status": "APPROVED",
                                "eligibility_status": loan_offer_result.get("eligibility", {}).get("eligible", False),
                                "recommended_amount": loan_offer_result.get("eligibility", {}).get("recommended_amount", 0),
                                "max_eligible_amount": loan_offer_result.get("eligibility", {}).get("max_eligible_amount", 0),
                                "final_interest_rate": loan_offer_result.get("final_rate", 0),
                                "property_value": loan_offer_result.get("collateral_info", {}).get("property_value", 0),
                                "loan_options_count": len(loan_offer_result.get("loan_options", [])),
                                "generation_timestamp": datetime.now().isoformat()
                            }
                        )
                        print(f"✅ Stored Loan Offer Generation result for customer {current_customer_id}")
                    except Exception as e:
                        print(f"⚠️ Failed to store loan offer result to Cosmos DB: {str(e)}")
                
                print(f"✅ Loan offer generated successfully!")
                return json.dumps(offer_summary)
                
            else:
                error_result = {
                    "status": "error",
                    "summary": f"Failed to generate loan offer for customer {current_customer_id}",
                    "full_response": "",
                    "processing_time_ms": 0
                }
                agent_results["loan_offer"] = error_result
                return json.dumps(error_result)
                
        except Exception as e:
            print(f"❌ Loan offer generation failed: {str(e)}")
            
            # Create fallback result
            fallback_result = {
                "status": "error",
                "summary": f"Loan offer generation failed: {str(e)}",
                "full_response": "",
                "processing_time_ms": 0
            }
            agent_results["loan_offer"] = fallback_result
            
            return json.dumps({"error": str(e), "status": "failed"})

# --- Main async function with Semantic Kernel Orchestrator ---
async def main():
    # Get customer ID from user input
    global current_customer_id
    current_customer_id = await get_customer_id()
    
    # Initialize Cosmos DB first
    print("\n🔧 Initializing Cosmos DB...")
    cosmos_initialized = await cosmos_service.initialize()
    if not cosmos_initialized:
        print("⚠️ Continuing without Cosmos DB storage...")

    print(f"\n🎯 Starting verification process for Customer: {current_customer_id}")
    print("=" * 60)
    
    creds = DefaultAzureCredential()
    project_client = AIProjectClient(
        endpoint=ENDPOINT,
        resource_group_name=RESOURCE_GROUP,
        subscription_id=SUBSCRIPTION_ID,
        project_name=PROJECT_NAME,
        credential=creds,
    )

    # Get Cognitive Search connection ID
    conn_id = next(conn.id for conn in project_client.connections.list() if conn.connection_type == "CognitiveSearch")

    # Create agents
    print("🔧 Creating agents...")
    agents = {
        "Identity": create_identity_agent(project_client, conn_id, IDENTITY_INDEX),
        "Income": create_income_agent(project_client, conn_id, INCOME_INDEX),
        "Guarantor": create_guarantor_agent(project_client, conn_id, GUARANTOR_INDEX),
        "Inspection": create_collateral_inspection_agent(project_client, conn_id, INSPECTION_INDEX),
        "Valuation": create_valuation_agent(project_client, conn_id, VALUATION_INDEX),
    }
    print("✅ All agents created.")

    # Initialize Semantic Kernel with proper autonomous orchestration
    try:
        print("\n🔧 Initializing Semantic Kernel...")
        kernel = Kernel()
        
        # Add Azure OpenAI Chat service to kernel
        ai_service = AzureChatCompletion(
            deployment_name=AZURE_OPENAI_DEPLOYMENT_NAME,
            endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY
        )
        kernel.add_service(ai_service)
        
        # Create and register the Loan Verification Plugin
        loan_verification_plugin = LoanVerificationPlugin(project_client, agents)
        kernel.add_plugin(loan_verification_plugin, plugin_name="loan_verification")
        
        print("✅ Semantic Kernel initialized.")
        
        # Start autonomous loan verification process
        print("\n🚀 Starting Autonomous Loan Verification...\n")
        
        try:
            # Direct kernel function invocation approach
            # Get the plugin from kernel  
            loan_plugin = kernel.get_plugin("loan_verification")
            
            # Execute functions in sequence with context passing
            context = ""
            
            print("1️⃣ Identity Verification...")
            identity_result = await kernel.invoke(loan_plugin["verify_identity"], context=context)
            context += f"Identity Verification: {identity_result}\n\n"
            print("✅ Identity completed\n")
            
            print("2️⃣ Income Verification...")
            income_result = await kernel.invoke(loan_plugin["verify_income"], context=context)
            context += f"Income Verification: {income_result}\n\n" 
            print("✅ Income completed\n")
            
            print("3️⃣ Guarantor Verification...")
            guarantor_result = await kernel.invoke(loan_plugin["verify_guarantor"], previous_context=context)
            context += f"Guarantor Verification: {guarantor_result}\n\n"
            print("✅ Guarantor completed\n")
            
            print("4️⃣ Collateral Inspection...")
            inspection_result = await kernel.invoke(loan_plugin["inspect_collateral"], verification_context=context)
            context += f"Inspection: {inspection_result}\n\n"
            print("✅ Inspection completed\n")
            
            print("5️⃣ Property Valuation...")
            valuation_result = await kernel.invoke(loan_plugin["verify_valuation"], all_context=context)
            context += f"Valuation: {valuation_result}\n\n"
            print("✅ Valuation completed\n")
            
            # Send Stage 4 Email: Document Approval (All verifications completed)
            try:
                print("📧 Sending Stage 4 Email: Document Approval...")
                email_result = send_email_template(current_customer_id, "document_approval")
                print(f"✅ Stage 4 email sent: {email_result.get('status', 'unknown')}")
            except Exception as e:
                print(f"⚠️ Failed to send Stage 4 email: {str(e)}")
            
            print("6️⃣ Underwriting Analysis...")
            underwriting_result = await kernel.invoke(loan_plugin["perform_underwriting"], verification_context=context)
            context += f"Underwriting: {underwriting_result}\n\n"
            print("✅ Underwriting completed\n")
            
            # Send Stage 5 Email: Approval (Only if underwriting is approved)
            try:
                # Check if underwriting was approved before sending approval email
                if "underwriting" in agent_results:
                    underwriting_summary = agent_results["underwriting"]["summary"].lower()
                    if "approved" in underwriting_summary or "conditional" in underwriting_summary:
                        print("📧 Sending Stage 5 Email: Loan Approval...")
                        email_result = send_email_template(current_customer_id, "approval")
                        print(f"✅ Stage 5 email sent: {email_result.get('status', 'unknown')}")
                    else:
                        print("⚠️ Stage 5 email not sent - underwriting not approved")
                else:
                    print("⚠️ Stage 5 email not sent - underwriting result not found")
            except Exception as e:
                print(f"⚠️ Failed to send Stage 5 email: {str(e)}")
            
            print("7️⃣ Loan Offer Generation...")
            loan_offer_result = await kernel.invoke(loan_plugin["generate_loan_offer_with_context"], underwriting_context=context)
            context += f"Loan Offer: {loan_offer_result}\n\n"
            print("✅ Loan Offer Generation completed\n")
            
            # Send Stage 6 Email: Loan Application Number (Only if loan offer was generated successfully)
            try:
                # Check if loan offer was generated successfully before sending final email
                if "loan_offer" in agent_results:
                    loan_offer_status = agent_results["loan_offer"]["status"].lower()
                    if "completed" in loan_offer_status and "generated successfully" in agent_results["loan_offer"]["summary"].lower():
                        print("📧 Sending Stage 6 Email: Loan Application Number...")
                        email_result = send_email_template(current_customer_id, "loan_application_number")
                        print(f"✅ Stage 6 email sent: {email_result.get('status', 'unknown')}")
                    else:
                        print("⚠️ Stage 6 email not sent - loan offer not generated successfully")
                else:
                    print("⚠️ Stage 6 email not sent - loan offer result not found")
            except Exception as e:
                print(f"⚠️ Failed to send Stage 6 email: {str(e)}")
            
            print("8️⃣ Final Recommendation...")
            final_result = await kernel.invoke(loan_plugin["generate_final_recommendation"], all_results=context)
            print("✅ Recommendation completed")
            
            
            # Store final recommendation to Cosmos DB
            if cosmos_initialized and current_customer_id:
                try:
                    final_recommendation_data = json.loads(str(final_result))
                    await cosmos_service.store_final_recommendation(
                        current_customer_id,
                        final_recommendation_data,
                        agent_results,
                        shared_context
                    )
                    print(f"✅ Final recommendation stored to Cosmos DB for customer {current_customer_id}")
                except Exception as e:
                    print(f"⚠️ Failed to store final recommendation to Cosmos DB: {str(e)}")
            
            
            print("\n✅ Autonomous orchestration completed!")
            print(f"\n📋 FINAL RECOMMENDATION:")
            print("=" * 60)
            
            # Parse and format the final result nicely
            try:
                final_data = json.loads(str(final_result))
                
                print(f"👤 Applicant: {final_data.get('applicant_name', 'Not identified')}")
                print(f"🆔 Customer ID: {final_data.get('customer_id', 'Not available')}")
                print(f"📊 Decision: {final_data.get('recommendation', 'No recommendation')}")
                print(f"⚠️  Total Issues: {final_data.get('total_issues', 0)}")
                print(f"🏦 Underwriting Approved: {'✅ Yes' if final_data.get('underwriting_approved') else '❌ No'}")
                print(f"💰 Loan Offer Generated: {'✅ Yes' if final_data.get('loan_offer_generated') else '❌ No'}")
                
                # Display loan offer details if available
                if final_data.get('loan_offer_details'):
                    loan_details = final_data['loan_offer_details']
                    print(f"\n💰 LOAN OFFER DETAILS:")
                    print("-" * 40)
                    
                    eligibility = loan_details.get('eligibility', {})
                    if eligibility:
                        print(f"   📈 Eligible: {'✅ Yes' if eligibility.get('eligible') else '❌ No'}")
                        if eligibility.get('recommended_amount'):
                            print(f"   💵 Recommended Amount: ₹{eligibility['recommended_amount']:,.2f}")
                        if eligibility.get('max_eligible_amount'):
                            print(f"   🏆 Max Eligible Amount: ₹{eligibility['max_eligible_amount']:,.2f}")
                    
                    if loan_details.get('final_rate'):
                        print(f"   📊 Interest Rate: {loan_details['final_rate']:.2f}%")
                    
                    loan_options = loan_details.get('loan_options', [])
                    if loan_options:
                        print(f"   📋 Loan Options Available: {len(loan_options)} tenure options")
                        # Show the recommended option (usually 25 years or middle option)
                        if len(loan_options) >= 3:
                            recommended_option = loan_options[2]  # Usually 25-year option
                            print(f"   🌟 Recommended EMI: ₹{recommended_option.get('emi', 0):,.2f} for {recommended_option.get('tenure_years', 0)} years")
                    
                    collateral = loan_details.get('collateral_info', {})
                    if collateral and collateral.get('property_value'):
                        print(f"   🏠 Property Value: ₹{collateral['property_value']:,.2f}")
                
                if final_data.get('risk_factors'):
                    print(f"\n🔴 Risk Factors ({len(final_data['risk_factors'])}):")
                    for risk in final_data['risk_factors']:
                        print(f"   • {risk}")
                
                if final_data.get('supporting_evidence'):
                    print(f"\n🟢 Supporting Evidence ({len(final_data['supporting_evidence'])}):")
                    for evidence in final_data['supporting_evidence']:
                        print(f"   • {evidence}")
                
                print(f"\n📄 Agent Processing Summary:")
                for i, summary in enumerate(final_data.get('agent_summaries', []), 1):
                    agent_name = summary.split(':')[0]
                    status = summary.split(':')[1].split(' - ')[0].strip() if ':' in summary else "Unknown"
                    print(f"   {i}. {agent_name}: {status}")
                    
            except (json.JSONDecodeError, Exception) as e:
                print("Raw output:")
                print(str(final_result))
            
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print("🔄 Fallback to legacy processing...")
            await legacy_sequential_processing(agents, project_client)
            
    except Exception as e:
        print(f"❌ Kernel setup error: {str(e)}")
        print("🔄 Fallback to legacy processing...")
        await legacy_sequential_processing(agents, project_client)

    # Display final results
    await display_final_results()

    # Close Cosmos DB connection
    await cosmos_service.close()
    print("✅ Process completed")

async def legacy_sequential_processing(agents, project_client):
    """Legacy sequential processing as final fallback"""
    print("\n🔄 LEGACY PROCESSING")
    
    # Execute agents sequentially with context
    success, _ = await run_agent_check_with_context(
        agents["Identity"],
        load_instruction_from_file("identity_verification_prompt.txt"), 
        "Identity Check", "identity", project_client
    )
    
    if success:
        context = build_context_summary("income")
        success, _ = await run_agent_check_with_context(
            agents["Income"],
            load_instruction_from_file("income_verification_prompt.txt"),
            "Income Check", "income", project_client, context
        )
        
        if success:
            context = build_context_summary("guarantor")
            success, _ = await run_agent_check_with_context(
                agents["Guarantor"],
                load_instruction_from_file("guarantor_verification_prompt.txt"),
                "Guarantor Check", "guarantor", project_client, context
            )
            
            if success:
                context = build_context_summary("inspection")
                success, _ = await run_agent_check_with_context(
                    agents["Inspection"],
                    "You are an expert in property inspection for loan applications. Review the provided inspection video or images and assess whether the house is maintained well or not. Focus on the overall maintenance status, structural condition, and any visible damages or deterioration.",
                    "Collateral Inspection Check", "inspection", project_client, context
                )
                
                if success:
                    context = build_context_summary("valuation")
                    success, _ = await run_agent_check_with_context(
                        agents["Valuation"],
                        "You are an expert in property valuation for loan applications. Analyze the sale deed and any supporting documents. Estimate the property's market value using an 11% annual appreciation from the last sale year. Consider the applicant's income, inspection findings, and overall risk profile when providing your valuation assessment.",
                        "Valuation Check", "valuation", project_client, context
                    )
                    
                    if success:
                        # Send Stage 4 Email: Document Approval (All verifications completed)
                        try:
                            print("📧 Sending Stage 4 Email: Document Approval...")
                            email_result = send_email_template(current_customer_id, "document_approval")
                            print(f"✅ Stage 4 email sent: {email_result.get('status', 'unknown')}")
                        except Exception as e:
                            print(f"⚠️ Failed to send Stage 4 email: {str(e)}")
                        
                        # Perform underwriting analysis
                        print("\n🏦 Performing Underwriting Analysis...")
                        try:
                            underwriting_agent.initialize_database_connection()
                            underwriting_result = underwriting_agent.perform_underwriting_analysis(
                                customer_id=current_customer_id,
                                verification_results=agent_results
                            )
                            
                            agent_results["underwriting"] = {
                                "status": "completed",
                                "summary": f"Underwriting Decision: {underwriting_result['underwriting_decision']['decision']}",
                                "full_response": json.dumps(underwriting_result, indent=2),
                                "processing_time_ms": 0
                            }
                            
                            print(f"✅ Underwriting Complete: {underwriting_result['underwriting_decision']['decision']}")
                            
                            # Send Stage 5 Email: Approval (Only if underwriting is approved)
                            try:
                                underwriting_summary = agent_results["underwriting"]["summary"].lower()
                                if "approved" in underwriting_summary or "conditional" in underwriting_summary:
                                    print("📧 Sending Stage 5 Email: Loan Approval...")
                                    email_result = send_email_template(current_customer_id, "approval")
                                    print(f"✅ Stage 5 email sent: {email_result.get('status', 'unknown')}")
                                else:
                                    print("⚠️ Stage 5 email not sent - underwriting not approved")
                            except Exception as e:
                                print(f"⚠️ Failed to send Stage 5 email: {str(e)}")
                            
                        except Exception as e:
                            print(f"⚠️ Underwriting failed: {str(e)}")
                            agent_results["underwriting"] = {
                                "status": "error",
                                "summary": f"Underwriting failed: {str(e)}",
                                "full_response": "",
                                "processing_time_ms": 0
                            }
                        finally:
                            underwriting_agent.close_connection()
                        
                        # Generate loan offer (if underwriting approved)
                        if "underwriting" in agent_results and "approved" in agent_results["underwriting"]["summary"].lower():
                            try:
                                print("\n💰 Generating Loan Offer...")
                                if LOAN_OFFER_AVAILABLE:
                                    loan_offer_result = generate_loan_offer(current_customer_id)
                                else:
                                    loan_offer_result = generate_loan_offer(current_customer_id)  # Fallback
                                
                                if loan_offer_result:
                                    agent_results["loan_offer"] = {
                                        "status": "completed",
                                        "summary": f"Loan offer generated successfully for customer {current_customer_id}",
                                        "offer_details": loan_offer_result,
                                        "processing_time_ms": 0
                                    }
                                    
                                    # Send Stage 6 Email: Loan Application Number
                                    try:
                                        print("📧 Sending Stage 6 Email: Loan Application Number...")
                                        email_result = send_email_template(current_customer_id, "loan_application_number")
                                        print(f"✅ Stage 6 email sent: {email_result.get('status', 'unknown')}")
                                    except Exception as e:
                                        print(f"⚠️ Failed to send Stage 6 email: {str(e)}")
                                        
                                    print(f"✅ Loan Offer Generated Successfully!")
                                else:
                                    print("⚠️ Loan offer generation failed")
                                    
                            except Exception as e:
                                print(f"⚠️ Loan offer generation failed: {str(e)}")
                        
                        print("\n✅ Legacy processing completed!")

async def display_final_results():
    """Display comprehensive final results"""
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE FINAL RESULTS")
    print("=" * 70)
    
    if current_customer_id:
        print(f"\n🆔 Customer ID: {current_customer_id}")
    
    # Agent results summary
    print("\n📋 VERIFICATION SUMMARY")
    print("-" * 40)
    for key, result in agent_results.items():
        status_icon = "✅" if result['status'] == 'passed' else "❌"
        processing_time = result.get('processing_time_ms', 0)
        print(f"\n{status_icon} {key.upper()}: {result['status'].capitalize()} ({processing_time:.0f}ms)")
        
        summary_snippet = result['summary'][:200] + "..." if len(result['summary']) > 200 else result['summary']
        print(f"   📝 Summary: {summary_snippet}")
    
    # Risk vs Evidence Analysis
    total_risks = len(shared_context.get('risk_factors', []))
    total_evidence = len(shared_context.get('supporting_evidence', []))
    
    print(f"\n📊 RISK ANALYSIS")
    print("-" * 40)
    print(f"⚠️  Total Risk Factors: {total_risks}")
    print(f"✅ Total Supporting Evidence: {total_evidence}")
    print(f"📈 Evidence-to-Risk Ratio: {total_evidence/max(total_risks, 1):.2f}")
    
    # Final recommendation logic
    total_passed = sum(1 for r in agent_results.values() if r['status'] == 'passed')
    total_agents = len(agent_results)
    
    print(f"\n📊 VERIFICATION COMPLETION")
    print("-" * 40)
    print(f"✅ Passed Verifications: {total_passed}/{total_agents}")
    print(f"📊 Success Rate: {(total_passed/total_agents)*100:.1f}%")
    
    # Final decision - prioritize underwriting and loan offer results
    print(f"\n🎯 FINAL DECISION")
    print("-" * 40)
    
    # Check if underwriting and loan offer were successful
    underwriting_approved = False
    loan_offer_generated = False
    
    if "underwriting" in agent_results:
        underwriting_summary = agent_results["underwriting"]["summary"].lower()
        if "approved" in underwriting_summary:
            underwriting_approved = True
    
    if "loan_offer" in agent_results:
        loan_offer_status = agent_results["loan_offer"]["status"].lower()
        if "completed" in loan_offer_status and "generated successfully" in agent_results["loan_offer"]["summary"].lower():
            loan_offer_generated = True
    
    # Final decision based on modern underwriting and loan offer
    if underwriting_approved and loan_offer_generated:
        decision = "🎉 LOAN APPROVED WITH OFFER"
        reason = "Underwriting approved and loan offer successfully generated"
    elif underwriting_approved and not loan_offer_generated:
        decision = "✅ LOAN APPROVED"
        reason = "Underwriting approved, loan offer generation pending"
    elif total_passed == total_agents and total_risks <= 3:
        decision = "🎉 LOAN APPROVED"
        reason = "All verifications passed with minimal risk factors"
    elif total_passed == total_agents and total_risks <= 6:
        decision = "⚠️ CONDITIONAL APPROVAL"
        reason = "All verifications passed but with some risk factors to monitor"
    elif total_passed >= total_agents * 0.8:
        decision = "⚠️ CONDITIONAL APPROVAL"
        reason = "Most verifications passed, requires additional review"
    else:
        decision = "❌ LOAN REJECTED"
        reason = "Multiple verification failures or significant risk factors"
    
    print(f"{decision}")
    print(f"📋 Reason: {reason}")
    
    if shared_context.get('applicant_name'):
        print(f"\n👤 APPLICANT SUMMARY")
        print("-" * 40)
        print(f"Name: {shared_context['applicant_name']}")
        print(f"Risk Score: {total_risks}/10")
        print(f"Evidence Score: {total_evidence}/10")

# --- Utility function to retrieve customer data from Cosmos DB ---
async def retrieve_customer_data(customer_id: str):
    """Retrieve and display all stored data for a specific customer"""
    print(f"\n🔍 RETRIEVING DATA FOR CUSTOMER: {customer_id}")
    print("=" * 60)
    
    if not await cosmos_service.initialize():
        print("❌ Could not connect to Cosmos DB")
        return
    
    results = await cosmos_service.get_customer_results(customer_id)
    
    if not results:
        print("❌ No data found for this customer")
        return
    
    print(f"📊 Found {len(results)} records")
    
    agent_records = [r for r in results if r.get('document_type') == 'agent_result']
    final_records = [r for r in results if r.get('document_type') == 'final_recommendation']
    
    print(f"\n📝 AGENT RESULTS ({len(agent_records)} records):")
    print("-" * 40)
    for record in agent_records:
        timestamp = record.get('timestamp', 'Unknown')[:19]  # Format timestamp
        status = record.get('status', 'Unknown')
        processing_time = record.get('processing_time_ms', 0)
        print(f"🤖 {record.get('agent_name', 'Unknown')} - {status} - {timestamp} ({processing_time:.0f}ms)")
        summary = record.get('summary', '')[:100] + "..." if len(record.get('summary', '')) > 100 else record.get('summary', '')
        print(f"   📄 {summary}")
    
    if final_records:
        print(f"\n🎯 FINAL RECOMMENDATIONS ({len(final_records)} records):")
        print("-" * 40)
        for record in final_records:
            timestamp = record.get('timestamp', 'Unknown')[:19]
            recommendation = record.get('recommendation', {})
            print(f"📋 {timestamp}: {recommendation.get('recommendation', 'No recommendation')}")
    
    await cosmos_service.close()
    return results

async def get_customer_id():
    """Get customer ID from user input"""
    print("🏦 LOAN VERIFICATION SYSTEM")
    print("=" * 50)
    print("📋 Customer Identification Required")
    print("-" * 30)
    
    while True:
        customer_id = input("\n🆔 Please enter Customer ID (format: CUSTXXXX, e.g., CUST1234): ").strip().upper()
        
        if not customer_id:
            print("❌ Customer ID cannot be empty. Please try again.")
            continue
        
        if len(customer_id) < 4:
            print("❌ Customer ID too short. Please use format CUSTXXXX.")
            continue
            
        if not customer_id.startswith("CUST"):
            print("❌ Customer ID must start with 'CUST'. Please use format CUSTXXXX.")
            continue
        
        # Validate the numeric part
        numeric_part = customer_id[4:]
        if not numeric_part.isdigit():
            print("❌ Customer ID must end with numbers. Please use format CUSTXXXX.")
            continue
        
        # Confirm with user
        print(f"\n✅ Customer ID: {customer_id}")
        confirm = input("🤔 Is this correct? (y/n): ").strip().lower()
        
        if confirm in ['y', 'yes']:
            return customer_id
        else:
            print("🔄 Let's try again...")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "retrieve":
            if len(sys.argv) > 2:
                # Retrieve data for specific customer
                customer_id = sys.argv[2].upper()
                asyncio.run(retrieve_customer_data(customer_id))
            else:
                # Ask for customer ID interactively
                print("🏦 CUSTOMER DATA RETRIEVAL")
                print("=" * 40)
                customer_id = input("🆔 Enter Customer ID to retrieve data: ").strip().upper()
                if customer_id:
                    asyncio.run(retrieve_customer_data(customer_id))
                else:
                    print("❌ No Customer ID provided. Exiting.")
        else:
            print("Usage:")
            print("  python integrated_try.py                     - Run main agent workflow")
            print("  python integrated_try.py retrieve            - Retrieve customer data (interactive)")
            print("  python integrated_try.py retrieve CUST5410   - Retrieve specific customer data")
    else:
        # Run main workflow
        asyncio.run(main())