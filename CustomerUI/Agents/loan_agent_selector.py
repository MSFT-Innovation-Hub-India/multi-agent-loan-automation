"""
Simple Intent-Based Agent Selection
A working implementation that doesn't inherit from SequentialSelectionStrategy
to avoid Pydantic validation issues.
"""

from typing import List, Optional, Any
import asyncio


class LoanAgentSelector:
    """
    Intent-based agent selector for loan application routing.
    
    Routing Rules:
    1. "eligibility", "prequalify", "check" → PrequalificationAgent
    2. "apply", "application", "loan application", "status", "audit", "progress" → ApplicationAssistAgent  
    3. Default → First agent in list
    """
    
    def __init__(self):
        # Intent detection keywords
        self.prequalify_words = ["eligibility", "eligible", "prequalify", "qualify", "can i get", "check eligibility", "check my eligibility"]
        self.apply_words = ["apply", "application", "start application", "apply for loan", "loan application", "status", "audit", "progress", "loan status", "show status", "check status", "application status", "track", "tracking", "customer", "check my status", "show my status", "check my loan", "show my loan"]
        
        # Customer ID patterns (CUST followed by numbers)
        import re
        self.customer_id_pattern = re.compile(r'cust\d+', re.IGNORECASE)
        
        # Form data patterns - these should NOT go to LoanStatusCheckAgent
        # These are actual application form fields, not prequalification data
        self.form_data_patterns = [
            re.compile(r'fathers?\s+name:', re.IGNORECASE),
            re.compile(r'date of birth:', re.IGNORECASE),
            re.compile(r'dob:', re.IGNORECASE),
            re.compile(r'address:', re.IGNORECASE),
            re.compile(r'pincode:', re.IGNORECASE),
            re.compile(r'nationality:', re.IGNORECASE),
            re.compile(r'marital status:', re.IGNORECASE),
            re.compile(r'gender:', re.IGNORECASE),
            re.compile(r'alternate mobile:', re.IGNORECASE),
            re.compile(r'city:', re.IGNORECASE),
            re.compile(r'state:', re.IGNORECASE),
            re.compile(r'\d+\.\s*[a-z]', re.IGNORECASE),  # Numbered list items like "1. Full Name:"
        ]
        
        # Prequalification data patterns - these should stay with PrequalificationAgent
        self.prequalification_data_patterns = [
            re.compile(r'full name:.*age:.*employment.*income', re.IGNORECASE | re.DOTALL),
            re.compile(r'name:.*age:.*monthly income', re.IGNORECASE | re.DOTALL),
            re.compile(r'credit score.*loan type', re.IGNORECASE),
            re.compile(r'employment type.*monthly income', re.IGNORECASE),
            re.compile(r'salaried.*monthly income.*₹', re.IGNORECASE),
            re.compile(r'age:.*employment.*income.*credit.*loan', re.IGNORECASE | re.DOTALL),
        ]
        
        # More specific confirmation words that indicate proceeding with application
        self.proceed_application_phrases = [
            "proceed with application", "proceed with the application", 
            "start application", "start the application",
            "apply now", "begin application", "continue with application",
            "go ahead with application", "move to application",
            "yes proceed", "yes i want to proceed", "yes let's proceed",
            "yes please proceed", "proceed", "let's proceed", "continue"
        ]
    
    async def select_agent(self, agents: List[Any], history: List[Any]) -> Optional[Any]:
        """Select agent based on user intent from the last message."""
        
        # Safety checks
        if not agents:
            return None
        if not history:
            return agents[0]  # Default to first agent
            
        # Get the last user message
        last_message = history[-1]
        user_input = ""
        
        # Extract user input from different message formats
        if hasattr(last_message, 'content'):
            user_input = str(last_message.content).lower().strip()
        elif hasattr(last_message, 'message'):
            user_input = str(last_message.message).lower().strip()
        else:
            user_input = str(last_message).lower().strip()
        
        print(f"🔍 User input: '{user_input}'")
        
        # 0. Check if this is prequalification data - keep with PrequalificationAgent
        if any(pattern.search(user_input) for pattern in self.prequalification_data_patterns):
            print("🔍 Prequalification data detected - routing to PrequalificationAgent")
            prequal_agent = self._find_agent(agents, "PrequalificationAgent")
            if prequal_agent:
                print("✅ → PrequalificationAgent (prequalification data)")
                return prequal_agent
        
        # 1. Check if this looks like application form data - if so, route to Application
        if any(pattern.search(user_input) for pattern in self.form_data_patterns):
            print("🔍 Application form data detected - routing to ApplicationAssistAgent")
            app_agent = self._find_agent(agents, "ApplicationAssistAgent")
            if app_agent:
                print("✅ → ApplicationAssistAgent (application form data)")
                return app_agent
        
        # 2. Check if this looks like application form data - if so, route to Application
        if any(pattern.search(user_input) for pattern in self.form_data_patterns):
            print("🔍 Application form data detected - routing to ApplicationAssistAgent")
            app_agent = self._find_agent(agents, "ApplicationAssistAgent")
            if app_agent:
                print("✅ → ApplicationAssistAgent (application form data)")
                return app_agent
        
        # 3. Check for prequalification intent
        if any(word in user_input for word in self.prequalify_words):
            prequal_agent = self._find_agent(agents, "PrequalificationAgent")
            if prequal_agent:
                print("✅ → PrequalificationAgent (eligibility check)")
                return prequal_agent
        
        # 4. Check for application intent (including status checks)
        if (any(word in user_input for word in self.apply_words) or 
            self.customer_id_pattern.search(user_input)):
            app_agent = self._find_agent(agents, "ApplicationAssistAgent")
            if app_agent:
                if self.customer_id_pattern.search(user_input):
                    print("✅ → ApplicationAssistAgent (customer ID detected for status)")
                else:
                    print("✅ → ApplicationAssistAgent (application or status check)")
                return app_agent
        
        # 5. Check for specific application proceeding confirmation after prequalification
        proceed_match = any(phrase in user_input for phrase in self.proceed_application_phrases)
        print(f"🔍 Proceed match: {proceed_match}")
        
        if proceed_match:
            # Look for the previous agent in history
            previous_agent = self._get_last_agent_from_history(history)
            print(f"🔍 Previous agent: {previous_agent}")
            
            if previous_agent == "PrequalificationAgent":
                app_agent = self._find_agent(agents, "ApplicationAssistAgent")
                if app_agent:
                    print("✅ → ApplicationAssistAgent (user confirmed to proceed with application)")
                    return app_agent
        
        # 6. Default: continue with current agent or first agent
        current_agent = self._get_current_agent(agents, history)
        if current_agent:
            print(f"🔄 → Continuing with {self._get_agent_name(current_agent)}")
            return current_agent
        
        print(f"🔄 → Default to {self._get_agent_name(agents[0])}")
        return agents[0]
    
    def _find_agent(self, agents: List[Any], agent_name: str) -> Optional[Any]:
        """Find agent by name."""
        for agent in agents:
            if self._get_agent_name(agent) == agent_name:
                return agent
        return None
    
    def _get_agent_name(self, agent: Any) -> str:
        """Extract agent name from different agent formats."""
        if hasattr(agent, 'name'):
            return agent.name
        elif hasattr(agent, 'definition') and hasattr(agent.definition, 'name'):
            return agent.definition.name
        elif hasattr(agent, '_name'):
            return agent._name
        return "UnknownAgent"
    
    def _get_last_agent_from_history(self, history: List[Any]) -> Optional[str]:
        """Get the last agent that responded (not user message)."""
        # Look backwards through history for assistant/agent messages
        for i in range(len(history) - 2, -1, -1):  # Skip last message (user)
            message = history[i]
            
            # Check for agent name in various formats
            if hasattr(message, 'agent_name'):
                return message.agent_name
            elif hasattr(message, 'role') and message.role == 'assistant':
                # Try to find agent name in metadata or source
                if hasattr(message, 'source'):
                    return message.source
                elif hasattr(message, 'metadata') and 'agent_name' in message.metadata:
                    return message.metadata['agent_name']
            elif hasattr(message, 'name'):
                return message.name
        
        return None
    
    def _get_current_agent(self, agents: List[Any], history: List[Any]) -> Optional[Any]:
        """Get current active agent based on recent conversation."""
        last_agent_name = self._get_last_agent_from_history(history)
        if last_agent_name:
            return self._find_agent(agents, last_agent_name)
        return None


# Quick usage example
def create_loan_agents_with_intent_routing():
    """
    Example function showing how to set up agents with intent-based routing.
    This would be called in your main orchestration code.
    """
    
    # Create the intent-based selector
    selector = LoanAgentSelector()
    
    return {
        'selection_strategy': selector,
        'description': 'Intent-based routing for loan application process'
    }


# Test the intent detection logic
def test_intent_routing():
    """Quick test of the intent detection."""
    selector = LoanAgentSelector()
    
    test_cases = [
        "I want to check my eligibility",
        "Can I apply for a loan?", 
        "Am I eligible for home loan?",
        "I want to start my application",
        "Show loan status for customer CUST001",
        "What's the progress on my application?",
        "Check audit records for my loan",
        "Yes, I want to proceed",
        "Hello there"
    ]
    
    print("🧪 Testing Intent Detection:")
    for test_input in test_cases:
        user_input = test_input.lower()
        
        if any(word in user_input for word in selector.prequalify_words):
            result = "PrequalificationAgent"
        elif any(word in user_input for word in selector.apply_words):
            result = "ApplicationAssistAgent"
        elif any(phrase in user_input for phrase in selector.proceed_application_phrases):
            result = "Proceed with Application (context-dependent)"
        else:
            result = "Default Agent"
            
        print(f"'{test_input}' → {result}")


if __name__ == "__main__":
    test_intent_routing()
