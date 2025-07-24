
#RUn this code , it is fully working 

from openai import AzureOpenAI
from dotenv import load_dotenv
load_dotenv()

from playwright.sync_api import sync_playwright

import base64
import time
from PIL import Image
from io import BytesIO

# Azure OpenAI client
client = AzureOpenAI(
    api_key="...",  # Replace with your actual API key
    azure_endpoint="...",  # Replace with your actual Azure endpoint
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
            print("Switched to new page/tab")

        match action_type:
            case "click":
                x, y = action.x, action.y
                button = action.button
                print(f"Clicking at ({x}, {y}) with button {button}")
                page.mouse.click(x, y, button=button)

            case "scroll":
                x, y = action.x, action.y
                scroll_x, scroll_y = action.scroll_x, action.scroll_y
                print(f"Scrolling at ({x}, {y}) with offsets (scroll_x={scroll_x}, scroll_y={scroll_y})")
                page.mouse.move(x, y)
                page.evaluate(f"window.scrollBy({scroll_x}, {scroll_y})")

            case "keypress":
                keys = action.keys
                for k in keys:
                    print(f"Keypress: '{k}'")
                    if k.lower() == "enter":
                        page.keyboard.press("Enter")
                    elif k.lower() == "space":
                        page.keyboard.press(" ")
                    else:
                        page.keyboard.press(k)

            case "type":
                text = action.text
                print(f"Typing: {text}")
                page.keyboard.type(text)

            case "wait":
                print("Waiting...")
                time.sleep(2)

            case _:
                print(f"Unrecognized action: {action}")

        return page

    except Exception as e:
        print(f"Error handling action {action}: {e}")
        return page

def safe_api_call(func, max_retries=5, base_delay=2):
    """
    Safely call OpenAI API with exponential backoff retry logic
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            error_str = str(e)
            print(f"API call failed (attempt {attempt + 1}/{max_retries}): {error_str}")
            
            if "503" in error_str or "InternalServerError" in error_str:
                # Server overload - wait longer
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                print(f"Server error detected. Waiting {delay} seconds before retry...")
                time.sleep(delay)
            elif "429" in error_str or "rate" in error_str.lower():
                # Rate limit - wait even longer
                delay = base_delay * (3 ** attempt)
                print(f"Rate limit detected. Waiting {delay} seconds before retry...")
                time.sleep(delay)
            else:
                # Other errors - shorter wait
                delay = base_delay
                print(f"Other error. Waiting {delay} seconds before retry...")
                time.sleep(delay)
            
            if attempt == max_retries - 1:
                print("Max retries reached. Raising exception.")
                raise e
    
    return None

def computer_use_loop_with_safety(browser, page, response):
    """
    Modified computer use loop with safety checks and user interaction capability
    """
    max_iterations = 15  # Limit total iterations to prevent infinite loops
    iteration_count = 0
    
    while iteration_count < max_iterations:
        try:
            computer_calls = [item for item in response.output if item.type == "computer_call"]
            
            if not computer_calls:
                # Check if agent sent a message (possibly asking for user input)
                agent_message = ""
                for item in response.output:
                    if hasattr(item, 'content') and item.content:
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                agent_message += content_item.text + " "
                    elif hasattr(item, 'text'):
                        agent_message += item.text + " "
                
                agent_message = agent_message.strip()
                  # If agent sent a message, show it and ask for user input
                if agent_message and ('?' in agent_message or 'provide' in agent_message.lower() or 'need' in agent_message.lower()):
                    print("\n" + "🤖" + "="*60)
                    print("AGENT MESSAGE:")
                    print("="*60)
                    print(agent_message)
                    print("="*60)
                    print("💡 Tip: Type 'quit', 'bye', 'exit', or 'stop' to end the session")
                    print("-" * 60)
                    
                    user_response = input("Your response: ").strip()
                    
                    # Check if user wants to quit
                    if user_response.lower() in ['quit', 'bye', 'exit', 'stop']:
                        print("🛑 User requested to stop the session. Ending...")
                        return response
                    
                    if user_response:
                        print(f"✅ Sending to agent: {user_response}")
                        
                        # Send user response back to agent
                        def create_user_response():
                            return client.responses.create(
                                model="computer-use-preview",
                                previous_response_id=response.id,
                                tools=tools,
                                input=[{"role": "user", "content": user_response}],
                                truncation="auto"
                            )
                        
                        response = safe_api_call(create_user_response)
                        if response is None:
                            print("Failed to send user response to agent.")
                            break
                        
                        # Continue the loop to process agent's next actions
                        continue
                
                print("No more computer calls. Task completed.")
                for item in response.output:
                    print(item)
                break

            computer_call = computer_calls[0]
            last_call_id = computer_call.call_id
            action = computer_call.action

            print(f"Iteration {iteration_count + 1}: {action}")
            
            page = handle_model_action(browser, page, action)
            time.sleep(1)

            screenshot_bytes = get_screenshot(page)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")

            # Safe API call with retry logic
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
                print("Failed to get response after retries. Breaking loop.")
                break
            
            print(f"Response {iteration_count + 1}: {response.output}")
            iteration_count += 1
            
        except Exception as e:
            print(f"Error in computer use loop iteration {iteration_count + 1}: {e}")
            break

    print(f"Computer use loop completed after {iteration_count} iterations")
    return response

def main():
    # Get customer ID from user
    print("="*50)
    print("CUSTOMER LOOKUP SYSTEM")
    print("="*50)
    customer_id = input("Enter the Customer ID you want to search for: ").strip()
    username = input("Enter the Username of the CRM System: ").strip()
    password = input("Enter the Password of the CRM System: ").strip()
    if not customer_id:
        print("No customer ID provided. Exiting...")
        return
    
    print(f"Searching for Customer ID: {customer_id}")
    print("="*50)
    
    # Let the agent ask for credentials naturally when needed
    # half1_message = f"Navigate to the website and handle any login if required. If you need login credentials, use {username} and {password} for the CRM System and then Go to the customers tab and find the CRM Ref for the Customer ID {customer_id}"
   # half2_message = f"Go to the customers tab and find the CRM Ref for the Customer ID {customer_id},if you need login credentials, ask the user for them. use {username} and {password} for the CRM System."
    half1_message = f"""
Navigate to the website and handle any login if required. 
If you need login credentials, use {username} and {password} for the CRM System. 
Then go to the Customers tab and find the CRM Ref for the Customer ID {customer_id}. 
Once found, return only the CRM Ref value in this format: 
"The CRM Ref for the customer with ID '{customer_id}' is '<CRM_REF>'." 
Do not include anything else or offer further assistance.
"""

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

        # Navigate to the initial URL
        page.goto("https://globaltrustbank1.pythonanywhere.com/dashboard", wait_until="domcontentloaded")
        time.sleep(2)

        print("="*50)
        print("EXECUTING FIRST HALF: LOGIN AND NAVIGATION")
        print("="*50)
        
        # First half: Login and basic navigation
        def create_first_response():
            return client.responses.create(
                model="computer-use-preview",
                input=[{"role": "user", "content": half1_message}],
                tools=tools,
                reasoning={"generate_summary": "concise"},
                truncation="auto"
            )
        
        response1 = safe_api_call(create_first_response)
        if response1:
            print("First half response:", response1.output)
            final_response1 = computer_use_loop_with_safety(browser, page, response1)
        else:
            print("Failed to get initial response for first half")
            return

        # Wait between halves
        time.sleep(3)
        
        print("="*50)
        # print(f"EXECUTING SECOND HALF: FIND CUSTOMER {customer_id}")
        # print("="*50)
        
        # # Second half: Find specific customer
        # def create_second_response():
        #     return client.responses.create(
        #         model="computer-use-preview",
        #         input=[{"role": "user", "content": half2_message}],
        #         tools=tools,
        #         reasoning={"generate_summary": "concise"},
        #         truncation="auto"
        #     )
        
        # response2 = safe_api_call(create_second_response)
        # if response2:
        #     print("Second half response:", response2.output)
        #     final_response2 = computer_use_loop_with_safety(browser, page, response2)
            
        #     if final_response2:
        #         print("\n" + "="*50)
        #         print("FINAL RESULT:")
        #         print("="*50)
        #         print(final_response2.output_text if hasattr(final_response2, 'output_text') else final_response2.output)
        # else:
        #     print("Failed to get initial response for second half")

        # # Keep browser open for review
        # time.sleep(5)
        browser.close()

if __name__ == "__main__":
    main()
