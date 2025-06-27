from openai import AzureOpenAI
from dotenv import load_dotenv
load_dotenv()

from playwright.sync_api import sync_playwright

import base64
import time
from PIL import Image
from io import BytesIO
import re

# Azure OpenAI client
client = AzureOpenAI(
    api_key="Fl4K9mHabFAqqaeEgbpziq4pSK98eXiQm6PMs3r2hKA8YWMcV4WJJQQJ99BDACHYHv6XJ3w3AAAAACOGFNlv",
    azure_endpoint="https://ai-ronakofficial14141992ai537166517119.openai.azure.com",
    api_version="2025-04-01-preview"
)

# Tools
tools = [{
    "type": "computer_use_preview",
    "display_width": 1024,
    "display_height": 768,
    "environment": "browser",
}]

def get_screenshot(page):
    return page.screenshot()

def handle_model_action(browser, page, action):
    action_type = action.type

    try:
        all_pages = browser.contexts[0].pages
        if len(all_pages) > 1 and all_pages[-1] != page:
            page = all_pages[-1]

        match action_type:
            case "click":
                x, y = action.x, action.y
                button = action.button
                page.mouse.click(x, y, button=button)

            case "scroll":
                x, y = action.x, action.y
                scroll_x, scroll_y = action.scroll_x, action.scroll_y
                page.mouse.move(x, y)
                page.evaluate(f"window.scrollBy({scroll_x}, {scroll_y})")

            case "keypress":
                keys = action.keys
                for k in keys:
                    if k.lower() == "enter":
                        page.keyboard.press("Enter")
                    elif k.lower() == "space":
                        page.keyboard.press(" ")
                    else:
                        page.keyboard.press(k)

            case "type":
                text = action.text
                page.keyboard.type(text)

            case "wait":
                time.sleep(2)

            case _:
                pass

        return page

    except Exception as e:
        print(f"Error handling action {action}: {e}")
        return page

def safe_api_call(func, max_retries=5, base_delay=2):
    """Safely call OpenAI API with exponential backoff retry logic"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            error_str = str(e)
            
            if "503" in error_str or "InternalServerError" in error_str:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            elif "429" in error_str or "rate" in error_str.lower():
                delay = base_delay * (3 ** attempt)
                time.sleep(delay)
            else:
                delay = base_delay
                time.sleep(delay)
            
            if attempt == max_retries - 1:
                raise e
    
    return None

def computer_use_loop_with_callback(browser, page, response, status_callback):
    """Modified computer use loop with status callback for web UI"""
    max_iterations = 15
    iteration_count = 0
    
    while iteration_count < max_iterations:
        try:
            computer_calls = [item for item in response.output if item.type == "computer_call"]
            
            if not computer_calls:
                # Check for agent messages
                agent_message = ""
                for item in response.output:
                    if hasattr(item, 'content') and item.content:
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                agent_message += content_item.text + " "
                    elif hasattr(item, 'text'):
                        agent_message += item.text + " "
                
                agent_message = agent_message.strip()
                
                # COMPREHENSIVE CRM reference extraction patterns
                crm_patterns = [
                    # Pattern 1: ResponseOutputMessage with CRM reference
                    r'(?:CRM\s+[Rr]ef|CRM\s+[Rr]eference|CRM\s+reference).*?is\s*[\\\'"]*([A-Z0-9]+)[\\\'"]*',
                    
                    # Pattern 2: Any "is" followed by quoted alphanumeric code
                    r'is\s*[\\\'"]+([A-Z0-9]{8,})[\\\'"]+',
                    
                    # Pattern 3: Simple quoted CRM codes
                    r'["\']([A-Z]*CRM[0-9]{6,})["\']',
                    
                    # Pattern 4: Escaped quoted CRM codes  
                    r'[\\\'"]+([A-Z]*CRM[0-9]{6,})[\\\'"]+',
                    
                    # Pattern 5: Standalone GTBCRM patterns
                    r'\b(GTBCRM[0-9]{6,})\b',
                    
                    # Pattern 6: Any CRM format codes
                    r'\b([A-Z]{2,}CRM[0-9]{6,})\b',
                    
                    # Pattern 7: Alphanumeric codes in any type of quotes
                    r'[\\\'"]*([A-Z]{3,}[0-9]{6,})[\\\'"]*',
                    
                    # Pattern 8: Simple quotes around codes
                    r'["\']([A-Z0-9]{8,})["\']',
                    
                    # Pattern 9: The CRM Ref format specifically
                    r'The\s+CRM\s+[Rr]ef.*?is\s*[\\\'"]*([A-Z0-9]+)[\\\'"]*',
                    
                    # Pattern 10: Any reference pattern with "is"
                    r'(?:reference|ref).*?is\s*[\\\'"]*([A-Z0-9]{8,})[\\\'"]*',
                    
                    # Pattern 11: Broad alphanumeric code detection
                    r'\b([A-Z0-9]{10,})\b',
                ]
                
                # Try each pattern to find CRM reference
                for i, pattern in enumerate(crm_patterns):
                    matches = re.findall(pattern, agent_message, re.IGNORECASE)
                    if matches:
                        for match in matches:
                            potential_ref = match.strip()
                            # Validate that it looks like a valid CRM reference
                            if len(potential_ref) >= 8 and re.match(r'^[A-Z0-9]+$', potential_ref):
                                # Prefer codes that contain "CRM" or start with known prefixes
                                if 'CRM' in potential_ref.upper() or potential_ref.startswith(('GTB', 'CRM')):
                                    status_callback(f"Found CRM reference using pattern {i+1}: {potential_ref}")
                                    return potential_ref
                                elif len(potential_ref) >= 10:  # Fallback for long codes
                                    status_callback(f"Found potential CRM reference using pattern {i+1}: {potential_ref}")
                                    return potential_ref
                
                status_callback("Task completed - checking for results...")
                break

            computer_call = computer_calls[0]
            last_call_id = computer_call.call_id
            action = computer_call.action

            status_callback(f"Performing action: {action.type}")
            
            page = handle_model_action(browser, page, action)
            time.sleep(1)

            screenshot_bytes = get_screenshot(page)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")

            def make_api_call():
                return client.responses.create(
                    model="computer-use-preview",
                    previous_response_id=response.id,
                    tools=tools,
                    input=[{
                        "call_id": last_call_id,
                        "type": "computer_call_output",
                        "output": {
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{screenshot_base64}"
                        }
                    }],
                    truncation="auto"
                )
            
            response = safe_api_call(make_api_call)
            if response is None:
                break
            
            iteration_count += 1
            
        except Exception as e:
            status_callback(f"Error in iteration {iteration_count + 1}: {str(e)}")
            break

    return None

def run_agent_lookup_with_callback(customer_id, username, password, status_callback):
    """Main function to run agent lookup with status callbacks"""
    try:
        status_callback("Starting browser...")
        
        message = f"Navigate to the website and handle any login if required. Use {username} and {password} for the CRM System login. Then go to the customers tab and find the CRM Ref for Customer ID {customer_id}. Once you find it, clearly state the CRM reference number."
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                chromium_sandbox=True,
                env={},
                args=[
                    "--disable-extensions", 
                    "--disable-file-system"
                ]
            )

            page = browser.new_page()
            page.set_viewport_size({"width": 1024, "height": 768})

            status_callback("Navigating to CRM system...")
            page.goto("https://globaltrustbank1.pythonanywhere.com/dashboard", wait_until="domcontentloaded")
            time.sleep(2)

            status_callback("Starting AI agent...")
            
            def create_response():
                return client.responses.create(
                    model="computer-use-preview",
                    input=[{"role": "user", "content": message}],
                    tools=tools,
                    reasoning={"generate_summary": "concise"},
                    truncation="auto"
                )
            
            response = safe_api_call(create_response)
            if response:
                status_callback("Agent is processing...")
                crm_ref = computer_use_loop_with_callback(browser, page, response, status_callback)
                
                if crm_ref:
                    status_callback("CRM reference found!")
                    return crm_ref
                else:
                    # Try to extract from page content as fallback
                    page_content = page.content()
                    crm_match = re.search(r'GTBCRM\d+', page_content)
                    if crm_match:
                        return crm_match.group(0)
            
            browser.close()
            return None
            
    except Exception as e:
        status_callback(f"Error: {str(e)}")
        return None
