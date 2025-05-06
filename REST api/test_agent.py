# Test cases for the loan processing agent
import requests
import json
from time import sleep

BASE_URL = "http://localhost:8001"

def test_agent(instruction):
    """Test the agent with a given instruction."""
    print(f"\nTesting instruction: {instruction}")
    try:
        response = requests.post(
            f"{BASE_URL}/agent",
            json={"instruction": instruction},
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
        return response
    except Exception as e:
        print(f"Error: {str(e)}")
    print("-" * 50)

def run_tests():
    """Run a series of test cases."""
    test_cases = [
        "Apply for a $10000 education loan for John Doe with email john@example.com, phone 1234567890, 12 month term, monthly income $5000, employment type Salaried",
        "Show me loan ID 1",
        "Submit loan ID 1",
        "Approve loan ID 1",
        "Reject loan ID 2 because insufficient income"
    ]
    
    for test in test_cases:
        response = test_agent(test)
        if response and response.status_code == 200:
            print("✅ Test passed")
        else:
            print("❌ Test failed")
        sleep(1)  # Pause between tests

if __name__ == "__main__":
    run_tests()
